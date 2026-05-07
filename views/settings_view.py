import asyncio

import flet as ft

from themes import THEMES


class SettingsView:
    """Configuracoes do app: temas, pomodoro, metas e perfil."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._save_buttons: dict[str, ft.ElevatedButton] = {}
        self._reveal_blocks: list[ft.Container] = []
        self._revealing = False
        self._theme_card_map: dict[str, ft.Container] = {}
        self._theme_applying = False
        self._save_buttons_animating: set[str] = set()

    def on_show(self):
        pass

    def _section_title(self, t: dict, title: str, subtitle: str | None = None):
        controls = [
            ft.Text(
                title,
                size=18,
                weight=ft.FontWeight.BOLD,
                color=t["text"],
            )
        ]
        if subtitle:
            controls.append(ft.Text(subtitle, size=12, color=t["text_sec"]))
        return ft.Column(controls, spacing=2, tight=True)

    def _panel(self, t: dict, content):
        return ft.Container(
            bgcolor=t["card"],
            border=ft.border.all(1, t.get("border_soft", t["entry_border"])),
            border_radius=16,
            padding=14,
            content=content,
        )

    def _base_field(self, t: dict, label: str, value: str = "", width: int = 110, number: bool = False):
        return ft.TextField(
            label=label,
            value=value,
            width=width,
            height=52,
            dense=True,
            keyboard_type=ft.KeyboardType.NUMBER if number else ft.KeyboardType.TEXT,
            bgcolor=t["entry_bg"],
            border_color=t["entry_border"],
            focused_border_color=t["primary"],
            color=t["text"],
            label_style=ft.TextStyle(color=t["text_sec"]),
        )

    def _hover_card_scale(self, e):
        if self.app.reduce_motion:
            return
        entering = str(getattr(e, "data", "")).lower() == "true"
        e.control.scale = 1.02 if entering else 1.0
        e.control.update()

    def _toggle_reduce_motion(self, e):
        self.app.set_reduce_motion(bool(e.control.value))
        self.app.show_snackbar("Preferencia de animacao atualizada.")

    def _make_save_button(self, t, key, label, handler, *, width=220, height=40):
        btn = ft.ElevatedButton(
            content=ft.Text(label, color="#FFFFFF", weight=ft.FontWeight.W_600),
            height=height,
            width=width,
            bgcolor=t["button"],
            color="#FFFFFF",
            scale=1.0,
            animate_scale=self.app.motion_ms(120),
            on_hover=lambda e: self._button_hover(e),
            on_click=lambda _, k=key, h=handler: self.app.page.run_task(self._animate_save_button_click, k, h),
        )
        self._save_buttons[key] = btn
        return btn

    def _button_hover(self, e):
        if self.app.reduce_motion:
            return
        entering = str(getattr(e, "data", "")).lower() == "true"
        e.control.scale = 1.02 if entering else 1.0
        e.control.update()

    async def _animate_save_button_click(self, key: str, handler):
        btn = self._save_buttons.get(key)
        if not btn:
            handler()
            return
        if key in self._save_buttons_animating:
            return

        self._save_buttons_animating.add(key)
        try:
            if not self.app.reduce_motion:
                btn.scale = 0.95
                self.app.page.update()
                await asyncio.sleep(0.05)

                btn.scale = 1.0
                self.app.page.update()
                await asyncio.sleep(0.02)

            handler()
        finally:
            self._save_buttons_animating.discard(key)

    def _mark_button_success(self, key: str, text: str):
        btn = self._save_buttons.get(key)
        if not btn:
            return
        t = self.app.theme_mgr.get_theme()
        default_text = btn.content.value if isinstance(btn.content, ft.Text) else "Salvar"
        btn.content = ft.Text(text, color="#FFFFFF", weight=ft.FontWeight.W_600)
        btn.bgcolor = t["success"]
        self.app.page.update()
        self.app.page.run_task(self._restore_button_state, btn, default_text)

    async def _restore_button_state(self, btn, default_text: str):
        await asyncio.sleep(1.15)
        t = self.app.theme_mgr.get_theme()
        btn.content = ft.Text(default_text, color="#FFFFFF", weight=ft.FontWeight.W_600)
        btn.bgcolor = t["button"]
        self.app.page.update()

    def build(self):
        t = self.app.theme_mgr.get_theme()
        user = self.app.current_user
        self._save_buttons = {}
        self._reveal_blocks = []
        self._theme_card_map = {}
        self._save_buttons_animating.clear()
        controls = []

        controls.append(self._section_title(t, "Temas visuais", "Escolha o estilo da interface"))

        theme_cards = []
        for name, theme in THEMES.items():
            is_active = name == self.app.theme_mgr.current_theme

            dots = ft.Row(
                [
                    ft.Container(width=20, height=10, border_radius=5, bgcolor=theme["primary"]),
                    ft.Container(width=20, height=10, border_radius=5, bgcolor=theme["accent"]),
                    ft.Container(width=20, height=10, border_radius=5, bgcolor=theme["success"]),
                    ft.Container(width=20, height=10, border_radius=5, bgcolor=theme["danger"]),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            )

            footer = (
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=999,
                    bgcolor=t.get("surface_soft", t["card"]),
                    border=ft.border.all(1, t.get("border_soft", t["entry_border"])),
                    content=ft.Text(
                        "Ativo",
                        size=11,
                        color=theme["accent"],
                        weight=ft.FontWeight.BOLD,
                    ),
                )
                if is_active
                else ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=999,
                    bgcolor=t.get("surface_soft", t["card"]),
                    border=ft.border.all(1, t.get("border_soft", t["entry_border"])),
                    content=ft.Text(
                        "Aplicar",
                        size=11,
                        color=theme["primary"],
                        weight=ft.FontWeight.BOLD,
                    ),
                )
            )

            theme_card = ft.Container(
                width=170,
                height=138,
                border_radius=14,
                padding=12,
                bgcolor=theme["card"],
                border=ft.border.all(2 if is_active else 1, theme["accent"] if is_active else t.get("border_soft", t["entry_border"])),
                scale=1.0,
                animate_scale=self.app.motion_ms(120),
                on_hover=lambda e: self._hover_card_scale(e),
                on_click=None if is_active else lambda _, n=name: self.app.page.run_task(self._apply_theme_with_effect, n),
                content=ft.Column(
                    [
                        dots,
                        ft.Text(
                            f"{theme['emoji']} {name}",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=theme["text"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            theme["desc"][:42],
                            size=10,
                            color=theme["text_sec"],
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        footer,
                    ],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
            self._theme_card_map[name] = theme_card
            theme_cards.append(theme_card)

        theme_rows = []
        for i in range(0, len(theme_cards), 2):
            theme_rows.append(
                ft.Row(
                    theme_cards[i:i + 2],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.START,
                )
            )
        controls.append(ft.Column(theme_rows, spacing=8, tight=True))

        self._reduce_motion_cb = ft.Checkbox(
            label="Reduzir animacoes",
            value=self.app.reduce_motion,
            active_color=t["primary"],
            label_style=ft.TextStyle(color=t["text"]),
            on_change=self._toggle_reduce_motion,
        )
        controls.append(self._section_title(t, "Interacoes", "Preferencias de movimento e resposta visual"))
        controls.append(
            self._panel(
                t,
                ft.Column(
                    [
                        self._reduce_motion_cb,
                        ft.Text(
                            "Quando ativado, suaviza ou desativa animacoes para uma navegacao mais direta.",
                            size=12,
                            color=t["text_sec"],
                        ),
                    ],
                    spacing=8,
                ),
            )
        )

        controls.append(self._section_title(t, "Configuracoes do Pomodoro"))
        focus_val = user.get("pomodoro_focus", 25) if user else 25
        short_val = user.get("pomodoro_short", 5) if user else 5
        long_val = user.get("pomodoro_long", 15) if user else 15

        self._pom_focus = self._base_field(t, "Foco (min)", str(focus_val), number=True)
        self._pom_short = self._base_field(t, "Pausa curta", str(short_val), number=True)
        self._pom_long = self._base_field(t, "Pausa longa", str(long_val), number=True)

        controls.append(
            self._panel(
                t,
                ft.Column(
                    [
                        ft.Row([self._pom_focus, self._pom_short, self._pom_long], spacing=8),
                        self._make_save_button(t, "pomodoro", "Salvar Pomodoro", self._save_pomodoro, width=280, height=40),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )

        controls.append(self._section_title(t, "Metas diarias"))
        pom_goal = user.get("daily_pomodoro_goal", 4) if user else 4
        xp_goal = user.get("daily_xp_goal", 100) if user else 100
        quiz_goal = user.get("daily_quiz_goal", 10) if user else 10

        self._goal_pom = self._base_field(t, "Pomodoros/dia", str(pom_goal), number=True)
        self._goal_xp = self._base_field(t, "XP/dia", str(xp_goal), number=True)
        self._goal_quiz = self._base_field(t, "Questoes/dia", str(quiz_goal), number=True)

        controls.append(
            self._panel(
                t,
                ft.Column(
                    [
                        ft.Row([self._goal_pom, self._goal_xp, self._goal_quiz], spacing=8),
                        self._make_save_button(t, "goals", "Salvar Metas", self._save_goals, width=280, height=40),
                    ],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )

        if user:
            controls.append(self._section_title(t, "Perfil", "Alterar nome e senha"))
            self._name_field = self._base_field(t, "Nome de exibicao", user.get("display_name", ""), width=360)
            self._old_pw = self._base_field(t, "Senha atual", width=360)
            self._old_pw.password = True
            self._old_pw.can_reveal_password = True
            self._new_pw = self._base_field(t, "Nova senha", width=360)
            self._new_pw.password = True
            self._new_pw.can_reveal_password = True

            controls.append(
                self._panel(
                    t,
                    ft.Column(
                        [
                            self._name_field,
                            self._make_save_button(t, "name", "Salvar Nome", self._save_name, width=220, height=38),
                            ft.Divider(color=t.get("border_soft", t["secondary"])),
                            ft.Text("Alterar senha", size=14, weight=ft.FontWeight.BOLD, color=t["text"]),
                            self._old_pw,
                            self._new_pw,
                            self._make_save_button(t, "password", "Atualizar Senha", self._save_password, width=220, height=38),
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )

        controls.append(self._section_title(t, "Sobre"))
        controls.append(
            self._panel(
                t,
                ft.Text(
                    "Switch Focus v3.0 (Flet)\n\n"
                    "Aplicativo de estudos com metodo Pomodoro.\n"
                    "ENEM e concursos com quizzes e videos.\n"
                    "Gamificacao com XP, niveis e conquistas.\n"
                    "Flashcards com repeticao espacada.\n"
                    "Temas visuais profissionais.\n\n"
                    "Desenvolvido com Python + Flet + SQLite.",
                    size=13,
                    color=t["text_sec"],
                ),
            )
        )

        controls.append(ft.Container(height=18))

        content = ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column([self._reveal(c) for c in controls], spacing=12, scroll=ft.ScrollMode.AUTO),
        )
        self.app.page.run_task(self._animate_reveal)
        return content

    async def _apply_theme_with_effect(self, name: str):
        if self._theme_applying:
            return

        card = self._theme_card_map.get(name)
        self._theme_applying = True
        try:
            if not self.app.reduce_motion and card:
                card.scale = 0.96
                self.app.page.update()
                await asyncio.sleep(0.055)

                card.scale = 1.02
                self.app.page.update()
                await asyncio.sleep(0.045)

            self._apply_theme(name)
        finally:
            self._theme_applying = False

    def _apply_theme(self, name):
        self.app.theme_mgr.set_theme(name)
        if self.app.current_user:
            self.db.update_user_theme(self.app.current_user["id"], name)
        self.app.refresh_theme()

    def _save_pomodoro(self, e=None):
        try:
            focus = int(self._pom_focus.value)
            short = int(self._pom_short.value)
            long_ = int(self._pom_long.value)
        except (TypeError, ValueError):
            self.app.show_snackbar("Insira valores numericos validos.")
            return
        if focus < 1 or short < 1 or long_ < 1:
            self.app.show_snackbar("Valores devem ser maiores que zero.")
            return
        if self.app.current_user:
            uid = self.app.current_user["id"]
            self.db.update_user_pomodoro(uid, focus, short, long_)
            self.app.current_user["pomodoro_focus"] = focus
            self.app.current_user["pomodoro_short"] = short
            self.app.current_user["pomodoro_long"] = long_
            self.app.show_snackbar("Configuracoes do Pomodoro salvas.")
            self._mark_button_success("pomodoro", "Salvo")
        else:
            self.app.show_snackbar("Faca login para salvar.")

    def _save_goals(self, e=None):
        try:
            pom = int(self._goal_pom.value)
            xp = int(self._goal_xp.value)
            quiz = int(self._goal_quiz.value)
        except (TypeError, ValueError):
            self.app.show_snackbar("Insira valores numericos validos.")
            return
        if pom < 1 or xp < 1 or quiz < 1:
            self.app.show_snackbar("Valores devem ser maiores que zero.")
            return
        if self.app.current_user:
            uid = self.app.current_user["id"]
            self.db.update_user_goals(uid, pom, xp, quiz)
            self.app.current_user["daily_pomodoro_goal"] = pom
            self.app.current_user["daily_xp_goal"] = xp
            self.app.current_user["daily_quiz_goal"] = quiz
            self.app.show_snackbar("Metas diarias salvas.")
            self._mark_button_success("goals", "Salvo")
        else:
            self.app.show_snackbar("Faca login para salvar.")

    def _save_name(self, e=None):
        new_name = self._name_field.value.strip() if self._name_field.value else ""
        if not new_name:
            self.app.show_snackbar("Nome nao pode ser vazio.")
            return
        uid = self.app.current_user["id"]
        self.db.update_user_display_name(uid, new_name)
        self.app.current_user["display_name"] = new_name
        self.app.show_snackbar("Nome atualizado com sucesso.")
        self._mark_button_success("name", "Atualizado")

    def _save_password(self, e=None):
        old_pw = self._old_pw.value.strip() if self._old_pw.value else ""
        new_pw = self._new_pw.value.strip() if self._new_pw.value else ""
        if not old_pw or not new_pw:
            self.app.show_snackbar("Preencha os dois campos de senha.")
            return
        if len(new_pw) < 4:
            self.app.show_snackbar("Nova senha deve ter pelo menos 4 caracteres.")
            return
        uid = self.app.current_user["id"]
        success = self.db.update_user_password(uid, old_pw, new_pw)
        if success:
            self.app.show_snackbar("Senha atualizada com sucesso.")
            self._mark_button_success("password", "Atualizada")
        else:
            self.app.show_snackbar("Senha atual incorreta.", bgcolor="#C45144")

    def _reveal(self, control):
        shell = ft.Container(
            content=control,
            opacity=1.0 if self.app.reduce_motion else 0.0,
            offset=ft.Offset(0, 0) if self.app.reduce_motion else ft.Offset(0, 0.032),
            animate_opacity=self.app.motion_ms(220),
            animate_offset=self.app.motion_ms(220),
        )
        self._reveal_blocks.append(shell)
        return shell

    async def _animate_reveal(self):
        if self.app.reduce_motion or self._revealing:
            return
        if self.app._current_view_name != "settings":
            return
        self._revealing = True
        try:
            await asyncio.sleep(0)
            for block in self._reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.038)
        finally:
            self._revealing = False
