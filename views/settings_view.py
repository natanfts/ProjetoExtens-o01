import flet as ft

from themes import THEMES


class SettingsView:
    """Configuracoes do app: temas, pomodoro, metas e perfil."""

    def __init__(self, app):
        self.app = app
        self.db = app.db

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

    def build(self):
        t = self.app.theme_mgr.get_theme()
        user = self.app.current_user
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
                else ft.TextButton(
                    "Aplicar",
                    on_click=lambda _, n=name: self._apply_theme(n),
                    style=ft.ButtonStyle(color=theme["primary"]),
                )
            )

            theme_cards.append(
                ft.Container(
                    width=170,
                    height=138,
                    border_radius=14,
                    padding=12,
                    bgcolor=theme["card"],
                    border=ft.border.all(2 if is_active else 1, theme["accent"] if is_active else t.get("border_soft", t["entry_border"])),
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
            )

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
                        ft.ElevatedButton(
                            "Salvar Pomodoro",
                            height=40,
                            width=280,
                            bgcolor=t["button"],
                            color="#FFFFFF",
                            on_click=self._save_pomodoro,
                        ),
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
                        ft.ElevatedButton(
                            "Salvar Metas",
                            height=40,
                            width=280,
                            bgcolor=t["button"],
                            color="#FFFFFF",
                            on_click=self._save_goals,
                        ),
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
                            ft.ElevatedButton(
                                "Salvar Nome",
                                height=38,
                                width=220,
                                bgcolor=t["button"],
                                color="#FFFFFF",
                                on_click=self._save_name,
                            ),
                            ft.Divider(color=t.get("border_soft", t["secondary"])),
                            ft.Text("Alterar senha", size=14, weight=ft.FontWeight.BOLD, color=t["text"]),
                            self._old_pw,
                            self._new_pw,
                            ft.ElevatedButton(
                                "Atualizar Senha",
                                height=38,
                                width=220,
                                bgcolor=t["button"],
                                color="#FFFFFF",
                                on_click=self._save_password,
                            ),
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

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(controls, spacing=12, scroll=ft.ScrollMode.AUTO),
        )

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
        else:
            self.app.show_snackbar("Senha atual incorreta.", bgcolor="#C45144")
