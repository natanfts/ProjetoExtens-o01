import flet as ft
import asyncio
import threading
import urllib.parse
import requests
from enem_syllabus import ENEM_SYLLABUS

# ── Wikipedia API helper ─────────────────────────────────────
_WIKI_HEADERS = {"User-Agent": "SwitchFocusApp/1.0 (estudos ENEM)"}
_WIKI_API = "https://pt.wikipedia.org/w/api.php"


def _wiki_search(query: str, limit: int = 6) -> list[dict]:
    """Busca artigos na Wikipedia e retorna título + resumo de cada um."""
    results = []
    try:
        # 1) Buscar títulos
        r = requests.get(_WIKI_API, params={
            "action": "opensearch", "format": "json",
            "search": query, "limit": str(limit),
        }, headers=_WIKI_HEADERS, timeout=8)
        data = r.json()
        titles = data[1] if len(data) > 1 else []
        urls = data[3] if len(data) > 3 else []
        if not titles:
            return []

        # 2) Buscar extracts de todos os títulos de uma vez
        r2 = requests.get(_WIKI_API, params={
            "action": "query", "format": "json",
            "prop": "extracts", "exintro": "1", "explaintext": "1",
            "titles": "|".join(titles[:limit]),
        }, headers=_WIKI_HEADERS, timeout=10)
        pages = r2.json().get("query", {}).get("pages", {})

        # Mapear title → extract
        extract_map = {}
        for page in pages.values():
            if page.get("extract"):
                extract_map[page["title"]] = page["extract"]

        for i, title in enumerate(titles):
            results.append({
                "title": title,
                "extract": extract_map.get(title, "Resumo não disponível."),
                "url": urls[i] if i < len(urls) else "",
            })
    except Exception:
        pass
    return results


def _wiki_article(title: str) -> dict | None:
    """Busca artigo completo da Wikipedia por título."""
    try:
        r = requests.get(_WIKI_API, params={
            "action": "query", "format": "json",
            "prop": "extracts", "explaintext": "1",
            "titles": title,
        }, headers=_WIKI_HEADERS, timeout=10)
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            if page.get("extract"):
                return {
                    "title": page["title"],
                    "content": page["extract"],
                    "url": f"https://pt.wikipedia.org/wiki/{urllib.parse.quote(page['title'])}",
                }
    except Exception:
        pass
    return None


class TheoryView:
    """Teorias ENEM — Leitura, resumos, fórmulas e pesquisa de artigos via API."""

    def __init__(self, app):
        self.app = app
        self.db = app.db
        self._mode = "areas"  # areas | topics | detail | search | articles | reading
        self._current_area = None
        self._current_topic = None
        self._search_query = ""
        self._notes_field = None
        # Artigos
        self._article_results = []
        self._article_query = ""
        self._current_article = None
        self._loading = False

    def on_show(self):
        pass  # Preservar estado da navegação

    def build(self):
        if self._mode == "topics":
            return self._build_topics()
        elif self._mode == "detail":
            return self._build_detail()
        elif self._mode == "search":
            return self._build_search_results()
        elif self._mode == "articles":
            return self._build_article_results()
        elif self._mode == "reading":
            return self._build_reading()
        return self._build_areas()

    # ══════════════════════════════════════════════════════════
    # ── TELA: ÁREAS DE CONHECIMENTO ──────────────────────────
    # ══════════════════════════════════════════════════════════
    def _build_areas(self):
        t = self.app.theme_mgr.get_theme()
        uid = self.app.get_user_id()
        progress = self.db.get_theory_progress(uid) if uid else {}
        stats = self.db.get_theory_stats(uid) if uid else {}

        # Total de progresso
        total_topics = sum(len(a["topics"]) for a in ENEM_SYLLABUS.values())
        total_completed = sum(1 for p in progress.values() if p["completed"])
        progress_pct = total_completed / total_topics if total_topics else 0

        # Campo de busca
        search_field = ft.TextField(
            hint_text="🔍 Buscar tópico...",
            border_radius=12, bgcolor=t["card"],
            color=t["text"], height=45, text_size=14,
            prefix_icon=ft.Icons.SEARCH,
            on_submit=lambda e: self._search(e.control.value),
        )

        # Card de progresso geral
        progress_card = ft.Container(
            bgcolor=t["card"], border_radius=14, padding=20,
            content=ft.Column([
                ft.Row([
                    ft.Text("📊 Progresso Geral", size=16,
                            weight=ft.FontWeight.BOLD, color=t["text"]),
                    ft.Text(f"{total_completed}/{total_topics}", size=14,
                            color=t["accent"], weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=progress_pct, height=8, color=t["accent"],
                               bgcolor=t["secondary"], border_radius=4),
                ft.Text(
                    f"{progress_pct*100:.0f}% concluído • {len(progress)} tópicos lidos",
                    size=12, color=t["text_sec"],
                ),
            ], spacing=8),
        )

        # Cards de áreas
        area_tiles = []
        for area_name, area_data in ENEM_SYLLABUS.items():
            topic_count = len(area_data["topics"])
            area_stats = stats.get(area_name, {"read": 0, "completed": 0})
            done = area_stats.get("completed", 0)
            pct = done / topic_count if topic_count else 0

            area_tiles.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=15,
                    on_click=lambda _, a=area_name: self._open_area(a),
                    ink=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(
                                f"{area_data['emoji']} {area_name}",
                                size=16, weight=ft.FontWeight.BOLD, color=t["text"],
                            ),
                            ft.Container(
                                bgcolor=t["primary"] if pct >= 1 else t["secondary"],
                                border_radius=10,
                                padding=ft.padding.symmetric(
                                    horizontal=8, vertical=3),
                                content=ft.Text(
                                    f"{done}/{topic_count}", size=11,
                                    color="#FFFFFF" if pct >= 1 else t["text_sec"],
                                ),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(
                            area_data["description"], size=12, color=t["text_sec"],
                            max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.ProgressBar(value=pct, height=4, color=t["accent"],
                                       bgcolor=t["secondary"], border_radius=2),
                    ], spacing=6),
                )
            )

        # Card de pesquisa de artigos via API
        article_field = ft.TextField(
            hint_text="Ex: Revolução Industrial, Fotossíntese...",
            border_radius=10, bgcolor=t["bg"],
            color=t["text"], height=42, text_size=13,
            on_submit=lambda e: self._search_articles_api(e.control.value),
        )
        research_card = ft.Container(
            bgcolor=t["card"], border_radius=14, padding=15,
            content=ft.Column([
                ft.Text("🔬 Pesquisar Artigos", size=16,
                        weight=ft.FontWeight.BOLD, color=t["text"]),
                ft.Text(
                    "Busque artigos da Wikipedia sobre temas do ENEM",
                    size=12, color=t["text_sec"],
                ),
                ft.Row([
                    ft.Container(expand=True, content=article_field),
                    ft.IconButton(
                        ft.Icons.SEARCH, icon_color=t["primary"],
                        icon_size=24, tooltip="Pesquisar",
                        on_click=lambda _: self._search_articles_api(
                            article_field.value),
                    ),
                ], spacing=5),
                ft.Text(
                    "🌐 Artigos trazidos diretamente da Wikipedia",
                    size=11, color=t["text_sec"], italic=True,
                ),
            ], spacing=8),
        )

        # Sugestões rápidas de pesquisa
        quick_searches = [
            "Revolução Industrial", "Fotossíntese", "Lei de Newton",
            "Globalização", "Genética", "Matemática Financeira",
        ]
        quick_chips = []
        for qs in quick_searches:
            quick_chips.append(
                ft.Container(
                    bgcolor=t["secondary"], border_radius=20,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    on_click=lambda _, q=qs: self._search_articles_api(q),
                    ink=True,
                    content=ft.Text(qs, size=11, color=t["accent"]),
                )
            )
        suggestions_card = ft.Container(
            bgcolor=t["card"], border_radius=14, padding=15,
            content=ft.Column([
                ft.Text("⚡ Sugestões de Pesquisa", size=14,
                        weight=ft.FontWeight.BOLD, color=t["text"]),
                ft.Row(quick_chips, spacing=6, wrap=True),
            ], spacing=8),
        )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=[
                    search_field,
                    progress_card,
                    ft.Text("📚 Áreas de Conhecimento", size=18,
                            weight=ft.FontWeight.BOLD, color=t["primary"]),
                    *area_tiles,
                    ft.Container(height=10),
                    research_card,
                    suggestions_card,
                    ft.Container(height=20),
                ],
                spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── TELA: TÓPICOS DE UMA ÁREA ────────────────────────────
    # ══════════════════════════════════════════════════════════
    def _build_topics(self):
        t = self.app.theme_mgr.get_theme()
        area_data = ENEM_SYLLABUS.get(self._current_area, {})
        topics = area_data.get("topics", [])
        uid = self.app.get_user_id()
        progress = self.db.get_theory_progress(uid) if uid else {}

        completed_count = sum(
            1 for tp in topics
            if progress.get((self._current_area, tp["title"]), {}).get("completed")
        )
        pct = completed_count / len(topics) if topics else 0

        # Cabeçalho com progresso
        header = ft.Container(
            bgcolor=t["card"], border_radius=14, padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        f"{area_data.get('emoji', '📚')} {self._current_area}",
                        size=18, weight=ft.FontWeight.BOLD, color=t["text"],
                    ),
                    ft.Text(f"{completed_count}/{len(topics)}", size=14,
                            color=t["accent"], weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=pct, height=6, color=t["accent"],
                               bgcolor=t["secondary"], border_radius=3),
                ft.Text(
                    area_data.get("description", ""), size=12,
                    color=t["text_sec"], max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ], spacing=6),
        )

        # Lista de tópicos
        topic_tiles = []
        diff_colors = {"fácil": "#4CAF50",
                       "médio": "#FF9800", "difícil": "#F44336"}

        for topic in topics:
            key = (self._current_area, topic["title"])
            is_read = key in progress
            is_completed = progress.get(key, {}).get("completed", False)
            diff = topic.get("difficulty", "médio")
            status_icon = "✅" if is_completed else "📖" if is_read else "📄"

            info_parts = []
            kc = topic.get("key_concepts", [])
            fm = topic.get("formulas", [])
            if kc:
                info_parts.append(f"{len(kc)} conceitos")
            if fm:
                info_parts.append(f"{len(fm)} fórmulas")
            info_text = " • ".join(info_parts) if info_parts else ""

            topic_tiles.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=12, padding=15,
                    on_click=lambda _, tp=topic: self._open_topic(tp),
                    ink=True,
                    content=ft.Row([
                        ft.Text(status_icon, size=22),
                        ft.Column([
                            ft.Text(
                                topic["title"], size=14,
                                weight=ft.FontWeight.BOLD, color=t["text"],
                            ),
                            ft.Row([
                                ft.Container(
                                    bgcolor=diff_colors.get(diff, "#FF9800"),
                                    border_radius=6,
                                    padding=ft.padding.symmetric(
                                        horizontal=6, vertical=2),
                                    content=ft.Text(
                                        diff, size=10, color="#FFFFFF"),
                                ),
                                ft.Text(info_text, size=11,
                                        color=t["text_sec"])
                                if info_text else ft.Container(),
                            ], spacing=5),
                        ], spacing=3, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT,
                                color=t["text_sec"], size=20),
                    ], spacing=10),
                )
            )

        # Botão voltar
        back_row = ft.TextButton(
            "← Voltar às Áreas",
            on_click=lambda _: self._go_areas(),
            style=ft.ButtonStyle(color=t["text_sec"]),
        )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=[
                    back_row,
                    header,
                    ft.Container(height=5),
                    *topic_tiles,
                    ft.Container(height=20),
                ],
                spacing=8, scroll=ft.ScrollMode.AUTO,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── TELA: DETALHE DE UM TÓPICO ───────────────────────────
    # ══════════════════════════════════════════════════════════
    def _build_detail(self):
        t = self.app.theme_mgr.get_theme()
        topic = self._current_topic
        if not topic:
            self._mode = "areas"
            return self.build()

        uid = self.app.get_user_id()
        progress = self.db.get_theory_progress(uid) if uid else {}
        key = (self._current_area, topic["title"])
        is_completed = progress.get(key, {}).get("completed", False)
        saved_notes = progress.get(key, {}).get("notes", "")

        diff = topic.get("difficulty", "médio")
        diff_colors = {"fácil": "#4CAF50",
                       "médio": "#FF9800", "difícil": "#F44336"}
        sections = []

        # Botão voltar
        sections.append(
            ft.TextButton(
                f"← Voltar — {self._current_area}",
                on_click=lambda _: self._go_topics(),
                style=ft.ButtonStyle(color=t["text_sec"]),
            )
        )

        # Título + dificuldade
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            topic["title"], size=20,
                            weight=ft.FontWeight.BOLD, color=t["text"],
                            expand=True,
                        ),
                        ft.Container(
                            bgcolor=diff_colors.get(diff, "#FF9800"),
                            border_radius=8,
                            padding=ft.padding.symmetric(
                                horizontal=8, vertical=4),
                            content=ft.Text(diff, size=11, color="#FFFFFF"),
                        ),
                    ]),
                    ft.Text(f"📚 {self._current_area}",
                            size=13, color=t["text_sec"]),
                ], spacing=6),
            )
        )

        # Resumo teórico
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=20,
                content=ft.Column([
                    ft.Text("📝 Resumo Teórico", size=16,
                            weight=ft.FontWeight.BOLD, color=t["primary"]),
                    ft.Text(topic["summary"], size=14, color=t["text"],
                            selectable=True),
                ], spacing=8),
            )
        )

        # Conceitos-chave
        if topic.get("key_concepts"):
            concept_items = []
            for concept in topic["key_concepts"]:
                concept_items.append(
                    ft.Container(
                        bgcolor=t["secondary"], border_radius=8,
                        padding=ft.padding.symmetric(
                            horizontal=10, vertical=6),
                        content=ft.Text(
                            f"💡 {concept}", size=12, color=t["text"]),
                    )
                )
            sections.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=20,
                    content=ft.Column([
                        ft.Text("🎯 Conceitos-Chave", size=16,
                                weight=ft.FontWeight.BOLD, color=t["primary"]),
                        ft.Column(concept_items, spacing=5),
                    ], spacing=8),
                )
            )

        # Fórmulas
        if topic.get("formulas"):
            formula_items = []
            for formula in topic["formulas"]:
                formula_items.append(
                    ft.Container(
                        bgcolor=t["bg"], border_radius=8,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=8),
                        content=ft.Text(
                            f"📐 {formula}", size=13, color=t["accent"],
                            weight=ft.FontWeight.W_500, selectable=True,
                        ),
                    )
                )
            sections.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=20,
                    content=ft.Column([
                        ft.Text("📐 Fórmulas", size=16,
                                weight=ft.FontWeight.BOLD, color=t["primary"]),
                        *formula_items,
                    ], spacing=8),
                )
            )

        # Dicas para o ENEM
        if topic.get("tips"):
            tip_items = []
            for tip in topic["tips"]:
                tip_items.append(
                    ft.Container(
                        bgcolor=t["bg"], border_radius=8,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=8),
                        content=ft.Text(f"⚡ {tip}", size=13, color=t["text"]),
                    )
                )
            sections.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=20,
                    content=ft.Column([
                        ft.Text("💡 Dicas para o ENEM", size=16,
                                weight=ft.FontWeight.BOLD, color=t["primary"]),
                        *tip_items,
                    ], spacing=6),
                )
            )

        # Tópicos relacionados
        if topic.get("related_topics"):
            related_chips = []
            for rel in topic["related_topics"]:
                related_chips.append(
                    ft.Container(
                        bgcolor=t["secondary"], border_radius=20,
                        padding=ft.padding.symmetric(
                            horizontal=12, vertical=6),
                        on_click=lambda _, r=rel: self._find_related(r),
                        ink=True,
                        content=ft.Text(
                            f"🔗 {rel}", size=12, color=t["accent"]),
                    )
                )
            sections.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=15,
                    content=ft.Column([
                        ft.Text("🔗 Tópicos Relacionados", size=14,
                                weight=ft.FontWeight.BOLD, color=t["text"]),
                        ft.Row(related_chips, spacing=8, wrap=True),
                    ], spacing=8),
                )
            )

        # Pesquisar mais sobre o tópico (via API)
        wiki_query = topic.get("wiki_query", topic["title"])
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=15,
                content=ft.Column([
                    ft.Text("🔬 Aprofundar Conhecimento", size=14,
                            weight=ft.FontWeight.BOLD, color=t["text"]),
                    ft.Text(
                        "Busque artigos sobre este tópico:",
                        size=12, color=t["text_sec"],
                    ),
                    ft.ElevatedButton(
                        content=ft.Text(
                            f"📚 Pesquisar \"{wiki_query}\"", size=13),
                        height=40, bgcolor=t["primary"], color="#FFFFFF",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=lambda _, q=wiki_query: self._search_articles_api(
                            q),
                    ),
                ], spacing=8),
            )
        )

        # Anotações pessoais
        self._notes_field = ft.TextField(
            value=saved_notes or "",
            hint_text="Suas anotações sobre este tópico...",
            multiline=True, min_lines=3, max_lines=6,
            bgcolor=t["bg"], color=t["text"], border_radius=10,
            text_size=13,
        )
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=15,
                content=ft.Column([
                    ft.Text("📝 Anotações", size=14,
                            weight=ft.FontWeight.BOLD, color=t["text"]),
                    self._notes_field,
                ], spacing=8),
            )
        )

        # Botão marcar como lido
        btn_text = "✅ Concluído" if is_completed else "📖 Marcar como Lido"
        btn_color = "#4CAF50" if is_completed else t["primary"]
        sections.append(
            ft.Container(
                padding=ft.padding.only(top=5, bottom=20),
                content=ft.ElevatedButton(
                    content=ft.Text(btn_text, size=15,
                                    weight=ft.FontWeight.BOLD),
                    height=50, width=300,
                    bgcolor=btn_color, color="#FFFFFF",
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=12)),
                    on_click=lambda _: self._mark_read(),
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
    # ── TELA: RESULTADOS DE BUSCA (tópicos internos) ─────────
    # ══════════════════════════════════════════════════════════
    def _build_search_results(self):
        t = self.app.theme_mgr.get_theme()
        query = self._search_query.lower().strip()

        results = []
        for area_name, area_data in ENEM_SYLLABUS.items():
            for topic in area_data["topics"]:
                searchable = (
                    f"{topic['title']} {topic['summary']} "
                    f"{' '.join(topic.get('key_concepts', []))} "
                    f"{' '.join(topic.get('formulas', []))}"
                )
                if query in searchable.lower():
                    results.append((area_name, area_data["emoji"], topic))

        result_tiles = []
        for area_name, emoji, topic in results:
            diff = topic.get("difficulty", "médio")
            diff_colors = {"fácil": "#4CAF50",
                           "médio": "#FF9800", "difícil": "#F44336"}
            result_tiles.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=12, padding=15,
                    on_click=lambda _, a=area_name, tp=topic: self._open_search_result(
                        a, tp),
                    ink=True,
                    content=ft.Row([
                        ft.Text(emoji, size=22),
                        ft.Column([
                            ft.Text(
                                topic["title"], size=14,
                                weight=ft.FontWeight.BOLD, color=t["text"],
                            ),
                            ft.Row([
                                ft.Text(area_name, size=12,
                                        color=t["text_sec"]),
                                ft.Container(
                                    bgcolor=diff_colors.get(diff, "#FF9800"),
                                    border_radius=6,
                                    padding=ft.padding.symmetric(
                                        horizontal=5, vertical=1),
                                    content=ft.Text(
                                        diff, size=10, color="#FFFFFF"),
                                ),
                            ], spacing=5),
                        ], spacing=2, expand=True),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT,
                                color=t["text_sec"], size=20),
                    ], spacing=10),
                )
            )

        empty_state = ft.Container(
            padding=40,
            content=ft.Column([
                ft.Text("🔍", size=40),
                ft.Text("Nenhum resultado encontrado",
                        size=16, color=t["text_sec"]),
                ft.Text("Tente outra palavra-chave",
                        size=13, color=t["text_sec"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=[
                    ft.TextButton(
                        "← Voltar",
                        on_click=lambda _: self._go_areas(),
                        style=ft.ButtonStyle(color=t["text_sec"]),
                    ),
                    ft.TextField(
                        value=self._search_query,
                        hint_text="🔍 Buscar tópico...",
                        border_radius=12, bgcolor=t["card"],
                        color=t["text"], height=45, text_size=14,
                        on_submit=lambda e: self._search(e.control.value),
                    ),
                    ft.Text(
                        f"📋 {len(results)} resultado(s) para \"{self._search_query}\"",
                        size=14, color=t["text_sec"],
                    ),
                    *(result_tiles if result_tiles else [empty_state]),
                    ft.Container(height=20),
                ],
                spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── TELA: RESULTADOS DE ARTIGOS (Wikipedia API) ──────────
    # ══════════════════════════════════════════════════════════
    def _build_article_results(self):
        t = self.app.theme_mgr.get_theme()

        if self._loading:
            return ft.Container(
                expand=True, bgcolor=t["bg"],
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.ProgressRing(color=t["primary"]),
                    ft.Text("🔍 Buscando artigos...", size=16, color=t["text"]),
                    ft.Text(f"Pesquisando: \"{self._article_query}\"",
                            size=13, color=t["text_sec"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            )

        article_tiles = []
        for art in self._article_results:
            extract_preview = art["extract"][:200] + \
                "..." if len(art["extract"]) > 200 else art["extract"]
            article_tiles.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=14, padding=15,
                    on_click=lambda _, a=art: self._open_article(a["title"]),
                    ink=True,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.ARTICLE,
                                    color=t["primary"], size=22),
                            ft.Text(
                                art["title"], size=15,
                                weight=ft.FontWeight.BOLD, color=t["text"],
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT,
                                    color=t["text_sec"], size=18),
                        ], spacing=8),
                        ft.Text(
                            extract_preview, size=13, color=t["text_sec"],
                            max_lines=4, overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ], spacing=6),
                )
            )

        if not article_tiles:
            article_tiles.append(
                ft.Container(
                    padding=40,
                    content=ft.Column([
                        ft.Text("📭", size=40),
                        ft.Text("Nenhum artigo encontrado",
                                size=16, color=t["text_sec"]),
                        ft.Text("Tente outra palavra-chave",
                                size=13, color=t["text_sec"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                )
            )

        # Campo para nova busca
        new_search = ft.TextField(
            value=self._article_query,
            hint_text="🔍 Buscar outro tema...",
            border_radius=12, bgcolor=t["card"],
            color=t["text"], height=45, text_size=14,
            on_submit=lambda e: self._search_articles_api(e.control.value),
        )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=[
                    ft.TextButton(
                        "← Voltar",
                        on_click=lambda _: self._go_areas(),
                        style=ft.ButtonStyle(color=t["text_sec"]),
                    ),
                    new_search,
                    ft.Text(
                        f"📚 {len(self._article_results)} artigo(s) para \"{self._article_query}\"",
                        size=15, weight=ft.FontWeight.BOLD, color=t["primary"],
                    ),
                    *article_tiles,
                    ft.Container(height=20),
                ],
                spacing=10, scroll=ft.ScrollMode.AUTO,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── TELA: LEITURA DE ARTIGO COMPLETO ─────────────────────
    # ══════════════════════════════════════════════════════════
    def _build_reading(self):
        t = self.app.theme_mgr.get_theme()

        if self._loading:
            return ft.Container(
                expand=True, bgcolor=t["bg"],
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.ProgressRing(color=t["primary"]),
                    ft.Text("📖 Carregando artigo...",
                            size=16, color=t["text"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            )

        art = self._current_article
        if not art:
            self._mode = "areas"
            return self.build()

        # Dividir conteúdo em partes para facilitar leitura
        content_text = art["content"]
        # Limitar para não travar a UI (artigos longos)
        if len(content_text) > 8000:
            content_text = content_text[:8000] + \
                "\n\n[...] Artigo resumido. Leia completo na Wikipedia."

        sections = []

        # Voltar
        sections.append(
            ft.TextButton(
                "← Voltar aos resultados",
                on_click=lambda _: self._go_articles(),
                style=ft.ButtonStyle(color=t["text_sec"]),
            )
        )

        # Título
        sections.append(
            ft.Container(
                bgcolor=t["card"], border_radius=14, padding=20,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ARTICLE, color=t["primary"], size=28),
                        ft.Text(
                            art["title"], size=20,
                            weight=ft.FontWeight.BOLD, color=t["text"],
                            expand=True,
                        ),
                    ], spacing=10),
                    ft.Text("Fonte: Wikipedia", size=12,
                            color=t["text_sec"], italic=True),
                ], spacing=6),
            )
        )

        # Dividir o conteúdo em parágrafos para melhor leitura
        paragraphs = [p.strip() for p in content_text.split("\n") if p.strip()]

        # Agrupar parágrafos em blocos de ~3 para não criar muitos containers
        block_size = 3
        for i in range(0, len(paragraphs), block_size):
            block = "\n\n".join(paragraphs[i:i + block_size])
            sections.append(
                ft.Container(
                    bgcolor=t["card"], border_radius=12, padding=15,
                    content=ft.Text(
                        block, size=14, color=t["text"],
                        selectable=True,
                    ),
                )
            )

        # Botão abrir no navegador
        sections.append(
            ft.Container(
                padding=ft.padding.only(top=10, bottom=20),
                content=ft.Column([
                    ft.ElevatedButton(
                        content=ft.Text(
                            "🌐 Ler artigo completo na Wikipedia", size=13),
                        height=42, bgcolor=t["primary"], color="#FFFFFF",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=lambda _, u=art.get(
                            "url", ""): self._launch_url(u),
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("🔍 Pesquisar outro tema", size=13),
                        height=42, bgcolor=t["card"], color=t["text"],
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=lambda _: self._go_areas(),
                    ),
                ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            )
        )

        return ft.Container(
            expand=True, bgcolor=t["bg"],
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            content=ft.Column(
                controls=sections,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
        )

    # ══════════════════════════════════════════════════════════
    # ── NAVEGAÇÃO INTERNA ────────────────────────────────────
    # ══════════════════════════════════════════════════════════
    def _open_area(self, area_name):
        self._current_area = area_name
        self._mode = "topics"
        self.app.show_view("theory")

    def _open_topic(self, topic):
        self._current_topic = topic
        self._mode = "detail"
        self.app.show_view("theory")

    def _go_areas(self):
        self._mode = "areas"
        self.app.show_view("theory")

    def _go_topics(self):
        self._mode = "topics"
        self.app.show_view("theory")

    def _go_articles(self):
        self._mode = "articles"
        self.app.show_view("theory")

    def _search(self, query):
        if not query or len(query.strip()) < 2:
            self.app.show_snackbar(
                "⚠️ Digite pelo menos 2 caracteres para buscar.")
            return
        self._search_query = query.strip()
        self._mode = "search"
        self.app.show_view("theory")

    def _open_search_result(self, area_name, topic):
        self._current_area = area_name
        self._current_topic = topic
        self._mode = "detail"
        self.app.show_view("theory")

    def _find_related(self, topic_title):
        """Navega para um tópico relacionado buscando pelo título."""
        for area_name, area_data in ENEM_SYLLABUS.items():
            for topic in area_data["topics"]:
                if topic["title"] == topic_title:
                    self._current_area = area_name
                    self._current_topic = topic
                    self._mode = "detail"
                    self.app.show_view("theory")
                    return
        self._search(topic_title)

    # ══════════════════════════════════════════════════════════
    # ── AÇÕES ────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════
    def _mark_read(self):
        uid = self.app.get_user_id()
        if not uid:
            self.app.show_snackbar("⚠️ Faça login para salvar seu progresso!")
            return
        notes = self._notes_field.value if self._notes_field else None
        self.db.mark_theory_read(
            uid, self._current_area,
            self._current_topic["title"],
            completed=True, notes=notes,
        )
        self.app.show_snackbar("✅ Tópico concluído! +15 XP", bgcolor="#4CAF50")
        self.app.refresh_xp_sidebar()
        self.app.show_view("theory")

    # ══════════════════════════════════════════════════════════
    # ── PESQUISA DE ARTIGOS VIA WIKIPEDIA API ────────────────
    # ══════════════════════════════════════════════════════════
    def _search_articles_api(self, query):
        """Busca artigos na Wikipedia e mostra resultados inline."""
        if not query or not query.strip():
            self.app.show_snackbar("⚠️ Digite um tema para pesquisar.")
            return
        query = query.strip()
        self._article_query = query
        self._loading = True
        self._mode = "articles"
        self.app.show_view("theory")

        def _fetch():
            results = _wiki_search(query, limit=6)
            self._article_results = results
            self._loading = False
            self.app.show_view("theory")

        threading.Thread(target=_fetch, daemon=True).start()

    def _open_article(self, title):
        """Carrega artigo completo da Wikipedia e mostra inline."""
        self._loading = True
        self._mode = "reading"
        self.app.show_view("theory")

        def _fetch():
            article = _wiki_article(title)
            self._current_article = article
            self._loading = False
            self.app.show_view("theory")

        threading.Thread(target=_fetch, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    # ── ABRIR URL NO NAVEGADOR (async no Flet 0.84) ─────────
    # ══════════════════════════════════════════════════════════
    def _launch_url(self, url):
        """Abre URL no navegador — launch_url é async no Flet 0.84."""
        if not url:
            return

        async def _open():
            await self.app.page.launch_url(url)

        self.app.page.run_task(_open)
