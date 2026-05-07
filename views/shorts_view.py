import asyncio

import flet as ft

from views.ui_components import filled_button, secondary_button, soft_card


class ShortsView:
    """Videos educativos por materia."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._category = "enem"
        self._reveal_blocks: list[ft.Container] = []
        self._revealing = False

    def on_show(self):
        pass

    def _category_switch(self, t):
        controls = []
        for label, key in [("ENEM", "enem"), ("Concursos", "concursos")]:
            is_active = self._category == key
            if is_active:
                controls.append(filled_button(t, label, lambda _, c=key: self._set_category(c), bgcolor=t["primary"], expand=True, height=38))
            else:
                controls.append(secondary_button(t, label, lambda _, c=key: self._set_category(c), expand=True, height=38))
        return ft.Row(controls, spacing=8)

    def build(self):
        t = self.app.theme_mgr.get_theme()
        self._reveal_blocks = []

        subjects = self.db.get_subjects(self._category, "video")
        subject_sections = []

        for subj in subjects:
            videos = self.db.get_videos(self._category, subj)
            if not videos:
                continue

            video_cards = []
            for v in videos[:6]:
                video_cards.append(
                    soft_card(
                        t,
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.Icons.PLAY_CIRCLE_ROUNDED, color=t["primary"], size=34),
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    v.get("video_title", "Video")[:52],
                                                    size=13,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=t["text"],
                                                    max_lines=2,
                                                    overflow=ft.TextOverflow.ELLIPSIS,
                                                ),
                                                ft.Text(v.get("video_channel", ""), size=11, color=t["text_sec"]),
                                            ],
                                            spacing=2,
                                            expand=True,
                                        ),
                                    ]
                                ),
                                ft.Text(v.get("topic", ""), size=10, color=t["text_sec"]),
                            ],
                            spacing=6,
                        ),
                        bgcolor=t["card"],
                        radius=16,
                        width=300,
                        padding=12,
                        on_click=lambda _, url=v.get("video_url", ""): self._open_video(url),
                    )
                )

            subject_sections.append(
                ft.Column(
                    [
                        ft.Text(subj, size=16, weight=ft.FontWeight.BOLD, color=t["primary"]),
                        ft.Row(video_cards, scroll=ft.ScrollMode.AUTO, spacing=8),
                    ],
                    spacing=6,
                )
            )

        if not subject_sections:
            subject_sections.append(
                soft_card(
                    t,
                    ft.Column(
                        [
                            ft.Icon(ft.Icons.VIDEO_COLLECTION_ROUNDED, size=44, color=t["text_sec"]),
                            ft.Text("Nenhum video disponivel ainda", size=16, color=t["text_sec"]),
                            ft.Text("Os videos sao atualizados automaticamente", size=13, color=t["text_sec"]),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=t["card"],
                    radius=20,
                    padding=28,
                )
            )

        content = ft.Container(
            expand=True,
            bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            content=ft.Column(
                [self._reveal(c) for c in [self._category_switch(t), *subject_sections]],
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
        self.app.page.run_task(self._animate_reveal)
        return content

    def _set_category(self, cat):
        self._category = cat
        self.app.show_view("shorts")

    def _open_video(self, url):
        if url:
            import webbrowser

            webbrowser.open(url)

    def _reveal(self, control):
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
        if self.app._current_view_name != "shorts":
            return
        self._revealing = True
        try:
            await asyncio.sleep(0)
            for block in self._reveal_blocks:
                block.opacity = 1.0
                block.offset = ft.Offset(0, 0)
                self.app.page.update()
                await asyncio.sleep(0.04)
        finally:
            self._revealing = False
