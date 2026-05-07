import asyncio
import json

import flet as ft

from views.ui_components import field_style, filled_button, primary_button, progress_track, secondary_button, soft_card


class StudyView:
    """Central de estudos com quiz de questoes do banco."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._mode = "menu"
        self._questions = []
        self._q_index = 0
        self._correct = 0
        self._total = 0
        self._category = "enem"
        self._subject = None
        self._menu_reveal_blocks: list[ft.Container] = []
        self._revealing_menu = False
        self._menu_tile_opening = False
        self._quiz_answer_locked = False

    def on_show(self):
        pass

    def build(self):
        if self._mode == "quiz":
            return self._build_quiz()
        if self._mode == "results":
            return self._build_results()
        return self._build_menu()

    def _category_switch(self, t):
        controls = []
        for label, key in [("ENEM", "enem"), ("Concursos", "concursos")]:
            is_active = self._category == key
            if is_active:
                controls.append(filled_button(t, label, lambda _, c=key: self._set_category(c), bgcolor=t["primary"], expand=True, height=40))
            else:
                controls.append(secondary_button(t, label, lambda _, c=key: self._set_category(c), expand=True, height=40))
        return ft.Row(controls, spacing=8)

    def _build_menu(self):
        t = self.app.theme_mgr.get_theme()
        self._menu_reveal_blocks = []

        subjects = self.db.get_subjects(self._category, "quiz")
        subject_tiles = []
        for subj in subjects:
            topics = self.db.get_topics(self._category, subj, "quiz")
            topic_count = len(topics) if topics else 0
            subject_card = soft_card(
                t,
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(subj, size=15, weight=ft.FontWeight.BOLD, color=t["text"]),
                                ft.Text(f"{topic_count} topicos", size=12, color=t["text_sec"]),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED, color=t["primary"], size=30),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=t["card"],
                radius=18,
                padding=14,
            )
            subject_tiles.append(self._menu_click_tile(subject_card, lambda s=subj: self._start_quiz(s)))

        enem_section = []
        if self._category == "enem":
            cached_years = self.db.get_cached_enem_years()
            if cached_years:
                enem_section.append(ft.Text("ENEM real", size=17, weight=ft.FontWeight.BOLD, color=t["primary"]))
                for year in cached_years[:6]:
                    count = self.db.get_cached_enem_year_count(year)
                    enem_card = soft_card(
                        t,
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(f"ENEM {year}", size=15, weight=ft.FontWeight.BOLD, color=t["text"]),
                                        ft.Text(f"{count} questoes em cache", size=12, color=t["text_sec"]),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                                ft.Icon(ft.Icons.QUIZ_ROUNDED, color=t["accent"], size=28),
                            ]
                        ),
                        bgcolor=t["card"],
                        radius=18,
                        padding=14,
                    )
                    enem_section.append(self._menu_click_tile(enem_card, lambda y=year: self._start_enem_quiz(y)))

        theory_card = soft_card(
            t,
            ft.Row(
                [
                    ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=t["primary"], size=26),
                    ft.Column(
                        [
                            ft.Text("Teorias do ENEM", size=15, weight=ft.FontWeight.BOLD, color=t["text"]),
                            ft.Text("Resumos, formulas e conceitos", size=12, color=t["text_sec"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=t["text_sec"], size=16),
                ],
                spacing=10,
            ),
            bgcolor=t["card"],
            radius=18,
            padding=14,
        )
        theory_card = self._menu_click_tile(theory_card, lambda: self.app.show_view("theory"), motion=-1)

        editais_card = soft_card(
            t,
            ft.Row(
                [
                    ft.Icon(ft.Icons.DESCRIPTION_ROUNDED, color=t["accent"], size=26),
                    ft.Column(
                        [
                            ft.Text("Editais do ENEM", size=15, weight=ft.FontWeight.BOLD, color=t["text"]),
                            ft.Text("Historico completo e temas de redacao", size=12, color=t["text_sec"]),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=t["text_sec"], size=16),
                ],
                spacing=10,
            ),
            bgcolor=t["card"],
            radius=18,
            padding=14,
        )
        editais_card = self._menu_click_tile(editais_card, lambda: self.app.show_view("enem_editais"), motion=1)

        menu_controls = [
            self._category_switch(t),
            theory_card,
            editais_card,
            ft.Text(f"Materias - {self._category.upper()}", size=18, weight=ft.FontWeight.BOLD, color=t["primary"]),
            *subject_tiles,
            *enem_section,
        ]

        content = ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [self._menu_reveal(c) for c in menu_controls],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.app.page.run_task(self._animate_menu_reveal)
        return content

    def _menu_click_tile(self, control, action, motion: int = 0):
        shell = ft.Container(
            content=control,
            scale=1.0,
            opacity=1.0,
            offset=ft.Offset(0, 0),
            animate_scale=self.app.motion_ms(150),
            animate_offset=self.app.motion_ms(150),
            animate_opacity=self.app.motion_ms(150),
        )
        shell.on_click = lambda _, c=shell, fn=action, m=motion: self.app.page.run_task(
            self._animate_menu_tile_click,
            c,
            fn,
            m,
        )
        return shell

    async def _animate_menu_tile_click(self, shell: ft.Container, action, motion: int = 0):
        if self._menu_tile_opening:
            return
        self._menu_tile_opening = True
        try:
            if not self.app.reduce_motion and shell:
                shell.scale = 0.985
                shell.opacity = 0.9
                shell.offset = ft.Offset(0.012 * motion, 0.01)
                self.app.page.update()
                await asyncio.sleep(0.06)

                shell.scale = 1.02
                shell.opacity = 1.0
                shell.offset = ft.Offset(0.0, -0.004)
                self.app.page.update()
                await asyncio.sleep(0.05)

            action()
        finally:
            self._menu_tile_opening = False

    def _start_quiz(self, subject, e=None):
        self._subject = subject
        self._questions = self.db.get_questions(self._category, subject, limit=10)
        if not self._questions:
            self.app.show_snackbar("Nenhuma questao disponivel para essa materia")
            return
        self._q_index = 0
        self._correct = 0
        self._total = len(self._questions)
        self._quiz_answer_locked = False
        self._mode = "quiz"
        self.app.show_view("study")

    def _start_enem_quiz(self, year, e=None):
        self._subject = f"ENEM {year}"
        questions_raw = self.db.get_enem_questions(year, limit=10)
        if not questions_raw:
            self.app.show_snackbar("Nenhuma questao em cache para esse ano")
            return

        self._questions = []
        for q in questions_raw:
            opts = q["options"] if isinstance(q["options"], list) else json.loads(q["options"])
            self._questions.append(
                {
                    "question": q["question_text"],
                    "options": json.dumps(opts) if isinstance(opts, list) else q["options"],
                    "correct_answer": q["correct_answer"],
                    "explanation": q.get("context", ""),
                    "subject": q.get("discipline_name", ""),
                    "topic": "",
                }
            )

        self._q_index = 0
        self._correct = 0
        self._total = len(self._questions)
        self._quiz_answer_locked = False
        self._mode = "quiz"
        self.app.show_view("study")

    def _build_quiz(self):
        t = self.app.theme_mgr.get_theme()

        if self._q_index >= len(self._questions):
            self._mode = "results"
            return self._build_results()

        self._quiz_answer_locked = False
        q = self._questions[self._q_index]
        options = json.loads(q["options"]) if isinstance(q["options"], str) else q["options"]
        progress_val = (self._q_index + 1) / self._total if self._total > 0 else 0

        option_btns = []
        for idx, opt in enumerate(options):
            option_btns.append(self._quiz_option_tile(t, opt, idx))

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            secondary_button(t, "Voltar", lambda _: self._back_to_menu(), icon=ft.Icons.ARROW_BACK_ROUNDED, height=36),
                            ft.Text(f"{self._q_index + 1}/{self._total}", size=14, color=t["text_sec"]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    progress_track(t, progress_val, color=t["accent"], height=7),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 8},
                                content=ft.Text(
                                    q.get("subject", self._subject),
                                    size=13,
                                    color=t["text_sec"],
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=0,
                        run_spacing=0,
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            ft.Container(
                                col={"xs": 12, "sm": 11, "md": 10, "lg": 8},
                                content=soft_card(
                                    t,
                                    ft.Column(
                                        [
                                            ft.Text("Pergunta", size=12, color=t["primary"], weight=ft.FontWeight.BOLD),
                                            ft.Text(
                                                q["question"],
                                                size=20,
                                                color=t["text"],
                                                weight=ft.FontWeight.W_600,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ],
                                        spacing=10,
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    bgcolor=t["card"],
                                    radius=22,
                                    padding=24,
                                ),
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=0,
                        run_spacing=0,
                    ),
                    ft.Text("Escolha uma resposta", size=12, color=t["text_sec"], text_align=ft.TextAlign.CENTER),
                    ft.Column(
                        controls=option_btns,
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        tight=True,
                    ),
                ],
                spacing=9,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _quiz_option_tile(self, t: dict, option_text: str, index: int):
        letter = chr(65 + (index % 26))
        motion = -1 if index % 2 == 0 else 1
        option_card = soft_card(
            t,
            ft.Row(
                [
                    ft.Container(
                        width=26,
                        height=26,
                        border_radius=999,
                        bgcolor=t.get("surface_soft", t["bg"]),
                        border=ft.border.all(1, t.get("border_soft", t["entry_border"])),
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(letter, size=12, color=t["text_sec"], weight=ft.FontWeight.BOLD),
                    ),
                    ft.Text(
                        option_text,
                        size=15,
                        color=t["text"],
                        text_align=ft.TextAlign.LEFT,
                        expand=True,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=t["card"],
            radius=16,
            padding=ft.padding.symmetric(horizontal=14, vertical=13),
        )

        option_shell = ft.Container(
            col={"xs": 12, "sm": 11, "md": 10, "lg": 8},
            content=option_card,
            scale=1.0,
            opacity=1.0,
            offset=ft.Offset(0, 0),
            animate_scale=self.app.motion_ms(140),
            animate_offset=self.app.motion_ms(140),
            animate_opacity=self.app.motion_ms(140),
            on_hover=self._quiz_option_hover,
        )
        option_shell.on_click = lambda _, c=option_shell, ans=option_text, m=motion: self.app.page.run_task(
            self._animate_quiz_option_click,
            c,
            ans,
            m,
        )
        return ft.ResponsiveRow(
            controls=[option_shell],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
            run_spacing=0,
        )

    def _quiz_option_hover(self, e):
        if self.app.reduce_motion:
            return
        entering = str(getattr(e, "data", "")).lower() == "true"
        e.control.scale = 1.01 if entering else 1.0
        e.control.update()

    async def _animate_quiz_option_click(self, option_shell: ft.Container, chosen: str, motion: int):
        if self._quiz_answer_locked:
            return
        self._quiz_answer_locked = True
        try:
            if not self.app.reduce_motion and option_shell:
                option_shell.scale = 0.982
                option_shell.opacity = 0.9
                option_shell.offset = ft.Offset(0.018 * motion, 0)
                self.app.page.update()
                await asyncio.sleep(0.06)

                option_shell.scale = 1.02
                option_shell.opacity = 1.0
                option_shell.offset = ft.Offset(0, -0.004)
                self.app.page.update()
                await asyncio.sleep(0.05)

            self._answer(chosen)
        except Exception:
            self._quiz_answer_locked = False
            raise

    def _answer(self, chosen):
        q = self._questions[self._q_index]
        correct = q["correct_answer"]
        is_correct = chosen.strip() == correct.strip()

        if is_correct:
            self._correct += 1
            self.app.show_snackbar("Correto", bgcolor="#1F8A70")
        else:
            self.app.show_snackbar(f"Resposta correta: {correct}", bgcolor="#C45144")

        uid = self.app.get_user_id()
        if uid:
            xp = 10 if is_correct else 3
            self.db.add_xp(uid, xp, "quiz", f"Quiz: {self._subject}")
            self.db.update_daily_goal_progress(uid, "quiz")
            self.db.update_daily_goal_progress(uid, "xp", xp)

        self._q_index += 1

        async def _next():
            await asyncio.sleep(0.5)
            self.app.show_view("study")

        self.app.page.run_task(_next)

    def _build_results(self):
        t = self.app.theme_mgr.get_theme()
        score = (self._correct / self._total * 100) if self._total > 0 else 0

        uid = self.app.get_user_id()
        if uid and self._total > 0:
            self.db.save_study_progress(
                self._subject or "",
                "",
                "quiz",
                score,
                self._total,
                self._correct,
                self._category,
                uid,
            )
            self.db.check_and_grant_achievements(uid)
            self.app.refresh_xp_sidebar()

        tone = t["success"] if score >= 70 else t["warning"]
        badge = "Excelente" if score >= 80 else "Bom" if score >= 50 else "Continue"

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            alignment=ft.Alignment.CENTER,
            padding=24,
            content=soft_card(
                t,
                ft.Column(
                    [
                        ft.Text("Resultado do quiz", size=24, weight=ft.FontWeight.BOLD, color=t["primary"]),
                        ft.Text(self._subject or "", size=13, color=t["text_sec"]),
                        ft.Text(f"{score:.0f}%", size=50, weight=ft.FontWeight.BOLD, color=tone),
                        ft.Text(f"{self._correct}/{self._total} corretas", size=15, color=t["text"]),
                        ft.Text(badge, size=12, color=t["text_sec"]),
                        ft.Row(
                            [
                                primary_button(t, "Tentar novamente", lambda _: self._retry(), icon=ft.Icons.REPLAY_ROUNDED, expand=True),
                                secondary_button(t, "Voltar ao menu", lambda _: self._back_to_menu(), icon=ft.Icons.HOME_ROUNDED, expand=True),
                            ],
                            spacing=8,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                bgcolor=t["card"],
                radius=26,
                padding=22,
                width=380,
            ),
        )

    def _retry(self):
        if self._subject and self._subject.startswith("ENEM "):
            try:
                year = int(self._subject.split()[-1])
                self._start_enem_quiz(year)
                return
            except ValueError:
                pass
        if self._subject:
            self._start_quiz(self._subject)

    def _back_to_menu(self):
        self._mode = "menu"
        self.app.show_view("study")

    def _set_category(self, cat):
        self._category = cat
        self.app.show_view("study")

    def _menu_reveal(self, control):
        shell = ft.Container(
            content=control,
            opacity=1.0 if self.app.reduce_motion else 0.0,
            offset=ft.Offset(0, 0) if self.app.reduce_motion else ft.Offset(0, 0.032),
            animate_opacity=self.app.motion_ms(220),
            animate_offset=self.app.motion_ms(220),
        )
        self._menu_reveal_blocks.append(shell)
        return shell

    async def _animate_menu_reveal(self):
        if self.app.reduce_motion or self._revealing_menu:
            return
        if self.app._current_view_name != "study" or self._mode != "menu":
            return
        self._revealing_menu = True
        try:
            await asyncio.sleep(0)
            for block in self._menu_reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.042)
        finally:
            self._revealing_menu = False
