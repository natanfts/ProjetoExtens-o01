import flet as ft
from enem_editais import ENEM_EDITIONS, ENEM_STATS


class EnemEditaisView:
    """Editais do ENEM — Histórico completo de todas as edições e temas de redação."""

    def __init__(self, app):
        self.app = app
        self._mode = "list"        # list | detail
        self._selected_edition = None
        self._filter = "all"       # all | antigo | novo
        self._search_query = ""

    def on_show(self):
        pass

    def build(self):
        if self._mode == "detail" and self._selected_edition:
            return self._build_detail()
        return self._build_list()

    # ══════════════════════════════════════════════════════════
    # ── TELA PRINCIPAL: LISTA DE EDITAIS ─────────────────────
    # ══════════════════════════════════════════════════════════
    def _build_list(self):
        t = self.app.theme_mgr.get_theme()

        # Filtrar edições
        editions = list(ENEM_EDITIONS)
        if self._filter == "antigo":
            editions = [e for e in editions if e["year"] < 2009]
        elif self._filter == "novo":
            editions = [e for e in editions if e["year"] >= 2009]

        # Busca por texto
        if self._search_query.strip():
            q = self._search_query.lower().strip()
            editions = [
                e for e in editions
                if q in e["tema_redacao"].lower()
                or q in str(e["year"])
                or q in e.get("detalhes", "").lower()
            ]

        # Ordenar do mais recente ao mais antigo
        editions = sorted(editions, key=lambda e: e["year"], reverse=True)

        # ── Header com estatísticas ──────────────────────────
        stats_card = ft.Container(
            bgcolor=t["card"], border_radius=14, padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("📋 Editais do ENEM", size=18,
                            weight=ft.FontWeight.BOLD, color=t["text"]),
                    ft.Container(
                        bgcolor=t["primary"], border_radius=10,
                        padding=ft.padding.symmetric(
                            horizontal=10, vertical=4),
                        content=ft.Text(
                            f"{ENEM_STATS['total_editions']} edições",
                            size=12, color="#FFFFFF",
                            weight=ft.FontWeight.BOLD,
                        ),
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    self._stat_chip(t, "📅", "1998–2025"),
                    self._stat_chip(
                        t, "🏆", f"Recorde: {ENEM_STATS['record_inscritos']['count']} ({ENEM_STATS['record_inscritos']['year']})"),
                ], spacing=8, wrap=True),
                ft.Text(
                    "Histórico completo com todos os temas de redação",
                    size=12, color=t["text_sec"], italic=True,
                ),
            ], spacing=8),
        )

        # ── Filtros ──────────────────────────────────────────
        filter_btns = []
        for label, key in [("📚 Todos", "all"), ("📄 Antigo (98–08)", "antigo"), ("🆕 Novo (09–25)", "novo")]:
            is_active = self._filter == key
            filter_btns.append(
                ft.Container(
                    bgcolor=t["primary"] if is_active else t["secondary"],
                    border_radius=20,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    on_click=lambda _, k=key: self._set_filter(k),
                    ink=True,
                    content=ft.Text(
                        label, size=12,
                        color="#FFFFFF" if is_active else t["text_sec"],
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    ),
                )
            )

        filter_row = ft.Row(filter_btns, spacing=6, wrap=True)

        # ── Campo de busca ───────────────────────────────────
        search_field = ft.TextField(
            value=self._search_query,
            hint_text="🔍 Buscar por tema ou ano...",
            border_radius=12, bgcolor=t["card"],
            color=t["text"], height=45, text_size=14,
            prefix_icon=ft.Icons.SEARCH,
            on_submit=lambda e: self._do_search(e.control.value),
            on_change=lambda e: self._do_search(e.control.value),
        )

        # ── Cards de edições ─────────────────────────────────
        edition_cards = []
        for ed in editions:
            is_future = ed["year"] >= 2025
            is_new_enem = ed["year"] >= 2009

            # Cores por era
            if is_future:
                year_color = "#FF9800"
                year_icon = "🔮"
            elif is_new_enem:
                year_color = t["primary"]
                year_icon = "🆕"
            else:
                year_color = t["accent"]
                year_icon = "📄"

            # Tema resumido
            tema = ed["tema_redacao"]
            tema_display = tema if len(tema) <= 80 else tema[:77] + "..."

            edition_cards.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=12, padding=15,
                    on_click=lambda _, e=ed: self._open_detail(e),
                    ink=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                bgcolor=year_color, border_radius=10,
                                padding=ft.padding.symmetric(
                                    horizontal=10, vertical=5),
                                content=ft.Text(
                                    f"{year_icon} {ed['year']}", size=14,
                                    color="#FFFFFF", weight=ft.FontWeight.BOLD,
                                ),
                            ),
                            ft.Text(
                                ed["edition"], size=12, color=t["text_sec"],
                                expand=True, text_align=ft.TextAlign.RIGHT,
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=4),
                        ft.Row([
                            ft.Icon(ft.Icons.EDIT_NOTE,
                                    color=t["accent"], size=18),
                            ft.Text(
                                tema_display, size=13, color=t["text"],
                                expand=True,
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ], spacing=8),
                        ft.Row([
                            ft.Text(
                                f"📅 {ed['data_prova']}", size=11, color=t["text_sec"],
                            ),
                            ft.Text(
                                f"👥 {ed['inscritos']}", size=11, color=t["text_sec"],
                            ),
                        ], spacing=10, wrap=True),
                    ], spacing=4),
                )
            )

        if not edition_cards:
            edition_cards.append(
                ft.Container(
                    padding=40,
                    content=ft.Column([
                        ft.Text("🔍", size=40),
                        ft.Text("Nenhum resultado encontrado",
                                size=16, color=t["text_sec"]),
                        ft.Text("Tente outra busca", size=13,
                                color=t["text_sec"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                )
            )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=[
                    stats_card,
                    filter_row,
                    search_field,
                    ft.Text(
                        f"📝 {len(editions)} edição(ões)",
                        size=14, color=t["text_sec"],
                    ),
                    *edition_cards,
                    ft.Container(height=20),
                ],
                spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── TELA: DETALHE DE UMA EDIÇÃO ──────────────────────────
    # ══════════════════════════════════════════════════════════
    def _build_detail(self):
        t = self.app.theme_mgr.get_theme()
        ed = self._selected_edition
        is_new_enem = ed["year"] >= 2009

        sections = []

        # Voltar
        sections.append(
            ft.TextButton(
                "← Voltar aos Editais",
                on_click=lambda _: self._go_list(),
                style=ft.ButtonStyle(color=t["text_sec"]),
            )
        )

        # Cabeçalho
        year_color = t["primary"] if is_new_enem else t["accent"]
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            bgcolor=year_color, border_radius=12,
                            padding=ft.padding.symmetric(
                                horizontal=14, vertical=8),
                            content=ft.Text(
                                f"ENEM {ed['year']}", size=20,
                                color="#FFFFFF", weight=ft.FontWeight.BOLD,
                            ),
                        ),
                        ft.Container(
                            bgcolor=t["secondary"], border_radius=8,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=4),
                            content=ft.Text(
                                "Novo ENEM" if is_new_enem else "ENEM Antigo",
                                size=11, color=t["text_sec"],
                            ),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(ed["edition"], size=14, color=t["text_sec"]),
                ], spacing=8),
            )
        )

        # Tema da Redação (destaque)
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=20,
                border=ft.border.all(2, t["accent"]),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.EDIT_NOTE,
                                color=t["accent"], size=24),
                        ft.Text("📝 Tema da Redação", size=16,
                                weight=ft.FontWeight.BOLD, color=t["accent"]),
                    ], spacing=8),
                    ft.Container(height=4),
                    ft.Text(
                        ed["tema_redacao"], size=16, color=t["text"],
                        weight=ft.FontWeight.W_500, selectable=True,
                    ),
                ], spacing=4),
            )
        )

        # Informações da prova
        info_items = [
            ("📅", "Data da Prova", ed["data_prova"]),
            ("👥", "Inscritos", ed["inscritos"]),
            ("📊", "Nota Máx. Redação", ed["nota_maxima_redacao"]),
            ("📋", "Formato", "180 questões + redação (TRI)" if is_new_enem else "63 questões + redação"),
        ]
        info_rows = []
        for icon, label, value in info_items:
            info_rows.append(
                ft.Container(
                    bgcolor=t["bg"], border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    content=ft.Row([
                        ft.Text(f"{icon} {label}", size=13,
                                color=t["text_sec"], expand=True),
                        ft.Text(value, size=13, color=t["text"],
                                weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                    ]),
                )
            )
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=15,
                content=ft.Column([
                    ft.Text("📋 Informações", size=16,
                            weight=ft.FontWeight.BOLD, color=t["primary"]),
                    *info_rows,
                ], spacing=6),
            )
        )

        # Detalhes / Curiosidades
        if ed.get("detalhes"):
            sections.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=20,
                    content=ft.Column([
                        ft.Text("💡 Detalhes e Curiosidades", size=16,
                                weight=ft.FontWeight.BOLD, color=t["primary"]),
                        ft.Text(ed["detalhes"], size=14, color=t["text"],
                                selectable=True),
                    ], spacing=8),
                )
            )

        # Navegação entre edições
        all_years = [e["year"] for e in ENEM_EDITIONS]
        idx = all_years.index(ed["year"]) if ed["year"] in all_years else -1
        nav_btns = []
        if idx > 0:
            prev_ed = ENEM_EDITIONS[idx - 1]
            nav_btns.append(
                ft.TextButton(
                    f"← ENEM {prev_ed['year']}",
                    on_click=lambda _, e=prev_ed: self._open_detail(e),
                    style=ft.ButtonStyle(color=t["accent"]),
                )
            )
        if idx < len(all_years) - 1:
            next_ed = ENEM_EDITIONS[idx + 1]
            nav_btns.append(
                ft.TextButton(
                    f"ENEM {next_ed['year']} →",
                    on_click=lambda _, e=next_ed: self._open_detail(e),
                    style=ft.ButtonStyle(color=t["accent"]),
                )
            )
        if nav_btns:
            sections.append(
                ft.Container(
                    padding=ft.padding.only(top=5, bottom=20),
                    content=ft.Row(
                        nav_btns,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                )
            )

        # Botão pesquisar tema na teoria
        sections.append(
            ft.Container(
                padding=ft.padding.only(bottom=20),
                content=ft.ElevatedButton(
                    content=ft.Text(f"🔬 Pesquisar sobre este tema", size=13),
                    height=42, bgcolor=t["primary"], color="#FFFFFF",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda _: self._search_theme_in_theory(
                        ed["tema_redacao"]),
                ),
            )
        )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=sections,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── HELPERS UI ───────────────────────────────────────────
    # ══════════════════════════════════════════════════════════
    def _stat_chip(self, t, icon, text):
        return ft.Container(
            bgcolor=t["secondary"], border_radius=8,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            content=ft.Text(f"{icon} {text}", size=11, color=t["text_sec"]),
        )

    # ══════════════════════════════════════════════════════════
    # ── NAVEGAÇÃO ────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════
    def _open_detail(self, edition):
        self._selected_edition = edition
        self._mode = "detail"
        self.app.show_view("enem_editais")

    def _go_list(self):
        self._mode = "list"
        self.app.show_view("enem_editais")

    def _set_filter(self, f):
        self._filter = f
        self._mode = "list"
        self.app.show_view("enem_editais")

    def _do_search(self, query):
        self._search_query = query or ""
        self._mode = "list"
        self.app.show_view("enem_editais")

    def _search_theme_in_theory(self, tema):
        """Abre a view de teorias e pesquisa o tema da redação."""
        # Criar/obter theory view e configurar busca
        if "theory" not in self.app._views:
            self.app._views["theory"] = self.app._create_view("theory")
        theory = self.app._views["theory"]
        if theory and hasattr(theory, "_search_articles_api"):
            # Extrair palavras-chave do tema
            keywords = tema.split(":")
            search_term = keywords[0].strip() if keywords else tema
            # Limitar tamanho para busca efetiva
            if len(search_term) > 60:
                words = search_term.split()
                search_term = " ".join(words[:6])
            theory._search_articles_api(search_term)
        else:
            self.app.show_view("theory")
