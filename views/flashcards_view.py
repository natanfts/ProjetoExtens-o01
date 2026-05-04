import flet as ft

from views.ui_components import field_style, filled_button, primary_button, progress_track, secondary_button, soft_card


class FlashcardsView:
    """Flashcards com repeticao espacada (SM-2)."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._mode = "menu"  # menu | review | create | results
        self._cards = []
        self._card_index = 0
        self._showing_back = False
        self._review_results = {"total": 0, "easy": 0, "medium": 0, "hard": 0, "forgot": 0}

    def on_show(self):
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
            subject_tiles.append(
                soft_card(
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
                    on_click=lambda _, s=subj: self._start_review_subject(s),
                )
            )

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
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
                    *subject_tiles,
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    def _start_review(self):
        uid = self.app.get_user_id()
        self._cards = self.db.get_flashcards_for_review(uid, limit=20)
        if not self._cards:
            self.app.show_snackbar("Nenhum flashcard para revisar agora")
            return
        self._card_index = 0
        self._showing_back = False
        self._review_results = {"total": 0, "easy": 0, "medium": 0, "hard": 0, "forgot": 0}
        self._mode = "review"
        self.app.show_view("flashcards")

    def _start_review_subject(self, subject):
        uid = self.app.get_user_id()
        self._cards = self.db.get_flashcards(uid, subject=subject)
        if not self._cards:
            self.app.show_snackbar("Nenhum flashcard nesta materia")
            return
        self._card_index = 0
        self._showing_back = False
        self._review_results = {"total": 0, "easy": 0, "medium": 0, "hard": 0, "forgot": 0}
        self._mode = "review"
        self.app.show_view("flashcards")

    def _build_review(self):
        t = self.app.theme_mgr.get_theme()

        if self._card_index >= len(self._cards):
            self._mode = "results"
            return self._build_results()

        card = self._cards[self._card_index]
        progress = self._card_index / len(self._cards) if self._cards else 0

        if not self._showing_back:
            card_content = soft_card(
                t,
                ft.Column(
                    [
                        ft.Text("PERGUNTA", size=12, weight=ft.FontWeight.BOLD, color=t["accent"]),
                        ft.Text(card["front"], size=20, weight=ft.FontWeight.BOLD, color=t["text"], text_align=ft.TextAlign.CENTER),
                        ft.Text("Toque para ver resposta", size=13, color=t["text_sec"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                bgcolor=t["card"],
                radius=24,
                height=300,
                padding=26,
                on_click=lambda _: self._flip_card(),
            )
            quality_row = ft.Container()
        else:
            card_content = soft_card(
                t,
                ft.Column(
                    [
                        ft.Text("RESPOSTA", size=12, weight=ft.FontWeight.BOLD, color=t["success"]),
                        ft.Text(card["back"], size=18, color=t["text"], text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                bgcolor=t["card"],
                radius=24,
                height=300,
                padding=26,
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

        return ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            secondary_button(t, "Voltar", lambda _: self._back_to_menu(), icon=ft.Icons.ARROW_BACK_ROUNDED, height=36),
                            ft.Text(f"{self._card_index + 1}/{len(self._cards)}", size=14, color=t["text_sec"]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    progress_track(t, progress, color=t["accent"], height=7),
                    ft.Text(f"{card.get('subject', '')} | {card.get('topic', '')}", size=13, color=t["text_sec"]),
                    card_content,
                    quality_row,
                ],
                spacing=10,
            ),
        )

    def _flip_card(self):
        self._showing_back = True
        self.app.show_view("flashcards")

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
        self.app.show_view("flashcards")

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
                "médio",
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
        self.app.show_view("flashcards")
