import asyncio
import platform
import threading
from datetime import datetime

import flet as ft

from views.ui_components import filled_button, progress_track, secondary_button, soft_card, with_alpha

if platform.system() == "Windows":
    import winsound
else:
    winsound = None


class PomodoroView:
    """Timer Pomodoro com controles e selecao de tarefa."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._reveal_blocks: list[ft.Container] = []
        self._revealing = False

        self._focus_min = 25
        self._short_min = 5
        self._long_min = 15
        self._seconds_left = self._focus_min * 60
        self._running = False
        self._session_type = "foco"
        self._sessions_done = 0
        self._started_at = None
        self._selected_task = None

        self._time_label = ft.Text("25:00", size=72, weight=ft.FontWeight.BOLD)
        self._session_label = ft.Text("Sessao de foco", size=16, weight=ft.FontWeight.W_600)
        self._counter_label = ft.Text("Sessao 0/4", size=13)
        self._progress_bar = ft.ProgressBar(value=1.0, height=10, border_radius=5)
        self._task_label = ft.Text("Nenhuma tarefa selecionada", size=12)
        self._time_shell = ft.Container(
            content=self._time_label,
            scale=1.0,
            opacity=1.0,
            animate_scale=260,
            animate_opacity=260,
        )
        self._progress_shell = ft.Container(
            content=self._progress_bar,
            width=280,
            padding=ft.padding.only(top=10),
            scale=1.0,
            animate_scale=220,
        )
        self._urgent_pulse = False

        self._start_btn = ft.ElevatedButton(content=ft.Text("Iniciar"), height=44, width=120, on_click=self._start)
        self._pause_btn = ft.ElevatedButton(content=ft.Text("Pausar"), height=44, width=120, on_click=self._pause, disabled=True)
        self._reset_btn = ft.ElevatedButton(content=ft.Text("Reset"), height=44, width=120, on_click=self._reset)
        self._skip_btn = ft.ElevatedButton(content=ft.Text("Pular pausa"), height=44, width=130, on_click=self._skip_break, visible=False)

    def on_show(self):
        self._load_durations()
        self._update_display()

    def _btn_style(self, theme, bgcolor):
        return ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=14),
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 5,
                ft.ControlState.PRESSED: 1,
            },
            overlay_color={
                ft.ControlState.HOVERED: "#14FFFFFF",
                ft.ControlState.PRESSED: "#24FFFFFF",
            },
            animation_duration=160,
            bgcolor={
                ft.ControlState.DEFAULT: bgcolor,
                ft.ControlState.HOVERED: with_alpha(bgcolor, "EE"),
                ft.ControlState.PRESSED: with_alpha(bgcolor, "CC"),
            },
            color="#FFFFFF",
        )

    def build(self):
        t = self.app.theme_mgr.get_theme()
        self._reveal_blocks = []

        self._time_label.color = t["text"]
        self._session_label.color = t["primary"]
        self._counter_label.color = t["text_sec"]
        self._progress_bar.color = t["progress"]
        self._progress_bar.bgcolor = with_alpha(t["primary"], "20")
        self._task_label.color = t["text_sec"]
        self._time_shell.animate_scale = self.app.motion_ms(260)
        self._time_shell.animate_opacity = self.app.motion_ms(260)
        self._progress_shell.animate_scale = self.app.motion_ms(220)
        self._apply_urgency_feedback(self._running and self._session_type == "foco" and self._seconds_left <= 10)

        self._start_btn.style = self._btn_style(t, t["success"])
        self._pause_btn.style = self._btn_style(t, t["warning"])
        self._reset_btn.style = self._btn_style(t, t["danger"])
        self._skip_btn.style = self._btn_style(t, t["primary"])

        labels = {
            "foco": t.get("focus_label", "Sessao de foco"),
            "pausa_curta": t.get("short_break_label", "Pausa curta"),
            "pausa_longa": t.get("long_break_label", "Pausa longa"),
        }
        self._session_label.value = labels.get(self._session_type, "Sessao de foco")

        mode_controls = []
        for txt, stype in [("Foco", "foco"), ("Pausa curta", "pausa_curta"), ("Pausa longa", "pausa_longa")]:
            is_active = self._session_type == stype
            if is_active:
                mode_controls.append(
                    filled_button(
                        t,
                        txt,
                        lambda _, s=stype: self._set_type(s),
                        bgcolor=t["primary"],
                        height=36,
                    )
                )
            else:
                mode_controls.append(
                    secondary_button(
                        t,
                        txt,
                        lambda _, s=stype: self._set_type(s),
                        height=36,
                    )
                )

        pick_task_btn = secondary_button(
            t,
            "Selecionar tarefa",
            self._pick_task,
            icon=ft.Icons.CHECKLIST_ROUNDED,
            height=38,
        )

        timer_card = soft_card(
            t,
            ft.Column(
                [
                    self._session_label,
                    self._time_shell,
                    self._counter_label,
                    self._progress_shell,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            width=360,
            height=330,
            radius=28,
            padding=20,
            bgcolor=t["card"],
        )

        content = ft.Container(
            expand=True,
            bgcolor=t["bg"],
            alignment=ft.Alignment.TOP_CENTER,
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            content=ft.Column(
                [
                    self._reveal(timer_card),
                    self._reveal(ft.Row([self._start_btn, self._pause_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10)),
                    self._reveal(ft.Row([self._reset_btn, self._skip_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=10)),
                    self._reveal(soft_card(
                        t,
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TASK_ALT_ROUNDED, color=t["primary"], size=18),
                                ft.Container(content=self._task_label, expand=True),
                                pick_task_btn,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=12,
                        radius=18,
                        bgcolor=t["card"],
                    )),
                    self._reveal(ft.Row(
                        mode_controls,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                    )),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        )
        self.app.page.run_task(self._animate_reveal)
        return content

    def _reveal(self, control):
        shell = ft.Container(
            content=control,
            opacity=1.0 if self.app.reduce_motion else 0.0,
            offset=ft.Offset(0, 0) if self.app.reduce_motion else ft.Offset(0, 0.035),
            animate_opacity=self.app.motion_ms(220),
            animate_offset=self.app.motion_ms(220),
        )
        self._reveal_blocks.append(shell)
        return shell

    async def _animate_reveal(self):
        if self.app.reduce_motion or self._revealing:
            return
        if self.app._current_view_name != "pomodoro":
            return
        self._revealing = True
        try:
            await asyncio.sleep(0)
            for block in self._reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.045)
        finally:
            self._revealing = False

    def _start(self, e=None):
        if not self._running:
            self._running = True
            self._started_at = self._started_at or datetime.now().isoformat()
            self._start_btn.disabled = True
            self._pause_btn.disabled = False
            self.app.page.update()
            self.app.page.run_task(self._tick_loop)

    def _pause(self, e=None):
        self._running = False
        self._start_btn.disabled = False
        self._start_btn.content = ft.Text("Continuar")
        self._pause_btn.disabled = True
        self._apply_urgency_feedback(False)
        self.app.page.update()

    def _reset(self, e=None):
        self._running = False
        self._load_durations()
        self._seconds_left = self._get_duration() * 60
        self._started_at = None
        self._start_btn.disabled = False
        self._start_btn.content = ft.Text("Iniciar")
        self._pause_btn.disabled = True
        self._progress_bar.value = 1.0
        self._apply_urgency_feedback(False)
        self._update_display()
        self.app.page.update()

    async def _tick_loop(self):
        while self._running and self._seconds_left > 0:
            await asyncio.sleep(1)
            if not self._running:
                break
            self._seconds_left -= 1
            total = self._get_duration() * 60
            self._progress_bar.value = self._seconds_left / total if total else 0
            self._update_display()
            self._apply_urgency_feedback(self._session_type == "foco" and self._seconds_left <= 10)
            try:
                self.app.page.update()
            except Exception:
                break

        if self._seconds_left <= 0 and self._running:
            self._running = False
            self._session_complete()

    def _session_complete(self):
        self._start_btn.disabled = False
        self._start_btn.content = ft.Text("Iniciar")
        self._pause_btn.disabled = True

        duration = self._get_duration()
        self.db.save_session(
            self._session_type,
            duration,
            self._started_at or datetime.now().isoformat(),
            user_id=self.app.get_user_id(),
            task_id=self._selected_task["id"] if self._selected_task else None,
        )

        if self._session_type == "foco":
            self._sessions_done += 1
            if self._selected_task:
                self.db.increment_task_pomodoro(self._selected_task["id"])
            uid = self.app.get_user_id()
            if uid:
                self.db.add_xp(uid, 25, "pomodoro", f"Pomodoro de {duration} min")
                self.db.update_streak(uid)
                self.db.update_daily_goal_progress(uid, "pomodoro")
                self.db.update_daily_goal_progress(uid, "xp", 25)
                self.db.check_and_grant_achievements(uid)
                self.app.refresh_xp_sidebar()

        def _beep():
            if winsound:
                winsound.Beep(800, 600)
            else:
                print("\a")

        threading.Thread(target=_beep, daemon=True).start()

        if self._session_type == "foco":
            if self._sessions_done % 4 == 0:
                self._set_type("pausa_longa")
            else:
                self._set_type("pausa_curta")
        else:
            self._set_type("foco")

        self._started_at = None
        self.app.show_snackbar("Sessao concluida")
        try:
            self.app.page.update()
        except Exception:
            pass

    def _set_type(self, stype, e=None):
        self._running = False
        self._session_type = stype
        self._load_durations()
        self._seconds_left = self._get_duration() * 60
        self._progress_bar.value = 1.0
        self._start_btn.disabled = False
        self._start_btn.content = ft.Text("Iniciar")
        self._pause_btn.disabled = True
        self._started_at = None
        self._apply_urgency_feedback(False)

        t = self.app.theme_mgr.get_theme()
        labels = {
            "foco": t.get("focus_label", "Sessao de foco"),
            "pausa_curta": t.get("short_break_label", "Pausa curta"),
            "pausa_longa": t.get("long_break_label", "Pausa longa"),
        }
        self._session_label.value = labels.get(stype, stype)
        self._skip_btn.visible = stype in ("pausa_curta", "pausa_longa")

        self._update_display()
        try:
            self.app.page.update()
        except Exception:
            pass

    def _skip_break(self, e=None):
        if self._session_type in ("pausa_curta", "pausa_longa"):
            self._running = False
            self._set_type("foco")

    def _get_duration(self):
        return {
            "foco": self._focus_min,
            "pausa_curta": self._short_min,
            "pausa_longa": self._long_min,
        }.get(self._session_type, self._focus_min)

    def _load_durations(self):
        user = self.app.current_user
        if user:
            self._focus_min = user.get("pomodoro_focus", 25)
            self._short_min = user.get("pomodoro_short", 5)
            self._long_min = user.get("pomodoro_long", 15)

    def _update_display(self):
        m, s = divmod(self._seconds_left, 60)
        self._time_label.value = f"{m:02d}:{s:02d}"
        self._counter_label.value = f"Sessao {self._sessions_done}/4"

    def _apply_urgency_feedback(self, urgent: bool):
        t = self.app.theme_mgr.get_theme()
        if urgent and not self.app.reduce_motion:
            self._urgent_pulse = not self._urgent_pulse
            self._time_shell.scale = 1.03 if self._urgent_pulse else 1.0
            self._time_shell.opacity = 0.88 if self._urgent_pulse else 1.0
            self._progress_shell.scale = 1.01 if self._urgent_pulse else 1.0
            self._session_label.color = t["danger"]
            self._progress_bar.color = t["danger"]
            return

        self._urgent_pulse = False
        self._time_shell.scale = 1.0
        self._time_shell.opacity = 1.0
        self._progress_shell.scale = 1.0
        self._session_label.color = t["primary"]
        self._progress_bar.color = t["progress"]

    def _pick_task(self, e=None):
        tasks = self.db.get_tasks(user_id=self.app.get_user_id(), status="pendente")
        if not tasks:
            self.app.show_snackbar("Nenhuma tarefa pendente")
            return

        t = self.app.theme_mgr.get_theme()
        task_tiles = []
        for task in tasks:
            prio_icon = {"alta": "A", "média": "M", "baixa": "B"}.get(task["priority"], "-")
            task_tiles.append(
                ft.ListTile(
                    title=ft.Text(f"[{prio_icon}] {task['title']}", color=t["text"]),
                    subtitle=ft.Text(task.get("description", ""), color=t["text_sec"], size=11),
                    on_click=lambda _, tk=task: self._select_task(tk),
                )
            )

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=20,
                bgcolor=t["card"],
                content=ft.Column(
                    controls=[
                        ft.Text("Selecionar tarefa", size=18, weight=ft.FontWeight.BOLD, color=t["primary"]),
                        *task_tiles,
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
        )
        self.app.page.overlay.append(bs)
        bs.open = True
        self.app.page.update()

    def _select_task(self, task):
        self._selected_task = task
        self._task_label.value = f"Tarefa: {task['title']}"
        if self.app.page.overlay:
            self.app.page.overlay[-1].open = False
        self.app.page.update()
