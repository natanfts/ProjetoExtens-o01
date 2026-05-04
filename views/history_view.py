import csv
import os
from datetime import datetime

import flet as ft

from views.ui_components import filled_button, primary_button, secondary_button, soft_card


class HistoryView:
    """Historico com estatisticas e sessoes."""

    def __init__(self, app):
        self.app = app
        self.db = app.db

    def on_show(self):
        pass

    def build(self):
        t = self.app.theme_mgr.get_theme()
        uid = self.app.get_user_id()

        if not uid:
            return ft.Container(
                expand=True,
                bgcolor=t["bg"],
                alignment=ft.Alignment.CENTER,
                content=soft_card(
                    t,
                    ft.Column(
                        [
                            ft.Icon(ft.Icons.QUERY_STATS_ROUNDED, size=46, color=t["text_sec"]),
                            ft.Text("Faca login para ver seu historico", size=16, color=t["text_sec"]),
                            primary_button(t, "Entrar", lambda _: self.app.show_view("login"), icon=ft.Icons.LOGIN_ROUNDED),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    bgcolor=t["card"],
                    radius=24,
                    padding=24,
                    width=360,
                ),
            )

        stats = self.db.get_session_stats(uid)
        xp_info = self.db.get_xp_info(uid)

        stat_cards = []
        stat_data = [
            ("P", "Pomodoros", str(stats.get("focus_count", 0))),
            ("F", "Min. foco", str(stats.get("focus_minutes", 0))),
            ("D", "Dias ativos", str(stats.get("days_active", 0))),
            ("N", "Nivel", str(xp_info["level"])),
        ]
        for icon_text, label, value in stat_data:
            stat_cards.append(
                ft.Container(
                    col={"xs": 6, "sm": 6, "md": 3},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Text(icon_text, size=12, color=t["text_sec"]),
                                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=t["primary"]),
                                ft.Text(label, size=11, color=t["text_sec"]),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=3,
                        ),
                        bgcolor=t["card"],
                        radius=18,
                        padding=14,
                    ),
                )
            )

        study_stats = self.db.get_study_stats(uid)
        study_rows = []
        for s in study_stats:
            avg = s.get("avg_score", 0) or 0
            study_rows.append(
                soft_card(
                    t,
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(s["subject"], size=14, weight=ft.FontWeight.BOLD, color=t["text"]),
                                    ft.Text(
                                        f"{s['sessions']} sessoes | {s.get('total_correct', 0)}/{s.get('total_q', 0)} acertos",
                                        size=12,
                                        color=t["text_sec"],
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Text(
                                f"{avg:.0f}%",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=t["success"] if avg >= 70 else t["warning"],
                            ),
                        ]
                    ),
                    bgcolor=t["card"],
                    radius=14,
                    padding=12,
                )
            )

        sessions = self.db.get_sessions(uid, limit=20)
        session_tiles = []
        stype_labels = {"foco": "Foco", "pausa_curta": "Pausa", "pausa_longa": "Pausa longa"}
        for s in sessions:
            stype = stype_labels.get(s.get("session_type", ""), s.get("session_type", ""))
            completed = s.get("completed_at", "")
            time_str = ""
            if completed:
                try:
                    dt = datetime.fromisoformat(completed)
                    time_str = dt.strftime("%d/%m %H:%M")
                except (ValueError, TypeError):
                    time_str = completed[:16]

            task_title = s.get("task_title", "")
            task_text = f" | {task_title}" if task_title else ""

            session_tiles.append(
                soft_card(
                    t,
                    ft.Column(
                        [
                            ft.Text(f"{stype}{task_text}", size=13, color=t["text"]),
                            ft.Text(f"{s.get('duration', 0)} min | {time_str}", size=11, color=t["text_sec"]),
                        ],
                        spacing=2,
                    ),
                    bgcolor=t["card"],
                    radius=12,
                    padding=10,
                )
            )

        export_btn = secondary_button(
            t,
            "Exportar CSV",
            lambda _: self._export_csv(uid),
            icon=ft.Icons.DOWNLOAD_ROUNDED,
            width=170,
            height=40,
        )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
                    ft.ResponsiveRow(stat_cards, spacing=8, run_spacing=8),
                    ft.Text("Desempenho por materia", size=18, weight=ft.FontWeight.BOLD, color=t["primary"]),
                    *(study_rows if study_rows else [ft.Text("Nenhum quiz realizado ainda", size=14, color=t["text_sec"])]),
                    ft.Text("Sessoes recentes", size=18, weight=ft.FontWeight.BOLD, color=t["primary"]),
                    *(session_tiles if session_tiles else [ft.Text("Nenhuma sessao registrada", size=14, color=t["text_sec"])]),
                    ft.Container(height=6),
                    export_btn,
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _export_csv(self, uid):
        try:
            sessions = self.db.get_sessions(uid, limit=500)
            path = os.path.join(os.path.expanduser("~"), "switch_focus_export.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Tipo", "Duracao (min)", "Tarefa", "Data"])
                for s in sessions:
                    writer.writerow(
                        [
                            s.get("session_type", ""),
                            s.get("duration", 0),
                            s.get("task_title", ""),
                            s.get("completed_at", ""),
                        ]
                    )
            self.app.show_snackbar(f"Exportado: {path}")
        except Exception as e:
            self.app.show_snackbar(f"Erro ao exportar: {e}", bgcolor="#C45144")
