import threading
import asyncio

import flet as ft

from content_updater import ContentUpdater
from database import DatabaseManager
from themes import ThemeManager
from views.ui_components import soft_card, with_alpha


class SwitchFocusApp:
    """Aplicativo principal Switch Focus."""

    NAV_VIEWS = ["dashboard", "pomodoro", "tasks", "study", "more"]
    MOTION_PREF_KEY = "switch_focus.reduce_motion"

    def __init__(self, page: ft.Page):
        self.page = page
        self.db = DatabaseManager()
        self.theme_mgr = ThemeManager()
        self.updater = ContentUpdater(self.db, interval_hours=24)
        self.current_user = None
        self._views: dict = {}
        self._current_view_name = None
        self._active_view_obj = None
        self.reduce_motion = False
        self._more_reveal_blocks: list[ft.Container] = []
        self._revealing_more = False

    def initialize(self):
        self.reduce_motion = self._load_motion_pref()
        self.theme_mgr.set_active_view("dashboard")
        t = self.theme_mgr.get_theme()

        self.page.title = "Switch Focus"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = t["bg"]
        self.page.padding = 0
        self.page.window.width = 420
        self.page.window.height = 800
        self.page.window.min_width = 380
        self.page.window.min_height = 720
        self.page.theme = ft.Theme(
            color_scheme_seed=t["primary"],
            font_family="Segoe UI",
        )
        self.page.on_keyboard_event = self._on_keyboard_event

        self._content_stage = ft.Container(
            expand=True,
            animate_opacity=self.motion_ms(180),
            animate_offset=self.motion_ms(180),
            opacity=1.0,
            offset=ft.Offset(0, 0),
            content=ft.Container(expand=True),
        )

        self._content = ft.Container(
            expand=True,
            bgcolor=t["bg"],
            content=self._content_stage,
        )

        self._app_bar = ft.AppBar(
            title=ft.Text("Switch Focus", size=20, weight=ft.FontWeight.BOLD, color=t["text"]),
            bgcolor=t["sidebar"],
            center_title=False,
            actions=[],
            toolbar_height=66,
            elevation=0,
        )
        self.page.appbar = self._app_bar

        self._nav_bar = ft.NavigationBar(
            selected_index=0,
            bgcolor=t["sidebar"],
            indicator_color=with_alpha(t["primary"], "2E"),
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.HOME_ROUNDED, label="Home"),
                ft.NavigationBarDestination(icon=ft.Icons.TIMER_ROUNDED, label="Pomodoro"),
                ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST_ROUNDED, label="Tarefas"),
                ft.NavigationBarDestination(icon=ft.Icons.SCHOOL_ROUNDED, label="Estudar"),
                ft.NavigationBarDestination(icon=ft.Icons.MENU_ROUNDED, label="Mais"),
            ],
            on_change=self._on_nav_change,
        )
        self.page.navigation_bar = self._nav_bar

        self.page.add(self._content)
        self.show_view("dashboard")
        threading.Thread(target=self._auto_update_content, daemon=True).start()

    def _on_nav_change(self, e):
        idx = e.control.selected_index
        if idx < len(self.NAV_VIEWS):
            self.show_view(self.NAV_VIEWS[idx])

    def show_view(self, name: str):
        self._current_view_name = name
        self.theme_mgr.set_active_view(name)
        t = self.theme_mgr.get_theme()
        self._animate_transition_out()

        titles = {
            "dashboard": "Dashboard",
            "pomodoro": t.get("timer_title", "Pomodoro"),
            "tasks": "Tarefas",
            "study": t.get("study_title", "Estudar"),
            "flashcards": "Flashcards",
            "shorts": "Shorts",
            "history": "Historico",
            "settings": "Configuracoes",
            "theory": "Teorias ENEM",
            "enem_editais": "Editais do ENEM",
            "login": "Entrar",
            "more": "Mais",
        }
        self._app_bar.title = ft.Text(
            titles.get(name, name),
            size=18,
            weight=ft.FontWeight.BOLD,
            color=t["text"],
        )
        self._app_bar.bgcolor = t["sidebar"]

        sub_pages = {"flashcards", "shorts", "history", "settings", "login", "theory", "enem_editais"}
        if name in sub_pages:
            self._app_bar.leading = ft.IconButton(
                ft.Icons.ARROW_BACK_ROUNDED,
                icon_color=t["text"],
                on_click=lambda _: self.show_view("more"),
            )
        else:
            self._app_bar.leading = None

        self._app_bar.actions = []
        uid = self.get_user_id()
        if uid:
            xp_info = self.db.get_xp_info(uid)
            streak = self.db.get_streak(uid)
            lp = t.get("level_prefix", "Nivel")
            self._app_bar.actions.append(
                ft.Container(
                    content=ft.Text(
                        f"Nivel {xp_info['level']}  |  Streak {streak['streak']}d",
                        size=12,
                        color=t["text"],
                        weight=ft.FontWeight.BOLD,
                    ),
                    margin=ft.margin.only(right=16),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    bgcolor=t.get("chip_bg", t["card"]),
                    border=ft.border.all(1, t.get("border_soft", "#E9DCC9")),
                    border_radius=999,
                )
            )

        if name in self.NAV_VIEWS:
            self._nav_bar.selected_index = self.NAV_VIEWS.index(name)

        if name == "more":
            content = self._build_more_menu()
            self._active_view_obj = None
        else:
            if name in {"pomodoro", "study", "theory", "enem_editais", "flashcards"}:
                if name not in self._views:
                    self._views[name] = self._create_view(name)
                view = self._views[name]
            else:
                view = self._create_view(name)
            self._active_view_obj = view

            if view is None:
                self.page.update()
                return

            if hasattr(view, "on_show"):
                view.on_show()
            content = view.build()

        self._content.bgcolor = t["bg"]
        self._content_stage.content = content
        self._content_stage.opacity = 1.0
        self._content_stage.offset = ft.Offset(0, 0)
        self._nav_bar.bgcolor = t["sidebar"]
        self._nav_bar.indicator_color = with_alpha(t["primary"], "2E")
        self.page.bgcolor = t["bg"]
        self.page.update()

    def _create_view(self, name):
        if name == "dashboard":
            from views.dashboard_view import DashboardView

            return DashboardView(self)
        if name == "pomodoro":
            from views.pomodoro_view import PomodoroView

            return PomodoroView(self)
        if name == "tasks":
            from views.tasks_view import TasksView

            return TasksView(self)
        if name == "study":
            from views.study_view import StudyView

            return StudyView(self)
        if name == "flashcards":
            from views.flashcards_view import FlashcardsView

            return FlashcardsView(self)
        if name == "shorts":
            from views.shorts_view import ShortsView

            return ShortsView(self)
        if name == "history":
            from views.history_view import HistoryView

            return HistoryView(self)
        if name == "settings":
            from views.settings_view import SettingsView

            return SettingsView(self)
        if name == "theory":
            from views.theory_view import TheoryView

            return TheoryView(self)
        if name == "enem_editais":
            from views.enem_editais_view import EnemEditaisView

            return EnemEditaisView(self)
        if name == "login":
            from views.login_view import LoginView

            return LoginView(self)
        return None

    def _build_more_menu(self):
        t = self.theme_mgr.get_theme()
        self._more_reveal_blocks = []

        items = [
            (ft.Icons.MENU_BOOK_ROUNDED, "Teorias ENEM", "Conteudo teorico", "theory"),
            (ft.Icons.DESCRIPTION_ROUNDED, "Editais do ENEM", "Consulta rapida", "enem_editais"),
            (ft.Icons.STYLE_ROUNDED, "Flashcards", "Repeticao espaçada", "flashcards"),
            (ft.Icons.VIDEO_LIBRARY_ROUNDED, "Shorts / Videos", "Conteudo rapido", "shorts"),
            (ft.Icons.BAR_CHART_ROUNDED, "Historico", "Evolucao", "history"),
            (ft.Icons.SETTINGS_ROUNDED, "Configuracoes", "Preferencias", "settings"),
        ]

        if self.current_user:
            user_text = self.current_user.get("display_name", "Usuario")
            user_subtitle = "Conta conectada"
            items.append((ft.Icons.LOGOUT_ROUNDED, "Sair", "Encerrar sessao", "_logout"))
        else:
            user_text = "Convidado"
            user_subtitle = "Explorando sem conta"
            items.append((ft.Icons.LOGIN_ROUNDED, "Entrar / Cadastrar", "Salvar progresso", "login"))

        tiles = []
        for icon, label, subtitle, target in items:
            tiles.append(
                self._more_reveal(
                    soft_card(
                        t,
                        ft.ListTile(
                            leading=ft.Container(
                                width=42,
                                height=42,
                                border_radius=14,
                                bgcolor=t.get("surface_soft", t["card"]),
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(icon, color=t["primary"]),
                            ),
                            title=ft.Text(label, color=t["text"], size=15, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text(subtitle, color=t["text_sec"], size=11),
                            trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=t["text_sec"]),
                            on_click=lambda _, tgt=target: self._on_more_item(tgt),
                        ),
                        bgcolor=t["card"],
                        radius=22,
                        padding=8,
                    ),
                )
            )

        content = ft.Container(
            bgcolor=t["bg"],
            padding=18,
            expand=True,
            content=ft.Column(
                controls=[
                    self._more_reveal(soft_card(
                        t,
                        ft.Row(
                            [
                                ft.Container(
                                    width=56,
                                    height=56,
                                    border_radius=20,
                                    bgcolor=t.get("surface_soft", t["card"]),
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, size=34, color=t["primary"]),
                                ),
                                ft.Column(
                                    [
                                        ft.Text(user_text, size=18, weight=ft.FontWeight.BOLD, color=t["text"]),
                                        ft.Text(user_subtitle, size=12, color=t["text_sec"]),
                                        ft.Text(
                                            t.get("welcome", "Bem-vindo ao Switch Focus!"),
                                            size=12,
                                            color=t["text_sec"],
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=15,
                        ),
                        padding=18,
                        bgcolor=t["card"],
                        radius=24,
                    )),
                    self._more_reveal(ft.Text("Mais recursos", size=18, weight=ft.FontWeight.BOLD, color=t["text"])),
                    *tiles,
                ],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.page.run_task(self._animate_more_reveal)
        return content

    def _on_more_item(self, target):
        if target == "_logout":
            self.logout()
        else:
            self.show_view(target)

    def get_user_id(self):
        return self.current_user["id"] if self.current_user else None

    def set_user(self, user_dict):
        self.current_user = user_dict
        if user_dict:
            if user_dict.get("theme"):
                self.theme_mgr.set_theme(user_dict["theme"])
            self.db.update_streak(user_dict["id"])
            self._apply_theme()

    def logout(self):
        self.current_user = None
        self._apply_theme()
        self.show_view("dashboard")

    def refresh_xp_sidebar(self):
        if self._current_view_name:
            uid = self.get_user_id()
            if uid:
                t = self.theme_mgr.get_theme()
                xp_info = self.db.get_xp_info(uid)
                streak = self.db.get_streak(uid)
                self._app_bar.actions = [
                    ft.Container(
                        content=ft.Text(
                            f"Nivel {xp_info['level']}  |  Streak {streak['streak']}d",
                            size=12,
                            color=t["text"],
                            weight=ft.FontWeight.BOLD,
                        ),
                        margin=ft.margin.only(right=16),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=t.get("chip_bg", t["card"]),
                        border=ft.border.all(1, t.get("border_soft", "#E9DCC9")),
                        border_radius=999,
                    )
                ]

    def _apply_theme(self):
        t = self.theme_mgr.get_theme()
        self.page.bgcolor = t["bg"]
        self._content.bgcolor = t["bg"]
        self._nav_bar.bgcolor = t["sidebar"]
        self._nav_bar.indicator_color = with_alpha(t["primary"], "2E")
        self._app_bar.bgcolor = t["sidebar"]
        self._sync_motion_controls()

    def refresh_theme(self):
        self._apply_theme()
        self._views = {}
        if self._current_view_name:
            self.show_view(self._current_view_name)

    def show_snackbar(self, message, bgcolor=None):
        t = self.theme_mgr.get_theme()
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="#FFFFFF"),
            bgcolor=bgcolor or t["primary"],
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_dialog(self, title, message, on_ok=None):
        def close(e):
            dlg.open = False
            self.page.update()
            if on_ok:
                on_ok()

        dlg = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[ft.TextButton("OK", on_click=close)],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def show_confirm(self, title, message, on_confirm):
        def close(e):
            dlg.open = False
            self.page.update()

        def confirm(e):
            dlg.open = False
            self.page.update()
            on_confirm()

        dlg = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("Cancelar", on_click=close),
                ft.TextButton("Confirmar", on_click=confirm),
            ],
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def motion_ms(self, duration: int) -> int:
        return 0 if self.reduce_motion else duration

    def set_reduce_motion(self, enabled: bool):
        enabled = bool(enabled)
        if self.reduce_motion == enabled:
            return
        self.reduce_motion = enabled
        self._save_motion_pref(enabled)
        self._sync_motion_controls()
        if self._current_view_name:
            self.show_view(self._current_view_name)

    def _sync_motion_controls(self):
        if hasattr(self, "_content_stage") and self._content_stage:
            self._content_stage.animate_opacity = self.motion_ms(180)
            self._content_stage.animate_offset = self.motion_ms(180)

    def _animate_transition_out(self):
        if not self._current_view_name:
            return
        if self.reduce_motion:
            return
        if not getattr(self, "_content_stage", None):
            return
        self._content_stage.opacity = 0.0
        self._content_stage.offset = ft.Offset(0.018, 0)
        try:
            self.page.update()
        except Exception:
            pass

    def _load_motion_pref(self) -> bool:
        try:
            return bool(self.page.client_storage.get(self.MOTION_PREF_KEY))
        except Exception:
            pass

        # Compat: em algumas versoes existe page.session.get e em outras page.session.store.get.
        try:
            return bool(self.page.session.get(self.MOTION_PREF_KEY))
        except Exception:
            pass
        try:
            return bool(self.page.session.store.get(self.MOTION_PREF_KEY))
        except Exception:
            return False

    def _save_motion_pref(self, enabled: bool):
        try:
            self.page.client_storage.set(self.MOTION_PREF_KEY, bool(enabled))
            return
        except Exception:
            pass
        try:
            self.page.session.set(self.MOTION_PREF_KEY, bool(enabled))
            return
        except Exception:
            pass
        try:
            self.page.session.store.set(self.MOTION_PREF_KEY, bool(enabled))
        except Exception:
            pass

    def _on_keyboard_event(self, e: ft.KeyboardEvent):
        view = self._active_view_obj
        if view and hasattr(view, "handle_keyboard_event"):
            try:
                consumed = view.handle_keyboard_event(e)
                if consumed:
                    return
            except Exception:
                pass

    def _more_reveal(self, control):
        shell = ft.Container(
            content=control,
            opacity=1.0 if self.reduce_motion else 0.0,
            offset=ft.Offset(0, 0) if self.reduce_motion else ft.Offset(0, 0.032),
            animate_opacity=self.motion_ms(220),
            animate_offset=self.motion_ms(220),
        )
        self._more_reveal_blocks.append(shell)
        return shell

    async def _animate_more_reveal(self):
        if self.reduce_motion or self._revealing_more:
            return
        if self._current_view_name != "more":
            return
        self._revealing_more = True
        try:
            await asyncio.sleep(0)
            for block in self._more_reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.page.update()
                await asyncio.sleep(0.04)
        finally:
            self._revealing_more = False

    def _auto_update_content(self):
        try:
            self.updater.start_update()
        except Exception:
            pass
