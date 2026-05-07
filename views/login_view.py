import asyncio

import flet as ft

from views.ui_components import primary_button, secondary_button, soft_card


class LoginView:
    """Tela de login e cadastro com estilo profissional claro."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._mode = "login"
        self._lead_index = 0
        self._reveal_blocks: list[ft.Container] = []
        self._revealing = False
        self._lead_drag_acc = 0.0
        self._lead_auto_enabled = True
        self._lead_auto_task_running = False
        self._leads = [
            {
                "icon": ft.Icons.AUTO_AWESOME_ROUNDED,
                "title": "Produtividade com cara de produto premium.",
                "desc": "Login libera sincronizacao de dados, metas, historico, gamificacao e personalizacao.",
                "features": [
                    "XP, niveis e evolucao visivel",
                    "Streak diario para reforcar consistencia",
                    "Conquistas com feedback imediato",
                    "Metas e tarefas em um fluxo unico",
                ],
            },
            {
                "icon": ft.Icons.TIMELINE_ROUNDED,
                "title": "Controle total da sua evolucao.",
                "desc": "Acompanhe desempenho diario com indicadores simples e metas de estudo realistas.",
                "features": [
                    "Historico com progresso por sessoes",
                    "Comparativo rapido por dia",
                    "Metas de XP e pomodoro editaveis",
                    "Ritmo de estudo consistente",
                ],
            },
            {
                "icon": ft.Icons.STYLE_ROUNDED,
                "title": "Aprendizado ativo com flashcards.",
                "desc": "Revisao inteligente para fixar conteudo com menos esforco e mais constancia.",
                "features": [
                    "Repeticao espacada no fluxo diario",
                    "Navegacao clara entre cards",
                    "Classificacao por dificuldade",
                    "Mais retencao no longo prazo",
                ],
            },
        ]

    def build(self):
        t = self.app.theme_mgr.get_theme()
        self._reveal_blocks = []

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

        self._lead_icon = ft.Icon(self._leads[0]["icon"], size=28, color=t["primary"])
        self._lead_title = ft.Text(
            self._leads[0]["title"],
            size=28,
            weight=ft.FontWeight.BOLD,
            color=t["text"],
        )
        self._lead_desc = ft.Text(
            self._leads[0]["desc"],
            size=13,
            color=t["text_sec"],
        )
        self._lead_feature_col = ft.Column(spacing=10)
        self._lead_progress = ft.Text("", size=12, color=t["text_sec"])
        self._lead_dots = ft.Row(spacing=6)
        self._lead_stage = ft.Container(
            content=ft.Column(
                [
                    self._lead_title,
                    self._lead_desc,
                    self._lead_feature_col,
                ],
                spacing=18,
            ),
            animate_opacity=self.app.motion_ms(220),
            animate_offset=self.app.motion_ms(220),
            opacity=1.0,
            offset=ft.Offset(0, 0),
        )

        left_panel = soft_card(
            t,
            ft.Column(
                [
                    self._reveal_block(ft.Container(
                        width=58,
                        height=58,
                        border_radius=20,
                        bgcolor=t.get("chip_bg", t["card"]),
                        alignment=ft.Alignment.CENTER,
                        content=self._lead_icon,
                    )),
                    self._reveal_block(self._lead_stage),
                    self._reveal_block(ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.CHEVRON_LEFT_ROUNDED,
                                icon_color=t["text"],
                                bgcolor=t.get("surface_soft", t["card"]),
                                on_click=self._prev_lead,
                                tooltip="Lead anterior",
                            ),
                            ft.Column(
                                [
                                    self._lead_dots,
                                    self._lead_progress,
                                    ft.Text("Use as setas para navegar", size=11, color=t["text_sec"]),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=3,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CHEVRON_RIGHT_ROUNDED,
                                icon_color=t["text"],
                                bgcolor=t.get("surface_soft", t["card"]),
                                on_click=self._next_lead,
                                tooltip="Proximo lead",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )),
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
                    self._reveal_block(self._title),
                    self._reveal_block(self._subtitle),
                    self._reveal_block(ft.Container(height=4)),
                    self._reveal_block(self._username),
                    self._reveal_block(self._password),
                    self._reveal_block(self._display_name),
                    self._reveal_block(ft.Container(height=8)),
                    self._reveal_block(self._action_btn),
                    self._reveal_block(self._toggle_btn),
                    self._reveal_block(ft.Container(height=4)),
                    self._reveal_block(self._skip_btn),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            radius=30,
            padding=28,
            width=390,
            bgcolor=t["card"],
        )

        lead_swipe_panel = ft.GestureDetector(
            content=left_panel,
            on_horizontal_drag_start=self._on_lead_drag_start,
            on_horizontal_drag_update=self._on_lead_drag_update,
            on_horizontal_drag_end=self._on_lead_drag_end,
        )

        layout = ft.ResponsiveRow(
            controls=[
                ft.Container(content=lead_swipe_panel, col={"xs": 12, "md": 7}),
                ft.Container(content=form_panel, col={"xs": 12, "md": 5}),
            ],
            columns=12,
            spacing=16,
            run_spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._render_lead(initial=True)
        self.app.page.run_task(self._lead_auto_loop)
        self.app.page.run_task(self._animate_reveal)

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.only(left=18, top=18, right=18, bottom=20),
            content=ft.ListView(
                expand=True,
                spacing=0,
                padding=0,
                controls=[layout],
            ),
        )

    def on_show(self):
        self._mode = "login"
        self._lead_index = 0
        self._lead_auto_enabled = True

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

    def _reveal_block(self, control):
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
        if self.app._current_view_name != "login":
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

    def _toggle_mode(self, e=None):
        if self._mode == "login":
            self._mode = "register"
            self._title.value = "Criar conta"
            self._subtitle.value = "Cadastre-se para salvar seu desempenho e personalizar a experiencia."
            self._action_btn.content = ft.Text("Cadastrar", color="#FFFFFF", weight=ft.FontWeight.W_600)
            self._action_btn.icon = ft.Icons.PERSON_ADD_ALT_1_ROUNDED
            self._toggle_btn.content = "Ja tem conta? Faca login"
            self._display_name.visible = True
        else:
            self._mode = "login"
            self._title.value = "Entrar"
            self._subtitle.value = "Acesse sua conta para salvar progresso, streak e conquistas."
            self._action_btn.content = ft.Text("Entrar", color="#FFFFFF", weight=ft.FontWeight.W_600)
            self._action_btn.icon = ft.Icons.LOGIN_ROUNDED
            self._toggle_btn.content = "Nao tem conta? Cadastre-se"
            self._display_name.visible = False
        self.app.page.update()

    def _render_lead(self, direction: int = 0, initial: bool = False):
        lead = self._leads[self._lead_index]
        t = self.app.theme_mgr.get_theme()

        if not initial:
            self._lead_stage.opacity = 0.35
            self._lead_stage.offset = ft.Offset(0.06 * (direction or 1), 0)
            self.app.page.update()

        self._lead_icon.name = lead["icon"]
        self._lead_title.value = lead["title"]
        self._lead_desc.value = lead["desc"]

        self._lead_feature_col.controls = [self._feature_line(t, f) for f in lead["features"]]
        self._lead_progress.value = f"Lead {self._lead_index + 1}/{len(self._leads)}"
        self._lead_dots.controls = [
            ft.Container(
                width=9 if i == self._lead_index else 7,
                height=9 if i == self._lead_index else 7,
                border_radius=999,
                bgcolor=t["primary"] if i == self._lead_index else t.get("border_soft", t["entry_border"]),
            )
            for i in range(len(self._leads))
        ]
        self._lead_stage.opacity = 1.0
        self._lead_stage.offset = ft.Offset(0, 0)
        if not initial:
            self.app.page.update()

    def _next_lead(self, e=None):
        self._lead_index = (self._lead_index + 1) % len(self._leads)
        self._render_lead(direction=1)

    def _prev_lead(self, e=None):
        self._lead_index = (self._lead_index - 1) % len(self._leads)
        self._render_lead(direction=-1)

    def _on_lead_drag_start(self, e):
        self._lead_drag_acc = 0.0
        self._lead_auto_enabled = False

    def _on_lead_drag_update(self, e):
        dx = 0.0
        if hasattr(e, "delta_x") and e.delta_x is not None:
            dx = float(e.delta_x)
        elif hasattr(e, "primary_delta") and e.primary_delta is not None:
            dx = float(e.primary_delta)
        self._lead_drag_acc += dx
        if self._lead_stage:
            drift = max(-0.12, min(0.12, self._lead_drag_acc / 420.0))
            self._lead_stage.offset = ft.Offset(drift, 0)
            self._lead_stage.opacity = 0.96
            self.app.page.update()

    def _on_lead_drag_end(self, e):
        velocity = 0.0
        if hasattr(e, "primary_velocity") and e.primary_velocity:
            velocity = float(e.primary_velocity)
        elif hasattr(e, "velocity_x") and e.velocity_x:
            velocity = float(e.velocity_x)

        threshold = 55
        if self._lead_drag_acc <= -threshold or velocity <= -350:
            self._next_lead()
        elif self._lead_drag_acc >= threshold or velocity >= 350:
            self._prev_lead()
        else:
            if self._lead_stage:
                self._lead_stage.offset = ft.Offset(0, 0)
                self._lead_stage.opacity = 1.0
                self.app.page.update()

        self._lead_drag_acc = 0.0
        self._lead_auto_enabled = True

    async def _lead_auto_loop(self):
        if self._lead_auto_task_running:
            return
        self._lead_auto_task_running = True
        try:
            while self.app._current_view_name == "login":
                await asyncio.sleep(5.5)
                if self.app._current_view_name != "login":
                    break
                if self._lead_auto_enabled:
                    self._next_lead()
        finally:
            self._lead_auto_task_running = False

    def handle_keyboard_event(self, e: ft.KeyboardEvent):
        key = (e.key or "").lower()
        if key in {"arrow right", "arrowright", "right"}:
            self._lead_auto_enabled = False
            self._next_lead()
            self._lead_auto_enabled = True
            return True
        if key in {"arrow left", "arrowleft", "left"}:
            self._lead_auto_enabled = False
            self._prev_lead()
            self._lead_auto_enabled = True
            return True
        if key in {"enter", "numpad enter"}:
            self._do_action()
            return True
        return False

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
