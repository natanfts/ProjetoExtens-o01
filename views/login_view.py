import flet as ft

from views.ui_components import primary_button, secondary_button, soft_card


class LoginView:
    """Tela de login e cadastro com estilo profissional claro."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._mode = "login"

    def build(self):
        t = self.app.theme_mgr.get_theme()

        self._username = self._build_field(t, "Usuario", ft.Icons.PERSON_OUTLINE_ROUNDED)
        self._password = self._build_field(
            t,
            "Senha",
            ft.Icons.LOCK_OUTLINE_ROUNDED,
            password=True,
            can_reveal_password=True,
        )
        self._display_name = self._build_field(
            t,
            "Nome de exibicao",
            ft.Icons.BADGE_OUTLINED,
            visible=False,
        )

        self._title = ft.Text("Entrar", size=30, weight=ft.FontWeight.BOLD, color=t["text"])
        self._subtitle = ft.Text(
            "Acesse sua conta para salvar progresso, streak e conquistas.",
            size=13,
            color=t["text_sec"],
            text_align=ft.TextAlign.CENTER,
        )

        self._action_btn = primary_button(
            t,
            "Entrar",
            self._do_action,
            icon=ft.Icons.LOGIN_ROUNDED,
            width=320,
            height=50,
        )
        self._toggle_btn = ft.TextButton(
            "Nao tem conta? Cadastre-se",
            on_click=self._toggle_mode,
            style=ft.ButtonStyle(color=t["text_sec"]),
        )
        self._skip_btn = secondary_button(
            t,
            "Continuar como convidado",
            lambda _: self.app.show_view("dashboard"),
            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
            width=320,
            height=50,
        )

        left_panel = soft_card(
            t,
            ft.Column(
                [
                    ft.Container(
                        width=58,
                        height=58,
                        border_radius=20,
                        bgcolor=t.get("chip_bg", t["card"]),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, size=28, color=t["primary"]),
                    ),
                    ft.Text(
                        "Produtividade com cara de produto premium.",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=t["text"],
                    ),
                    ft.Text(
                        "Login libera sincronizacao de dados, metas, historico, gamificacao e personalizacao.",
                        size=13,
                        color=t["text_sec"],
                    ),
                    ft.Column(
                        [
                            self._feature_line(t, "XP, niveis e evolucao visivel"),
                            self._feature_line(t, "Streak diario para reforcar consistencia"),
                            self._feature_line(t, "Conquistas com feedback imediato"),
                            self._feature_line(t, "Metas e tarefas em um fluxo unico"),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=18,
            ),
            radius=30,
            padding=28,
            expand=True,
            bgcolor=t["card"],
        )

        form_panel = soft_card(
            t,
            ft.Column(
                [
                    self._title,
                    self._subtitle,
                    ft.Container(height=4),
                    self._username,
                    self._password,
                    self._display_name,
                    ft.Container(height=8),
                    self._action_btn,
                    self._toggle_btn,
                    ft.Container(height=4),
                    self._skip_btn,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=30,
            padding=28,
            width=390,
            bgcolor=t["card"],
        )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.only(left=18, top=18, right=18, bottom=20),
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(content=left_panel, col={"xs": 12, "md": 7}),
                    ft.Container(content=form_panel, col={"xs": 12, "md": 5}),
                ],
                columns=12,
                spacing=16,
                run_spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def on_show(self):
        self._mode = "login"

    def _build_field(self, t, label, icon, **kwargs):
        return ft.TextField(
            label=label,
            width=320,
            height=56,
            prefix_icon=icon,
            border_radius=16,
            bgcolor=t["entry_bg"],
            border_color=t.get("border_soft", t["entry_border"]),
            focused_border_color=t["primary"],
            color=t["text"],
            label_style=ft.TextStyle(color=t["text_sec"]),
            text_style=ft.TextStyle(size=14, color=t["text"]),
            **kwargs,
        )

    def _feature_line(self, t, text):
        return ft.Row(
            [
                ft.Container(
                    width=22,
                    height=22,
                    border_radius=999,
                    bgcolor=t.get("chip_bg", t["card"]),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.CHECK_ROUNDED, size=14, color=t["primary"]),
                ),
                ft.Text(text, size=12, color=t["text_sec"]),
            ],
            spacing=10,
        )

    def _toggle_mode(self, e=None):
        if self._mode == "login":
            self._mode = "register"
            self._title.value = "Criar conta"
            self._subtitle.value = "Cadastre-se para salvar seu desempenho e personalizar a experiencia."
            self._action_btn.content = "Cadastrar"
            self._action_btn.icon = ft.Icons.PERSON_ADD_ALT_1_ROUNDED
            self._toggle_btn.content = "Ja tem conta? Faca login"
            self._display_name.visible = True
        else:
            self._mode = "login"
            self._title.value = "Entrar"
            self._subtitle.value = "Acesse sua conta para salvar progresso, streak e conquistas."
            self._action_btn.content = "Entrar"
            self._action_btn.icon = ft.Icons.LOGIN_ROUNDED
            self._toggle_btn.content = "Nao tem conta? Cadastre-se"
            self._display_name.visible = False
        self.app.page.update()

    def _do_action(self, e=None):
        username = self._username.value.strip() if self._username.value else ""
        password = self._password.value.strip() if self._password.value else ""

        if not username or not password:
            self.app.show_snackbar("Preencha usuario e senha.")
            return

        if self._mode == "register" and len(password) < 4:
            self.app.show_snackbar("A senha deve ter pelo menos 4 caracteres.")
            return

        if self._mode == "login":
            user = self.db.authenticate(username, password)
            if user:
                self.app.set_user(user)
                self.app.show_snackbar("Login realizado com sucesso.")
                self.app.show_view("dashboard")
            else:
                self.app.show_snackbar("Usuario ou senha invalidos.", bgcolor="#C45144")
        else:
            display = (self._display_name.value or "").strip() or username
            user = self.db.create_user(username, password, display)
            if user:
                self.app.set_user(user)
                self.app.show_snackbar("Conta criada com sucesso.")
                self.app.show_view("dashboard")
            else:
                self.app.show_snackbar("Usuario ja existe.", bgcolor="#C45144")
