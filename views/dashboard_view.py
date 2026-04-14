import flet as ft
from datetime import datetime, timedelta

from views.ui_components import (
    metric_card,
    primary_button,
    progress_track,
    section_title,
    secondary_button,
    soft_card,
    stat_pill,
    with_alpha,
)


class DashboardView:
    """Dashboard principal com foco em progresso, metas e ações rápidas."""

    def __init__(self, app):
        self.app = app
        self.db = app.db

    def on_show(self):
        pass

    def build(self):
        t = self.app.theme_mgr.get_theme()
        uid = self.app.get_user_id()

        if not uid:
            return self._build_guest(t)

        self.db.update_streak(uid)

        hour = datetime.now().hour
        greeting = "Bom dia" if hour < 12 else ("Boa tarde" if hour < 18 else "Boa noite")
        name = self.app.current_user.get("display_name", "Estudante")

        xp_info = self.db.get_xp_info(uid)
        streak_info = self.db.get_streak(uid)
        goals_summary = self.db.get_daily_goals_summary(uid)
        today_stats = self.db.get_today_stats(uid)
        sessions = self.db.get_sessions(uid, limit=200)
        new_achs = self.db.check_and_grant_achievements(uid)
        earned = self.db.get_user_achievements(uid)
        all_achs = self.db.get_all_achievements()

        content = ft.Column(
            controls=[
                self._build_hero(t, greeting, name, xp_info, streak_info, today_stats),
                section_title(
                    t,
                    "Visão do dia",
                    "Métricas rápidas para decidir sua próxima ação.",
                ),
                self._build_metrics(t, today_stats, streak_info),
                section_title(
                    t,
                    "Metas de hoje",
                    "Progresso visual e recompensa imediata ao concluir.",
                    action=ft.TextButton(
                        "Abrir tarefas",
                        icon=ft.Icons.ARROW_OUTWARD_ROUNDED,
                        on_click=lambda _: self.app.show_view("tasks"),
                        style=ft.ButtonStyle(color=t["primary"]),
                    ),
                ),
                self._build_goals(t, goals_summary, today_stats),
                *self._build_new_achievements(t, new_achs),
                section_title(
                    t,
                    f"Conquistas ({len(earned)}/{len(all_achs)})",
                    "Gamificação leve para reforçar consistência.",
                ),
                self._build_achievements(t, earned, all_achs),
                section_title(
                    t,
                    "Ritmo semanal",
                    "Atividade dos últimos 7 dias para leitura rápida de constância.",
                ),
                self._build_week_activity(t, sessions),
                section_title(
                    t,
                    "Ações rápidas",
                    "Atalhos pensados para uso frequente.",
                ),
                self._build_actions(t),
                ft.Container(height=6),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.only(left=18, top=14, right=18, bottom=20),
            content=content,
        )

    def _build_hero(self, t, greeting, name, xp_info, streak_info, today_stats):
        level_prefix = t.get("level_prefix", "Nível")
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
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color=t["text"],
                                    ),
                                    ft.Text(
                                        "Seu painel de foco, metas e evolução em um só lugar.",
                                        size=13,
                                        color="#B3FFFFFF",
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.Container(
                                width=52,
                                height=52,
                                border_radius=18,
                                bgcolor=t.get("surface_soft", "#12FFFFFF"),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text("🎯", size=26),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Row(
                        [
                            stat_pill(
                                t,
                                level_prefix,
                                f"{xp_info['level']}",
                                tone=t.get("surface_soft", "#12FFFFFF"),
                            ),
                            stat_pill(
                                t,
                                "Streak",
                                f"{streak_info['streak']} dias",
                                tone="#22CDE8D8",
                            ),
                            stat_pill(
                                t,
                                "XP hoje",
                                f"{today_stats['xp_today']}",
                                tone=t.get("surface_soft", "#12FFFFFF"),
                            ),
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
                                        color="#AAFFFFFF",
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            progress_track(
                                t,
                                xp_info["progress"],
                                color=t["accent"],
                                bgcolor="#14FFFFFF",
                                height=12,
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
                                "Ver estudo",
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
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[t["surface_alt"], t["card"], t["secondary"]],
            ),
            border=ft.border.all(1, "#12FFFFFF"),
        )

    def _build_metrics(self, t, today_stats, streak_info):
        cards = [
            metric_card(t, "🍅", "Pomodoros", str(today_stats["pomodoros"]), "Sessões completas"),
            metric_card(t, "⏱", "Minutos focados", str(today_stats["focus_min"]), "Tempo profundo"),
            metric_card(t, "📝", "Questões", str(today_stats["questions"]), "Treino ativo"),
            metric_card(t, "🔥", "Melhor streak", str(streak_info["longest"]), "Consistência"),
        ]
        return ft.ResponsiveRow(
            controls=[
                ft.Container(content=card, col={"xs": 6, "sm": 6, "md": 3}) for card in cards
            ],
            spacing=10,
            run_spacing=10,
        )

    def _build_goals(self, t, goals_summary, today_stats):
        goals = goals_summary["goals"]
        goal_configs = {
            "pomodoro": ("🍅", "Pomodoros", today_stats["pomodoros"]),
            "xp": ("⚡", "XP ganho", today_stats["xp_today"]),
            "quiz": ("📝", "Questões", today_stats["questions"]),
        }

        goal_cards = []
        for goal in goals:
            emoji, label, current = goal_configs.get(
                goal["goal_type"],
                ("📌", goal["goal_type"].title(), goal["current_value"]),
            )
            current = max(current, goal["current_value"])
            target = goal["target_value"]
            done = current >= target
            pct = min(current / target, 1.0) if target > 0 else 0

            goal_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 4},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            f"{emoji} {label}",
                                            size=15,
                                            weight=ft.FontWeight.W_700,
                                            color=t["text"],
                                        ),
                                        ft.Container(
                                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                                            border_radius=999,
                                            bgcolor="#183DD598" if done else t.get("surface_soft", "#10FFFFFF"),
                                            content=ft.Text(
                                                "Concluído" if done else "Em andamento",
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
                                    color=t["primary"] if not done else t["success"],
                                ),
                                progress_track(
                                    t,
                                    pct,
                                    color=t["success"] if done else t["primary"],
                                ),
                            ],
                            spacing=12,
                        ),
                        bgcolor=t.get("surface_soft", "#08FFFFFF"),
                        border=ft.border.all(1, "#12FFFFFF"),
                        radius=24,
                    ),
                )
            )

        controls = [ft.ResponsiveRow(goal_cards, spacing=10, run_spacing=10)]
        if goals_summary["all_done"]:
            controls.append(
                soft_card(
                    t,
                    ft.Row(
                        [
                            ft.Text("🎉", size=24),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Todas as metas do dia foram concluídas",
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
                    bgcolor="#1A3DD598",
                    border=ft.border.all(1, "#333DD598"),
                    radius=22,
                    padding=16,
                )
            )

        return ft.Column(controls, spacing=10)

    def _build_new_achievements(self, t, achievements):
        cards = []
        for ach in achievements:
            cards.append(
                soft_card(
                    t,
                    ft.Row(
                        [
                            ft.Container(
                                width=50,
                                height=50,
                                border_radius=18,
                                bgcolor=t.get("surface_soft", "#12FFFFFF"),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text(ach["emoji"], size=24),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        ach["title"],
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=t["bg"],
                                    ),
                                    ft.Text(
                                        f"{ach['description']} (+{ach['xp_reward']} XP)",
                                        size=12,
                                        color="#171717",
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                    ),
                    bgcolor=t["accent"],
                    radius=22,
                    padding=16,
                )
            )
        return cards

    def _build_achievements(self, t, earned, all_achs):
        earned_keys = {a["key"] for a in earned}
        badges = []

        for ach in all_achs[:12]:
            is_earned = ach["key"] in earned_keys
            badges.append(
                ft.Container(
                    col={"xs": 4, "sm": 3, "md": 2},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Text(ach["emoji"] if is_earned else "🔒", size=24),
                                ft.Text(
                                    ach["title"] if is_earned else "Bloqueado",
                                    size=10,
                                    weight=ft.FontWeight.W_600,
                                    text_align=ft.TextAlign.CENTER,
                                    color=t["text"] if is_earned else t["text_sec"],
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6,
                        ),
                        padding=14,
                        height=100,
                        bgcolor=t.get("surface_soft", "#09FFFFFF") if is_earned else "#05FFFFFF",
                        border=ft.border.all(1, "#303DD598" if is_earned else "#0FFFFFFF"),
                        radius=22,
                    ),
                )
            )

        return ft.ResponsiveRow(badges, spacing=10, run_spacing=10)

    def _build_week_activity(self, t, sessions):
        today_date = datetime.now().date()
        day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
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
            color = t["success"] if is_today and count > 0 else t["primary"] if count > 0 else "#12FFFFFF"

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
                            shadow=[ft.BoxShadow(blur_radius=12, color=with_alpha(color, "55"), offset=ft.Offset(0, 4))],
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
            bgcolor=t.get("surface_soft", "#08FFFFFF"),
            border=ft.border.all(1, "#12FFFFFF"),
            radius=24,
            padding=18,
        )

    def _build_actions(self, t):
        cards = [
            ("Pomodoro", "Começar uma sessão agora", "🍅", "pomodoro"),
            ("Quiz", "Praticar questões e ganhar XP", "📝", "study"),
            ("Flashcards", "Revisão rápida com repetição", "🃏", "flashcards"),
            ("Tarefas", "Organizar seu plano do dia", "📋", "tasks"),
        ]

        action_cards = []
        for title, subtitle, emoji, target in cards:
            action_cards.append(
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 3},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Text(emoji, size=24),
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
                        bgcolor=t.get("surface_soft", "#08FFFFFF"),
                        border=ft.border.all(1, "#12FFFFFF"),
                        radius=24,
                        height=180,
                    ),
                )
            )

        return ft.ResponsiveRow(action_cards, spacing=10, run_spacing=10)

    def _build_guest(self, t):
        hero = soft_card(
            t,
            ft.Column(
                [
                    ft.Text("Seu app de estudos pode parecer produto de verdade.", size=26, weight=ft.FontWeight.BOLD, color=t["text"], text_align=ft.TextAlign.CENTER),
                    ft.Text(
                        "Entre para liberar progresso, streak, metas, tarefas e uma experiência de estudo mais completa.",
                        size=13,
                        color=t["text_sec"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row(
                        [
                            primary_button(
                                t,
                                "Entrar / cadastrar",
                                lambda _: self.app.show_view("login"),
                                icon=ft.Icons.LOGIN_ROUNDED,
                                expand=True,
                            ),
                            secondary_button(
                                t,
                                "Continuar convidado",
                                lambda _: self.app.show_view("pomodoro"),
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=18,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=30,
            padding=28,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[t["surface_alt"], t["card"], t["secondary"]],
            ),
            border=ft.border.all(1, "#12FFFFFF"),
        )

        preview = ft.ResponsiveRow(
            [
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 3},
                    content=metric_card(t, "⭐", "XP e níveis", "Ativo", "Progressão visível"),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 3},
                    content=metric_card(t, "🔥", "Streak", "Diário", "Constância motivadora"),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 3},
                    content=metric_card(t, "🎯", "Metas", "Custom", "Clareza no dia"),
                ),
                ft.Container(
                    col={"xs": 12, "sm": 6, "md": 3},
                    content=metric_card(t, "🏆", "Conquistas", "Gamify", "Cara de app real"),
                ),
            ],
            spacing=10,
            run_spacing=10,
        )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.only(left=18, top=14, right=18, bottom=20),
            content=ft.Column(
                [hero, section_title(t, "O que desbloqueia com login"), preview],
                spacing=18,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
