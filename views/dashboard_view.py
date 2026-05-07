import asyncio
from datetime import datetime, timedelta

import flet as ft

from views.ui_components import (
    primary_button,
    progress_track,
    section_title,
    secondary_button,
    soft_card,
    stat_pill,
    with_alpha,
)


class DashboardView:
    """Dashboard principal com visual profissional claro."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._metric_values: list[tuple[ft.Text, int]] = []
        self._metric_cards: list[ft.Container] = []
        self._reveal_blocks: list[ft.Container] = []
        self._animating_metrics = False
        self._animating_reveal = False

    def on_show(self):
        pass

    def build(self):
        t = self.app.theme_mgr.get_theme()
        uid = self.app.get_user_id()
        self._metric_values = []
        self._metric_cards = []
        self._reveal_blocks = []

        if not uid:
            guest = self._build_guest_mode(t)
            self.app.page.run_task(self._animate_dashboard_reveal)
            return guest

        self.db.update_streak(uid)

        hour = datetime.now().hour
        greeting = "Bom dia" if hour < 12 else ("Boa tarde" if hour < 18 else "Boa noite")
        name = self.app.current_user.get("display_name", "Estudante")

        xp_info = self.db.get_xp_info(uid)
        streak_info = self.db.get_streak(uid)
        goals_summary = self.db.get_daily_goals_summary(uid)
        today_stats = self.db.get_today_stats(uid)
        sessions = self.db.get_sessions(uid, limit=200)

        content = ft.Column(
            controls=[
                self._reveal(self._build_main_hero(t, greeting, name, xp_info, streak_info, today_stats)),
                self._reveal(section_title(t, "Visao rapida", "Tudo que importa para decidir sua proxima acao.")),
                self._reveal(self._build_metrics(t, today_stats, streak_info)),
                self._reveal(section_title(
                    t,
                    "Metas de hoje",
                    "Progresso visual com leitura imediata.",
                    action=ft.TextButton(
                        "Abrir tarefas",
                        icon=ft.Icons.ARROW_OUTWARD_ROUNDED,
                        on_click=lambda _: self.app.show_view("tasks"),
                        style=ft.ButtonStyle(color=t["primary"]),
                    ),
                )),
                self._reveal(self._build_goals(t, goals_summary, today_stats)),
                self._reveal(section_title(t, "Ritmo semanal", "Consistencia dos ultimos 7 dias.")),
                self._reveal(self._build_week_activity(t, sessions)),
                self._reveal(section_title(t, "Atalhos", "Acoes rapidas para manter fluxo.")),
                self._reveal(self._build_actions(t)),
                ft.Container(height=8),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

        self.app.page.run_task(self._animate_dashboard_reveal)
        self.app.page.run_task(self._animate_metrics)

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.only(left=18, top=14, right=18, bottom=20),
            content=content,
        )

    def _build_main_hero(self, t, greeting, name, xp_info, streak_info, today_stats):
        level_prefix = t.get("level_prefix", "Nivel")
        xp_name = t.get("xp_name", "XP")

        return soft_card(
            t,
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{greeting}, {name}",
                                        size=28,
                                        weight=ft.FontWeight.BOLD,
                                        color=t["text"],
                                    ),
                                    ft.Text(
                                        "Seu painel de foco, metas e progresso em um so lugar.",
                                        size=13,
                                        color=t["text_sec"],
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.Container(
                                width=54,
                                height=54,
                                border_radius=18,
                                bgcolor=t.get("chip_bg", t["card"]),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=28, color=t["primary"]),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Row(
                        [
                            stat_pill(t, level_prefix, str(xp_info["level"])),
                            stat_pill(t, "Streak", f"{streak_info['streak']} dias"),
                            stat_pill(t, "XP hoje", f"{today_stats['xp_today']}"),
                        ],
                        wrap=True,
                        spacing=8,
                        run_spacing=8,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"{xp_info['xp']} / {xp_info['xp_next_level']} {xp_name}",
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=t["text"],
                                    ),
                                    ft.Text(
                                        f"Recorde: {streak_info['longest']} dias",
                                        size=11,
                                        color=t["text_sec"],
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            progress_track(
                                t,
                                xp_info["progress"],
                                color=t["primary"],
                                bgcolor=with_alpha(t["primary"], "1E"),
                                height=11,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        [
                            primary_button(
                                t,
                                "Iniciar foco",
                                lambda _: self.app.show_view("pomodoro"),
                                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                                expand=True,
                            ),
                            secondary_button(
                                t,
                                "Ir para estudo",
                                lambda _: self.app.show_view("study"),
                                icon=ft.Icons.SCHOOL_ROUNDED,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=16,
            ),
            radius=30,
            padding=24,
            bgcolor=t["card"],
        )

    def _build_metrics(self, t, today_stats, streak_info):
        specs = [
            ("P", "Pomodoros", int(today_stats["pomodoros"]), "Sessoes completas"),
            ("F", "Minutos focados", int(today_stats["focus_min"]), "Tempo profundo"),
            ("Q", "Questoes", int(today_stats["questions"]), "Treino ativo"),
            ("S", "Melhor streak", int(streak_info["longest"]), "Constancia"),
        ]
        cards = []
        for icon_txt, label, target, helper in specs:
            value_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=t["text"])
            card = soft_card(
                t,
                ft.Column(
                    [
                        ft.Text(icon_txt, size=22),
                        value_text,
                        ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=t["text_sec"]),
                        ft.Text(helper, size=10, color=t["text_sec"]),
                    ],
                    spacing=5,
                    tight=True,
                ),
                padding=18,
                radius=20,
                expand=True,
                bgcolor=t["card"],
            )
            shell = ft.Container(
                content=card,
                opacity=1.0 if self.app.reduce_motion else 0.0,
                offset=ft.Offset(0, 0) if self.app.reduce_motion else ft.Offset(0, 0.05),
                animate_opacity=self.app.motion_ms(240),
                animate_offset=self.app.motion_ms(240),
            )
            cards.append(shell)
            self._metric_values.append((value_text, target))
            self._metric_cards.append(shell)

        return ft.ResponsiveRow(
            controls=[ft.Container(content=card, col={"xs": 6, "sm": 6, "md": 3}) for card in cards],
            spacing=10,
            run_spacing=10,
        )

    def _build_goals(self, t, goals_summary, today_stats):
        goals = goals_summary.get("goals", [])
        goal_configs = {
            "pomodoro": ("Pomodoros", today_stats["pomodoros"]),
            "xp": ("XP ganho", today_stats["xp_today"]),
            "quiz": ("Questoes", today_stats["questions"]),
        }

        goal_cards = []
        for goal in goals:
            label, current = goal_configs.get(
                goal["goal_type"],
                (goal["goal_type"].title(), goal["current_value"]),
            )
            current = max(current, goal["current_value"])
            target = goal["target_value"]
            done = current >= target
            pct = min(current / target, 1.0) if target > 0 else 0.0

            goal_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 4},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(label, size=15, weight=ft.FontWeight.W_700, color=t["text"]),
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                            border_radius=999,
                                            bgcolor=with_alpha(t["success"], "20") if done else t.get("chip_bg", t["card"]),
                                            border=ft.border.all(1, t.get("border_soft", "#E9DCC9")),
                                            content=ft.Text(
                                                "Concluido" if done else "Em andamento",
                                                size=10,
                                                weight=ft.FontWeight.BOLD,
                                                color=t["success"] if done else t["text_sec"],
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(
                                    f"{current} de {target}",
                                    size=24,
                                    weight=ft.FontWeight.BOLD,
                                    color=t["success"] if done else t["primary"],
                                ),
                                progress_track(t, pct, color=t["success"] if done else t["primary"]),
                            ],
                            spacing=12,
                        ),
                        bgcolor=t["card"],
                        radius=24,
                    ),
                )
            )

        controls = [ft.ResponsiveRow(goal_cards, spacing=10, run_spacing=10)]
        if goals_summary.get("all_done"):
            controls.append(
                soft_card(
                    t,
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CELEBRATION_ROUNDED, size=24, color=t["success"]),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Todas as metas do dia foram concluidas",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=t["text"],
                                    ),
                                    ft.Text(
                                        t.get("celebration", "Excelente ritmo hoje."),
                                        size=12,
                                        color=t["text_sec"],
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    bgcolor=with_alpha(t["success"], "10"),
                    radius=22,
                    padding=16,
                )
            )

        return ft.Column(controls, spacing=10)

    def _build_week_activity(self, t, sessions):
        today_date = datetime.now().date()
        day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        counts = {}

        for i in range(6, -1, -1):
            d = today_date - timedelta(days=i)
            counts[d.isoformat()] = 0

        for session in sessions:
            completed = session.get("completed_at", "")
            if completed:
                date_str = completed[:10]
                if date_str in counts:
                    counts[date_str] += 1

        max_count = max(counts.values()) if counts else 1
        max_count = max(max_count, 1)

        bars = []
        for date_key, count in counts.items():
            d = datetime.fromisoformat(date_key).date()
            is_today = d == today_date
            height = max(int(64 * count / max_count), 8) if count > 0 else 8
            color = t["success"] if is_today and count > 0 else t["primary"] if count > 0 else with_alpha(t["text_sec"], "2A")

            bars.append(
                ft.Column(
                    [
                        ft.Text(
                            str(count),
                            size=11,
                            weight=ft.FontWeight.BOLD,
                            color=t["text"] if count > 0 else t["text_sec"],
                        ),
                        ft.Container(
                            width=28,
                            height=height,
                            border_radius=16,
                            bgcolor=color,
                            shadow=[ft.BoxShadow(blur_radius=10, color=with_alpha(color, "55"), offset=ft.Offset(0, 3))],
                        ),
                        ft.Text(
                            day_names[d.weekday()],
                            size=10,
                            weight=ft.FontWeight.W_600 if is_today else ft.FontWeight.NORMAL,
                            color=t["success"] if is_today else t["text_sec"],
                        ),
                    ],
                    width=36,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.END,
                    spacing=6,
                )
            )

        return soft_card(
            t,
            ft.Row(
                bars,
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            bgcolor=t["card"],
            radius=24,
            padding=18,
        )

    def _build_actions(self, t):
        cards = [
            ("Pomodoro", "Comecar sessao agora", ft.Icons.TIMER_ROUNDED, "pomodoro"),
            ("Quiz", "Praticar questoes e ganhar XP", ft.Icons.QUIZ_ROUNDED, "study"),
            ("Flashcards", "Revisao por repeticao", ft.Icons.STYLE_ROUNDED, "flashcards"),
            ("Tarefas", "Organizar plano do dia", ft.Icons.CHECKLIST_ROUNDED, "tasks"),
        ]

        action_cards = []
        for title, subtitle, icon, target in cards:
            action_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 3},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Container(
                                    width=36,
                                    height=36,
                                    border_radius=12,
                                    bgcolor=t.get("chip_bg", t["card"]),
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(icon, size=18, color=t["primary"]),
                                ),
                                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=t["text"]),
                                ft.Text(subtitle, size=12, color=t["text_sec"]),
                                ft.TextButton(
                                    "Abrir",
                                    icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                    on_click=lambda _, dest=target: self.app.show_view(dest),
                                    style=ft.ButtonStyle(color=t["primary"]),
                                ),
                            ],
                            spacing=8,
                        ),
                        bgcolor=t["card"],
                        radius=24,
                        height=182,
                    ),
                )
            )

        return ft.ResponsiveRow(action_cards, spacing=10, run_spacing=10)

    def _build_guest_mode(self, t):
        hero = soft_card(
            t,
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "Bem-vindo ao modo convidado",
                                size=30,
                                weight=ft.FontWeight.BOLD,
                                color=t["text"],
                                expand=True,
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=7),
                                border_radius=999,
                                bgcolor=t.get("chip_bg", t["card"]),
                                border=ft.border.all(1, t.get("border_soft", "#E9DCC9")),
                                content=ft.Text("Convidado", size=11, color=t.get("chip_text", t["text_sec"])),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        "Voce pode estudar agora com recursos essenciais. Para salvar progresso e desbloquear tudo, entre com sua conta.",
                        size=13,
                        color=t["text_sec"],
                    ),
                    ft.Row(
                        [
                            primary_button(
                                t,
                                "Entrar / Criar conta",
                                lambda _: self.app.show_view("login"),
                                icon=ft.Icons.LOGIN_ROUNDED,
                                expand=True,
                                height=50,
                            ),
                            secondary_button(
                                t,
                                "Continuar como convidado",
                                lambda _: self.app.show_view("pomodoro"),
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                expand=True,
                                height=50,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.TextButton(
                        "Ver recursos disponiveis",
                        icon=ft.Icons.VISIBILITY_ROUNDED,
                        style=ft.ButtonStyle(color=t["primary"]),
                        on_click=lambda _: None,
                    ),
                ],
                spacing=16,
            ),
            radius=30,
            padding=26,
            bgcolor=t["card"],
        )

        unlocked = [
            ("Pomodoro", "Sessao de foco e pausas"),
            ("Tarefas locais", "Checklist durante a sessao"),
            ("Estudo rapido", "Quiz e revisao imediata"),
        ]
        locked = [
            ("Sincronizacao", "Salvar progresso entre dispositivos"),
            ("XP e streak", "Gamificacao e constancia"),
            ("Historico completo", "Relatorios e desempenho"),
        ]

        unlocked_cards = []
        for title, subtitle in unlocked:
            unlocked_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 4},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=t["success"], size=18),
                                        ft.Text("Disponivel", size=11, color=t["success"]),
                                    ],
                                    spacing=6,
                                ),
                                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=t["text"]),
                                ft.Text(subtitle, size=12, color=t["text_sec"]),
                            ],
                            spacing=8,
                        ),
                        bgcolor=t["card"],
                        radius=22,
                        height=132,
                    ),
                )
            )

        locked_cards = []
        for title, subtitle in locked:
            locked_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 4},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.LOCK_ROUNDED, color=t["text_sec"], size=18),
                                        ft.Text("Com conta", size=11, color=t["text_sec"]),
                                    ],
                                    spacing=6,
                                ),
                                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=t["text"]),
                                ft.Text(subtitle, size=12, color=t["text_sec"]),
                            ],
                            spacing=8,
                        ),
                        bgcolor=t["card"],
                        radius=22,
                        height=132,
                    ),
                )
            )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.only(left=18, top=14, right=18, bottom=20),
            content=ft.Column(
                [
                    self._reveal(hero),
                    self._reveal(section_title(t, "Recursos disponiveis", "Ferramentas que voce pode usar agora.")),
                    self._reveal(ft.ResponsiveRow(unlocked_cards, spacing=10, run_spacing=10)),
                    self._reveal(section_title(t, "Desbloquear com conta", "Vantagens para manter consistencia.")),
                    self._reveal(ft.ResponsiveRow(locked_cards, spacing=10, run_spacing=10)),
                ],
                spacing=16,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _reveal(self, control):
        shell = ft.Container(
            content=control,
            opacity=1.0 if self.app.reduce_motion else 0.0,
            offset=ft.Offset(0, 0) if self.app.reduce_motion else ft.Offset(0, 0.035),
            animate_opacity=self.app.motion_ms(260),
            animate_offset=self.app.motion_ms(260),
        )
        self._reveal_blocks.append(shell)
        return shell

    async def _animate_dashboard_reveal(self):
        if self.app.reduce_motion or self._animating_reveal:
            return
        self._animating_reveal = True
        try:
            for shell in self._reveal_blocks:
                shell.opacity = 1.0
                shell.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.045)
        finally:
            self._animating_reveal = False

    async def _animate_metrics(self):
        if self.app.reduce_motion or self._animating_metrics:
            return
        self._animating_metrics = True
        try:
            for shell in self._metric_cards:
                shell.opacity = 1.0
                shell.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.045)

            max_target = max((target for _, target in self._metric_values), default=1)
            steps = 12
            for step in range(1, steps + 1):
                ratio = step / steps
                for label, target in self._metric_values:
                    label.value = str(int(round(target * ratio)))
                self.app.page.update()
                await asyncio.sleep(0.03 if max_target < 300 else 0.02)
        finally:
            self._animating_metrics = False
