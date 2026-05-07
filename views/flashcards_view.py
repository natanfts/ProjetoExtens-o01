import asyncio

import flet as ft

from views.ui_components import field_style, filled_button, primary_button, progress_track, secondary_button, soft_card


class FlashcardsView:
    """Flashcards com repeticao espacada (SM-2)."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._mode = "menu"  # menu | review | create | results
        self._menu_reveal_blocks: list[ft.Container] = []
        self._subject_reveal_blocks: list[ft.Container] = []
        self._menu_revealing = False
        self._cards = []
        self._card_index = 0
        self._showing_back = False
        self._review_results = {"total": 0, "easy": 0, "medium": 0, "hard": 0, "forgot": 0}
        self._card_shell = None
        self._pending_motion = 0
        self._preserve_mode = False
        self._swipe_dx = 0.0
        self._subject_opening = False
        self._button_action_running = False

    def on_show(self):
        if self._preserve_mode:
            self._preserve_mode = False
            return
        self._mode = "menu"

    def build(self):
        if self._mode == "review":
            return self._build_review()
        if self._mode == "create":
            return self._build_create()
        if self._mode == "results":
            return self._build_results()
        return self._build_menu()

    def _build_menu(self):
        t = self.app.theme_mgr.get_theme()
        uid = self.app.get_user_id()
        stats = self.db.get_flashcard_stats(uid)
        self._menu_reveal_blocks = []
        self._subject_reveal_blocks = []

        stat_cards = []
        for key, label, value in [
            ("T", "Total", str(stats["total"])),
            ("R", "Revisados", str(stats["reviewed"])),
            ("P", "Pendentes", str(stats["due"])),
        ]:
            stat_cards.append(
                ft.Container(
                    col={"xs": 4, "sm": 4, "md": 4},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Text(key, size=11, color=t["text_sec"]),
                                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=t["primary"]),
                                ft.Text(label, size=11, color=t["text_sec"]),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=3,
                        ),
                        bgcolor=t["card"],
                        radius=16,
                        padding=12,
                    ),
                )
            )

        due = stats["due"]
        review_text = f"Revisar agora ({due})" if due > 0 else "Tudo revisado"

        subjects = self.db.get_flashcard_subjects(uid)
        subject_tiles = []
        for subj in subjects:
            cards = self.db.get_flashcards(uid, subject=subj)
            tile = soft_card(
                t,
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(subj, size=14, weight=ft.FontWeight.BOLD, color=t["text"]),
                                ft.Text(f"{len(cards)} cards", size=11, color=t["text_sec"]),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=t["primary"]),
                    ]
                ),
                bgcolor=t["card"],
                radius=14,
                padding=12,
            )
            subject_tiles.append(self._subject_reveal(self._subject_tile(subj, tile)))

        if not subject_tiles:
            subject_tiles.append(
                self._subject_reveal(soft_card(
                    t,
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, color=t["text_sec"]),
                            ft.Text("Ainda nao existem materias de flashcards.", size=13, color=t["text_sec"]),
                        ]
                    ),
                    bgcolor=t["card"],
                    radius=14,
                    padding=12,
                ))
            )

        menu_controls = [
            ft.ResponsiveRow(stat_cards, spacing=8, run_spacing=8),
            filled_button(
                t,
                review_text,
                lambda _: self._start_review(),
                bgcolor=t["success"] if due > 0 else t.get("border_soft", t["card"]),
                color="#FFFFFF" if due > 0 else t["text_sec"],
                height=48,
            ),
            primary_button(
                t,
                "Criar novo flashcard",
                lambda _: self._show_create(),
                icon=ft.Icons.ADD_ROUNDED,
                height=44,
            ),
            secondary_button(
                t,
                "Ver todos",
                lambda _: self._show_browse(),
                icon=ft.Icons.LIBRARY_BOOKS_ROUNDED,
                height=40,
            ),
            ft.Text("Por materia", size=16, weight=ft.FontWeight.BOLD, color=t["primary"]),
        ]

        content = ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [self._menu_reveal(c) for c in menu_controls] + subject_tiles,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.app.page.run_task(self._animate_menu_reveal)
        return content

    def _start_review(self):
        uid = self.app.get_user_id()
        self._cards = self.db.get_flashcards_for_review(uid, limit=20)
        if not self._cards:
            self.app.show_snackbar("Nenhum flashcard para revisar agora")
            return
        self._card_index = 0
        self._showing_back = False
        self._pending_motion = 1
        self._review_results = {"total": 0, "easy": 0, "medium": 0, "hard": 0, "forgot": 0}
        self._mode = "review"
        self._preserve_mode = True
        self.app.show_view("flashcards")

    def _start_review_subject(self, subject):
        uid = self.app.get_user_id()
        self._cards = self.db.get_flashcards(uid, subject=subject)
        if not self._cards:
            self.app.show_snackbar("Nenhum flashcard nesta materia")
            return
        self._card_index = 0
        self._showing_back = False
        self._pending_motion = 1
        self._review_results = {"total": 0, "easy": 0, "medium": 0, "hard": 0, "forgot": 0}
        self._mode = "review"
        self._preserve_mode = True
        self.app.show_view("flashcards")

    def _subject_tile(self, subject: str, tile_control):
        shell = ft.Container(
            content=tile_control,
            scale=1.0,
            animate_scale=self.app.motion_ms(150),
            animate_offset=self.app.motion_ms(150),
            animate_opacity=self.app.motion_ms(150),
            offset=ft.Offset(0, 0),
            opacity=1.0,
        )
        shell.on_click = lambda _, s=subject, c=shell: self.app.page.run_task(self._open_subject_with_effect, s, c)
        return shell

    async def _open_subject_with_effect(self, subject: str, tile_shell: ft.Container):
        if self._subject_opening:
            return
        self._subject_opening = True
        try:
            if not self.app.reduce_motion and tile_shell:
                tile_shell.scale = 0.985
                tile_shell.offset = ft.Offset(0, 0.01)
                tile_shell.opacity = 0.9
                self.app.page.update()
                await asyncio.sleep(0.06)

                tile_shell.scale = 1.02
                tile_shell.offset = ft.Offset(0, -0.004)
                tile_shell.opacity = 1.0
                self.app.page.update()
                await asyncio.sleep(0.05)

            self._start_review_subject(subject)
        finally:
            self._subject_opening = False

    def _build_review(self):
        t = self.app.theme_mgr.get_theme()

        if self._card_index >= len(self._cards):
            self._mode = "results"
            return self._build_results()

        card = self._cards[self._card_index]
        progress = (self._card_index + 1) / len(self._cards) if self._cards else 0
        window_width = getattr(getattr(self.app.page, "window", None), "width", 0) or 0
        is_compact = window_width > 0 and window_width < 520
        card_height = 330 if is_compact else 300
        review_card_width = 760
        if window_width > 0:
            review_card_width = max(280, min(760, int(window_width - 72)))
        question_size = 18 if is_compact else 20
        answer_size = 17 if is_compact else 18

        if not self._showing_back:
            card_content = soft_card(
                t,
                ft.Column(
                    [
                        ft.Text("PERGUNTA", size=12, weight=ft.FontWeight.BOLD, color=t["accent"]),
                        ft.Container(
                            width=review_card_width - 52,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                card["front"],
                                size=question_size,
                                weight=ft.FontWeight.BOLD,
                                color=t["text"],
                                text_align=ft.TextAlign.CENTER,
                                no_wrap=False,
                            ),
                        ),
                        ft.Text("Toque para ver resposta", size=13, color=t["text_sec"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                bgcolor=t["card"],
                radius=24,
                height=card_height,
                padding=26,
                width=review_card_width,
            )
            quality_row = ft.Container(height=2)
        else:
            card_content = soft_card(
                t,
                ft.Column(
                    [
                        ft.Text("RESPOSTA", size=12, weight=ft.FontWeight.BOLD, color=t["success"]),
                        ft.Container(
                            width=review_card_width - 52,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(
                                card["back"],
                                size=answer_size,
                                color=t["text"],
                                text_align=ft.TextAlign.CENTER,
                                no_wrap=False,
                            ),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                bgcolor=t["card"],
                radius=24,
                height=card_height,
                padding=26,
                width=review_card_width,
            )
            quality_row = ft.Column(
                [
                    ft.Text("Como foi?", size=14, color=t["text_sec"], text_align=ft.TextAlign.CENTER),
                    ft.Row(
                        [
                            filled_button(t, "Esqueci", lambda _: self._rate(0), bgcolor=t["danger"], expand=True, height=40),
                            filled_button(t, "Dificil", lambda _: self._rate(3), bgcolor=t["warning"], color="#2E2A25", expand=True, height=40),
                            filled_button(t, "Bom", lambda _: self._rate(4), bgcolor=t["primary"], expand=True, height=40),
                            filled_button(t, "Facil", lambda _: self._rate(5), bgcolor=t["success"], expand=True, height=40),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=8,
            )

        self._card_shell = ft.Container(
            content=card_content,
            offset=ft.Offset(0.08 * self._pending_motion, 0),
            opacity=0.35 if self._pending_motion else 1.0,
            scale=0.99 if self._pending_motion else 1.0,
            animate_scale=self.app.motion_ms(220),
            animate_offset=self.app.motion_ms(220),
            animate_opacity=self.app.motion_ms(220),
        )

        if self._pending_motion:
            self.app.page.run_task(self._settle_card_animation)

        prev_btn = secondary_button(
            t,
            "Anterior",
            lambda _: None,
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            height=38,
        )
        prev_btn.disabled = self._card_index == 0 and not self._showing_back

        flip_label = "Ver resposta" if not self._showing_back else "Ver pergunta"
        flip_icon = ft.Icons.FLIP_ROUNDED

        next_btn = secondary_button(
            t,
            "Proximo",
            lambda _: None,
            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
            height=38,
        )
        next_btn.disabled = self._card_index == len(self._cards) - 1 and self._showing_back

        flip_btn = filled_button(
            t,
            flip_label,
            lambda _: None,
            icon=flip_icon,
            bgcolor=t["primary"],
            height=38,
        )

        self._wire_review_button(prev_btn, self._go_prev_card, -1)
        self._wire_review_button(flip_btn, self._flip_card, 1 if not self._showing_back else -1)
        self._wire_review_button(next_btn, self._go_next_card, 1)

        gesture_card = ft.GestureDetector(
            content=self._card_shell,
            on_tap=lambda _: self._flip_card(),
            on_horizontal_drag_start=self._on_card_drag_start,
            on_horizontal_drag_update=self._on_card_drag_update,
            on_horizontal_drag_end=self._on_card_drag_end,
        )
        review_card_row = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    col={"xs": 12, "sm": 11, "md": 10, "lg": 8},
                    content=gesture_card,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
            run_spacing=0,
        )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            secondary_button(t, "Voltar", lambda _: self._back_to_menu(), icon=ft.Icons.ARROW_BACK_ROUNDED, height=36),
                            ft.Text(f"Card {self._card_index + 1} de {len(self._cards)}", size=14, color=t["text_sec"]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    progress_track(t, progress, color=t["accent"], height=7),
                    ft.Text(f"{card.get('subject', '')} | {card.get('topic', '')}", size=13, color=t["text_sec"]),
                    review_card_row,
                    ft.Row(
                        [
                            prev_btn,
                            flip_btn,
                            next_btn,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    ft.Text(
                        "Atalhos: <-  ->  Espaco  1(esqueci)  2(dificil)  3(bom)  4(facil)",
                        size=11,
                        color=t["text_sec"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    quality_row,
                ],
                spacing=10,
            ),
        )

    def _wire_review_button(self, button_control, action, motion_hint: int = 0):
        button_control.on_click = (
            lambda _, btn=button_control, fn=action, motion=motion_hint: self.app.page.run_task(
                self._play_review_button_effect, btn, fn, motion
            )
        )

    async def _play_review_button_effect(self, button_control, action, motion_hint: int = 0):
        if self._button_action_running:
            return
        self._button_action_running = True
        try:
            if not self.app.reduce_motion:
                if button_control:
                    button_control.scale = 0.94
                if self._card_shell:
                    self._card_shell.scale = 0.995
                    self._card_shell.opacity = 0.92
                    if motion_hint:
                        self._card_shell.offset = ft.Offset(0.018 * motion_hint, 0)
                self.app.page.update()
                await asyncio.sleep(0.055)

                if button_control:
                    button_control.scale = 1.0
                if self._card_shell:
                    self._card_shell.scale = 1.0
                    self._card_shell.opacity = 1.0
                    self._card_shell.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.02)

            action()
        finally:
            self._button_action_running = False

    def _flip_card(self):
        self._showing_back = not self._showing_back
        self._refresh_review(1 if self._showing_back else -1)

    def _rate(self, quality):
        card = self._cards[self._card_index]
        uid = self.app.get_user_id()

        if uid:
            self.db.save_flashcard_review(card["id"], quality, user_id=uid)
            self.db.add_xp(uid, 5, "flashcard", "Revisao de flashcard")
            self.db.update_daily_goal_progress(uid, "xp", 5)

        self._review_results["total"] += 1
        if quality >= 5:
            self._review_results["easy"] += 1
        elif quality >= 4:
            self._review_results["medium"] += 1
        elif quality >= 3:
            self._review_results["hard"] += 1
        else:
            self._review_results["forgot"] += 1

        self._card_index += 1
        self._showing_back = False
        self._refresh_review(1)

    async def _settle_card_animation(self):
        await asyncio.sleep(0)
        if self._card_shell:
            self._card_shell.offset = ft.Offset(0, 0)
            self._card_shell.opacity = 1.0
            self._card_shell.scale = 1.0
            self._pending_motion = 0
            self.app.page.update()

    def _refresh_review(self, motion: int = 0):
        self._pending_motion = motion
        self._preserve_mode = True
        self.app.show_view("flashcards")

    def _go_prev_card(self):
        if self._showing_back:
            self._showing_back = False
            self._refresh_review(-1)
            return

        if self._card_index > 0:
            self._card_index -= 1
            self._showing_back = False
            self._refresh_review(-1)
            return

        self.app.show_snackbar("Voce ja esta no primeiro card.")

    def _go_next_card(self):
        if not self._showing_back:
            self._showing_back = True
            self._refresh_review(1)
            return

        if self._card_index < len(self._cards) - 1:
            self._card_index += 1
            self._showing_back = False
            self._refresh_review(1)
            return

        self.app.show_snackbar("Ultimo card da sequencia.")

    def _on_card_drag_start(self, e):
        self._swipe_dx = 0.0

    def _on_card_drag_update(self, e):
        dx = 0.0
        if hasattr(e, "delta_x") and e.delta_x is not None:
            dx = float(e.delta_x)
        elif hasattr(e, "primary_delta") and e.primary_delta is not None:
            dx = float(e.primary_delta)
        self._swipe_dx += dx
        if self._card_shell:
            self._card_shell.offset = ft.Offset(max(-0.16, min(0.16, self._swipe_dx / 480.0)), 0)
            self._card_shell.opacity = 0.95
            self.app.page.update()

    def _on_card_drag_end(self, e):
        velocity = 0.0
        if hasattr(e, "primary_velocity") and e.primary_velocity:
            velocity = float(e.primary_velocity)
        elif hasattr(e, "velocity_x") and e.velocity_x:
            velocity = float(e.velocity_x)

        threshold = 70
        if self._swipe_dx <= -threshold or velocity <= -350:
            self._go_next_card()
        elif self._swipe_dx >= threshold or velocity >= 350:
            self._go_prev_card()
        else:
            if self._card_shell:
                self._card_shell.offset = ft.Offset(0, 0)
                self._card_shell.opacity = 1.0
                self.app.page.update()
        self._swipe_dx = 0.0

    def handle_keyboard_event(self, e: ft.KeyboardEvent):
        if self._mode != "review":
            return False

        key = (e.key or "").lower()
        if key in {"arrow right", "arrowright", "right"}:
            self._go_next_card()
            return True
        if key in {"arrow left", "arrowleft", "left"}:
            self._go_prev_card()
            return True
        if key in {" ", "space"}:
            self._flip_card()
            return True

        if not self._showing_back:
            return False

        if key in {"1", "numpad1"}:
            self._rate(0)
            return True
        if key in {"2", "numpad2"}:
            self._rate(3)
            return True
        if key in {"3", "numpad3"}:
            self._rate(4)
            return True
        if key in {"4", "numpad4"}:
            self._rate(5)
            return True
        return False

    def _build_results(self):
        t = self.app.theme_mgr.get_theme()
        r = self._review_results

        uid = self.app.get_user_id()
        if uid:
            self.db.check_and_grant_achievements(uid)
            self.app.refresh_xp_sidebar()

        chips = [
            ("Facil", r["easy"], t["success"], "#FFFFFF"),
            ("Bom", r["medium"], t["primary"], "#FFFFFF"),
            ("Dificil", r["hard"], t["warning"], "#2E2A25"),
            ("Esqueci", r["forgot"], t["danger"], "#FFFFFF"),
        ]

        stat_controls = []
        for name, value, bg, fg in chips:
            stat_controls.append(
                ft.Container(
                    col={"xs": 6, "sm": 3, "md": 3},
                    content=soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=fg),
                                ft.Text(name, size=11, color=fg),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=2,
                        ),
                        bgcolor=bg,
                        radius=12,
                        padding=12,
                    ),
                )
            )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            alignment=ft.Alignment.CENTER,
            padding=24,
            content=soft_card(
                t,
                ft.Column(
                    [
                        ft.Text("Revisao concluida", size=24, weight=ft.FontWeight.BOLD, color=t["primary"]),
                        ft.Text(f"{r['total']} cards revisados", size=16, color=t["text"]),
                        ft.ResponsiveRow(stat_controls, spacing=8, run_spacing=8),
                        primary_button(t, "Voltar ao menu", lambda _: self._back_to_menu(), icon=ft.Icons.HOME_ROUNDED, width=240),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                bgcolor=t["card"],
                radius=24,
                padding=20,
                width=380,
            ),
        )

    def _show_create(self):
        self._mode = "create"
        self._preserve_mode = True
        self.app.show_view("flashcards")

    def _build_create(self):
        t = self.app.theme_mgr.get_theme()

        subject_f = ft.TextField(label="Materia", width=350, height=50, **field_style(t))
        topic_f = ft.TextField(label="Topico", width=350, height=50, **field_style(t))
        front_f = ft.TextField(label="Frente (pergunta)", width=350, height=90, multiline=True, **field_style(t))
        back_f = ft.TextField(label="Verso (resposta)", width=350, height=90, multiline=True, **field_style(t))

        def save(e):
            if not front_f.value or not back_f.value or not subject_f.value:
                self.app.show_snackbar("Preencha materia, frente e verso")
                return

            uid = self.app.get_user_id()
            self.db.create_flashcard(
                front_f.value.strip(),
                back_f.value.strip(),
                subject_f.value.strip(),
                topic_f.value.strip() if topic_f.value else "",
                "enem",
                "medio",
                uid,
            )
            self.app.show_snackbar("Flashcard criado")
            self._back_to_menu()

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
                    secondary_button(t, "Voltar", lambda _: self._back_to_menu(), icon=ft.Icons.ARROW_BACK_ROUNDED, height=36),
                    ft.Text("Novo flashcard", size=20, weight=ft.FontWeight.BOLD, color=t["primary"]),
                    subject_f,
                    topic_f,
                    front_f,
                    back_f,
                    primary_button(t, "Salvar", save, icon=ft.Icons.SAVE_ROUNDED, width=350, height=44),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _show_browse(self):
        t = self.app.theme_mgr.get_theme()
        uid = self.app.get_user_id()
        cards = self.db.get_flashcards(uid)

        tiles = []
        for card in cards[:60]:
            tiles.append(
                soft_card(
                    t,
                    ft.Column(
                        [
                            ft.Text(card["front"], size=14, weight=ft.FontWeight.BOLD, color=t["text"]),
                            ft.Text(card["back"], size=12, color=t["text_sec"]),
                            ft.Text(f"{card.get('subject', '')} | {card.get('difficulty', '')}", size=10, color=t["text_sec"]),
                        ],
                        spacing=4,
                    ),
                    bgcolor=t["card"],
                    radius=12,
                    padding=12,
                )
            )

        bs = ft.BottomSheet(
            content=ft.Container(
                height=520,
                padding=16,
                bgcolor=t["bg"],
                content=ft.Column(
                    [
                        ft.Text(f"Todos os flashcards ({len(cards)})", size=18, weight=ft.FontWeight.BOLD, color=t["primary"]),
                        *tiles,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=8,
                ),
            ),
        )
        self.app.page.overlay.append(bs)
        bs.open = True
        self.app.page.update()

    def _back_to_menu(self):
        self._mode = "menu"
        self._preserve_mode = True
        self.app.show_view("flashcards")

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
        if self.app.reduce_motion or self._menu_revealing:
            return
        if self.app._current_view_name != "flashcards" or self._mode != "menu":
            return
        self._menu_revealing = True
        try:
            await asyncio.sleep(0)
            for block in self._menu_reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.04)

            for block in self._subject_reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.032)
        finally:
            self._menu_revealing = False

    def _subject_reveal(self, control):
        shell = ft.Container(
            content=control,
            opacity=1.0 if self.app.reduce_motion else 0.0,
            offset=ft.Offset(0, 0) if self.app.reduce_motion else ft.Offset(0, 0.04),
            animate_opacity=self.app.motion_ms(220),
            animate_offset=self.app.motion_ms(220),
        )
        self._subject_reveal_blocks.append(shell)
        return shell

