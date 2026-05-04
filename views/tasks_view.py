from datetime import datetime

import flet as ft

from views.ui_components import field_style, filled_button, primary_button, secondary_button, soft_card


class TasksView:
    """Gerenciador de tarefas com estilo profissional."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._filter = "todas"

    def on_show(self):
        pass

    def build(self):
        t = self.app.theme_mgr.get_theme()
        self._theme = t

        filter_dd = ft.Dropdown(
            value="Todas",
            width=150,
            height=44,
            options=[ft.dropdown.Option(v) for v in ["Todas", "Pendentes", "Concluidas", "Alta", "Media", "Baixa"]],
            text_size=13,
            on_select=self._on_filter,
            **field_style(t),
        )

        add_btn = primary_button(
            t,
            "Nova tarefa",
            lambda _: self._open_add_dialog(),
            icon=ft.Icons.ADD_ROUNDED,
            width=170,
            height=44,
        )

        self._task_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self._load_tasks()

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
                    ft.Row([filter_dd, add_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self._task_list,
                ],
                expand=True,
                spacing=12,
            ),
        )

    def _load_tasks(self):
        t = self._theme
        self._task_list.controls.clear()

        status = None
        if self._filter == "pendentes":
            status = "pendente"
        elif self._filter == "concluidas":
            status = "concluída"

        tasks = self.db.get_tasks(user_id=self.app.get_user_id(), status=status)

        if self._filter in ("alta", "média", "baixa"):
            tasks = [tk for tk in tasks if tk.get("priority") == self._filter]
        elif self._filter == "media":
            tasks = [tk for tk in tasks if tk.get("priority") == "média"]

        if not tasks:
            self._task_list.controls.append(
                soft_card(
                    t,
                    ft.Container(
                        alignment=ft.Alignment.CENTER,
                        padding=24,
                        content=ft.Text(
                            "Nenhuma tarefa encontrada. Clique em 'Nova tarefa' para comecar.",
                            size=14,
                            color=t["text_sec"],
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                    bgcolor=t["card"],
                    radius=20,
                )
            )
            return

        for task in tasks:
            self._task_list.controls.append(self._render_task(task, t))

    def _render_task(self, task, t):
        done = task["status"] == "concluída"
        prio = {"alta": "A", "média": "M", "baixa": "B"}.get(task.get("priority"), "-")

        deadline_text = ""
        deadline = task.get("deadline")
        if deadline:
            try:
                dl = datetime.strptime(deadline, "%Y-%m-%d")
                days_left = (dl.date() - datetime.now().date()).days
                if days_left < 0:
                    deadline_text = f" | atrasada {abs(days_left)}d"
                elif days_left == 0:
                    deadline_text = " | vence hoje"
                elif days_left <= 3:
                    deadline_text = f" | {days_left}d"
                else:
                    deadline_text = f" | {dl.strftime('%d/%m')}"
            except ValueError:
                pass

        pom_text = f"P {task['pomodoros_done']}/{task['pomodoros_est']}"
        desc = (task.get("description") or "").strip()
        sub_text = f"{desc}  {pom_text}{deadline_text}".strip()

        return soft_card(
            t,
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.CHECK_CIRCLE_ROUNDED if done else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED,
                        icon_color=t["success"] if done else t["text_sec"],
                        icon_size=26,
                        on_click=lambda _, tid=task["id"], d=done: self._toggle_complete(tid, d),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"[{prio}] {task['title']}",
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=t["text_sec"] if done else t["text"],
                                style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH) if done else None,
                            ),
                            ft.Text(sub_text, size=12, color=t["text_sec"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_ROUNDED,
                        icon_color=t["primary"],
                        icon_size=20,
                        on_click=lambda _, tk=task: self._open_edit_dialog(tk),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE_ROUNDED,
                        icon_color=t["danger"],
                        icon_size=20,
                        on_click=lambda _, tid=task["id"]: self._delete(tid),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=t["card"],
            radius=18,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

    def _toggle_complete(self, task_id, currently_done):
        if currently_done:
            self.db.update_task(task_id, status="pendente", completed_at=None)
        else:
            self.db.complete_task(task_id)
            uid = self.app.get_user_id()
            if uid:
                self.db.add_xp(uid, 15, "task", "Tarefa concluida")
                self.db.update_daily_goal_progress(uid, "xp", 15)
                self.db.check_and_grant_achievements(uid)
                self.app.refresh_xp_sidebar()
        self._load_tasks()
        self.app.page.update()

    def _delete(self, task_id):
        self.app.show_confirm(
            "Confirmar",
            "Deseja excluir esta tarefa?",
            on_confirm=lambda: self._do_delete(task_id),
        )

    def _do_delete(self, task_id):
        self.db.delete_task(task_id)
        self._load_tasks()
        self.app.page.update()

    def _on_filter(self, e):
        self._filter = e.control.value.lower()
        self._load_tasks()
        self.app.page.update()

    def _open_add_dialog(self):
        self._task_dialog("Adicionar tarefa")

    def _open_edit_dialog(self, task):
        self._task_dialog("Editar tarefa", task)

    def _task_dialog(self, title, task=None):
        t = self._theme

        title_field = ft.TextField(
            label="Titulo da tarefa",
            width=340,
            height=50,
            value=task["title"] if task else "",
            **field_style(t),
        )
        desc_field = ft.TextField(
            label="Descricao (opcional)",
            width=340,
            height=50,
            value=task.get("description", "") if task else "",
            **field_style(t),
        )
        prio_dd = ft.Dropdown(
            label="Prioridade",
            width=340,
            height=52,
            value=task["priority"] if task else "média",
            options=[ft.dropdown.Option(v) for v in ["alta", "média", "baixa"]],
            **field_style(t),
        )
        pom_field = ft.TextField(
            label="Pomodoros estimados",
            width=340,
            height=50,
            value=str(task["pomodoros_est"]) if task else "1",
            keyboard_type=ft.KeyboardType.NUMBER,
            **field_style(t),
        )
        dl_field = ft.TextField(
            label="Prazo (dd/mm/aaaa)",
            width=340,
            height=50,
            value="",
            **field_style(t),
        )
        if task and task.get("deadline"):
            try:
                dl = datetime.strptime(task["deadline"], "%Y-%m-%d")
                dl_field.value = dl.strftime("%d/%m/%Y")
            except ValueError:
                pass

        def save(e):
            t_title = title_field.value.strip() if title_field.value else ""
            if not t_title:
                self.app.show_snackbar("Titulo e obrigatorio")
                return
            try:
                pom_val = int(pom_field.value)
            except (ValueError, TypeError):
                pom_val = 1

            deadline_val = None
            dl_text = dl_field.value.strip() if dl_field.value else ""
            if dl_text:
                try:
                    deadline_val = datetime.strptime(dl_text, "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    self.app.show_snackbar("Use formato dd/mm/aaaa")
                    return

            if task:
                self.db.update_task(
                    task["id"],
                    title=t_title,
                    description=desc_field.value.strip() if desc_field.value else "",
                    priority=prio_dd.value,
                    pomodoros_est=pom_val,
                    deadline=deadline_val,
                )
            else:
                self.db.create_task(
                    t_title,
                    desc_field.value.strip() if desc_field.value else "",
                    prio_dd.value,
                    pom_val,
                    user_id=self.app.get_user_id(),
                    deadline=deadline_val,
                )

            dlg.open = False
            self.app.page.update()
            self._load_tasks()
            self.app.page.update()

        def close(e):
            dlg.open = False
            self.app.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD, color=t["text"]),
            content=ft.Column([title_field, desc_field, prio_dd, pom_field, dl_field], tight=True, spacing=8),
            actions=[
                secondary_button(t, "Cancelar", close, height=40),
                filled_button(t, "Salvar", save, bgcolor=t["button"], height=40),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app.page.overlay.append(dlg)
        dlg.open = True
        self.app.page.update()
