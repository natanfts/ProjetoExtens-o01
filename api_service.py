import requests
import json
import random
import html
import time
import logging
from youtubesearchpython import VideosSearch

logger = logging.getLogger("APIService")


def _retry_request(method, url, max_retries=3, backoff=1.5, **kwargs):
    """Faz uma requisição HTTP com retry e backoff exponencial."""
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = method(url, **kwargs)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(backoff * (2 ** attempt))
        except requests.HTTPError as e:
            if e.response and e.response.status_code >= 500:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(backoff * (2 ** attempt))
            else:
                raise
    raise last_error


class APIService:
    """Serviço de APIs externas: ENEM API + Open Trivia DB + YouTube Search."""

    OPENTDB_URL = "https://opentdb.com/api.php"
    ENEM_API_BASE = "https://api.enem.dev/v1"

    # Anos disponíveis na API enem.dev
    ENEM_YEARS = list(range(2009, 2026))  # 2009 a 2025

    # Disciplinas do ENEM (valores retornados pela API)
    ENEM_DISCIPLINES = {
        "linguagens":        "Linguagens, Códigos e suas Tecnologias",
        "ciencias-humanas":  "Ciências Humanas e suas Tecnologias",
        "ciencias-natureza": "Ciências da Natureza e suas Tecnologias",
        "matematica":        "Matemática e suas Tecnologias",
    }

    ENEM_SUBJECTS = [
        "Linguagens", "Matemática",
        "Ciências da Natureza", "Ciências Humanas", "Redação",
    ]

    CONCURSO_SUBJECTS = [
        "Português", "Raciocínio Lógico", "Informática",
        "Direito Constitucional", "Atualidades",
    ]

    _TRIVIA_CATEGORIES = {
        "Ciências da Natureza": 17,
        "História": 23,
        "Geografia": 22,
        "Matemática": 19,
        "Informática": 18,
    }

    # ── ENEM API — buscar provas disponíveis ─────────────────
    def fetch_enem_exams(self) -> list[dict]:
        """Retorna lista de provas/anos disponíveis na API."""
        try:
            resp = _retry_request(
                requests.get,
                f"{self.ENEM_API_BASE}/exams", timeout=10)
            data = resp.json()
            return data if isinstance(data, list) else data.get("exams", [])
        except Exception as e:
            logger.error("Erro ao buscar provas ENEM: %s", e)
            return []

    # ── ENEM API — buscar questões de um ano ─────────────────
    def fetch_enem_questions(self, year: int, limit: int = 200, offset: int = 0) -> list[dict]:
        """
        Busca questões reais do ENEM de um ano específico.
        Retorna lista de dicts padronizados.
        Respeita rate-limit de 1 req/s.
        """
        all_questions = []
        current_offset = offset

        try:
            while True:
                resp = _retry_request(
                    requests.get,
                    f"{self.ENEM_API_BASE}/exams/{year}/questions",
                    params={"limit": min(limit, 50), "offset": current_offset},
                    timeout=15,
                )
                data = resp.json()

                questions = data.get("questions", [])
                if not questions:
                    break

                for q in questions:
                    parsed = self._parse_enem_question(q, year)
                    if parsed:
                        all_questions.append(parsed)

                # Verificar se há mais páginas
                if len(questions) < 50 or len(all_questions) >= limit:
                    break

                current_offset += len(questions)
                time.sleep(1.1)  # Respeitar rate-limit

            return all_questions[:limit]

        except Exception as e:
            logger.error("Erro ao buscar questões ENEM %d: %s", year, e)
            return all_questions  # Retorna o que já buscou

    # ── ENEM API — buscar questão específica ─────────────────
    def fetch_enem_question(self, year: int, index: int) -> dict | None:
        """Busca uma questão específica do ENEM por ano e índice."""
        try:
            resp = _retry_request(
                requests.get,
                f"{self.ENEM_API_BASE}/exams/{year}/questions/{index}",
                timeout=10,
            )
            return self._parse_enem_question(resp.json(), year)
        except Exception as e:
            logger.error("Erro ao buscar questão %d/%d: %s", year, index, e)
            return None

    # ── ENEM API — buscar por disciplina ─────────────────────
    def fetch_enem_by_discipline(self, year: int, discipline: str) -> list[dict]:
        """
        Busca todas as questões de um ano e filtra por disciplina.
        discipline: 'linguagens', 'ciencias-humanas', 'ciencias-natureza', 'matematica'
        """
        all_q = self.fetch_enem_questions(year, limit=200)
        return [q for q in all_q if q.get("discipline") == discipline]

    # ── Parser interno ───────────────────────────────────────
    def _parse_enem_question(self, raw: dict, year: int) -> dict | None:
        """Converte questão da API enem.dev para formato padronizado."""
        try:
            alternatives = raw.get("alternatives", [])
            if not alternatives:
                return None

            # Montar texto completo da questão
            context = raw.get("context") or ""
            intro = raw.get("alternativesIntroduction") or ""

            # Texto da questão = contexto + introdução das alternativas
            question_text = ""
            if context:
                question_text += context.strip()
            if intro:
                if question_text:
                    question_text += "\n\n"
                question_text += intro.strip()

            if not question_text:
                question_text = raw.get(
                    "title", f"Questão {raw.get('index', '?')}")

            # Alternativas
            options = []
            correct_answer = ""
            correct_letter = raw.get("correctAlternative", "")

            for alt in alternatives:
                letter = alt.get("letter", "")
                text = alt.get("text", "")
                opt_text = f"{letter}) {text}" if text else letter
                options.append(opt_text)
                if alt.get("isCorrect") or letter == correct_letter:
                    correct_answer = opt_text

            if not options or not correct_answer:
                return None

            # Imagens associadas
            files = raw.get("files", [])
            alt_files = [a.get("file") for a in alternatives if a.get("file")]

            return {
                "year": year,
                "index": raw.get("index", 0),
                "title": raw.get("title", ""),
                "discipline": raw.get("discipline") or "",
                "discipline_name": self.ENEM_DISCIPLINES.get(
                    raw.get("discipline", ""), raw.get("discipline", "")),
                "language": raw.get("language"),
                "context": context,
                "question_intro": intro,
                "question_text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "correct_letter": correct_letter,
                "images": files,
                "alt_images": alt_files,
            }
        except Exception as e:
            logger.error("Erro ao parsear questão ENEM: %s", e)
            return None

    # ── busca de questões trivia ─────────────────────────────
    def fetch_trivia_questions(self, category_name="Ciências da Natureza", amount=5):
        cat_id = self._TRIVIA_CATEGORIES.get(category_name)
        if not cat_id:
            return []
        try:
            resp = requests.get(
                self.OPENTDB_URL,
                params={"amount": amount, "category": cat_id,
                        "type": "multiple", "difficulty": "medium"},
                timeout=8,
            )
            data = resp.json()
            if data.get("response_code") != 0:
                return []
            questions = []
            for item in data["results"]:
                opts = [html.unescape(o) for o in item["incorrect_answers"]]
                correct = html.unescape(item["correct_answer"])
                opts.append(correct)
                random.shuffle(opts)
                questions.append({
                    "question": html.unescape(item["question"]),
                    "options": json.dumps(opts),
                    "correct_answer": correct,
                    "explanation": f"Resposta correta: {correct}",
                    "topic": html.unescape(item["category"]),
                    "difficulty": item["difficulty"],
                    "subject": category_name,
                    "category": "geral",
                })
            return questions
        except Exception:
            return []

    # ── busca de vídeos no YouTube ───────────────────────────
    @staticmethod
    def search_youtube_videos(query: str, limit: int = 5) -> list[dict]:
        """
        Busca vídeos no YouTube usando youtube-search-python.
        Retorna lista de dicts com: url, title, channel, duration, views, published.
        Não precisa de API key.
        """
        try:
            search = VideosSearch(query, limit=limit)
            results = search.result().get("result", [])
            videos = []
            for item in results:
                video = {
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "channel": item.get("channel", {}).get("name", ""),
                    "duration": item.get("duration", ""),
                    "views": item.get("viewCount", {}).get("short", ""),
                    "published": item.get("publishedTime", ""),
                    "thumbnail": "",
                }
                thumbs = item.get("thumbnails", [])
                if thumbs:
                    video["thumbnail"] = thumbs[0].get("url", "")
                videos.append(video)
            return videos
        except Exception:
            return []

    @staticmethod
    def get_youtube_search_url(query: str) -> str:
        q = query.replace(" ", "+")
        return f"https://www.youtube.com/results?search_query={q}+aula+enem"

    # ══════════════════════════════════════════════════════════
    # ── WIKIPEDIA (Teoria) ───────────────────────────────────
    # ══════════════════════════════════════════════════════════
    @staticmethod
    def fetch_wiki_summary(query: str) -> dict | None:
        """
        Busca resumo de um tópico na Wikipedia em português.
        Retorna dict com: title, extract, thumbnail, url — ou None.
        """
        try:
            url = "https://pt.wikipedia.org/api/rest_v1/page/summary/" + \
                  requests.utils.quote(query)
            resp = requests.get(url, timeout=8, headers={
                "User-Agent": "SwitchFocusApp/1.0 (educational-project)"
            })
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "title": data.get("title", query),
                    "extract": data.get("extract", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                }
            # Se 404, tenta busca alternativa
            if resp.status_code == 404:
                search_url = "https://pt.wikipedia.org/w/api.php"
                params = {
                    "action": "query", "list": "search",
                    "srsearch": query, "srlimit": 1,
                    "format": "json",
                }
                sr = requests.get(search_url, params=params, timeout=8,
                                  headers={"User-Agent": "SwitchFocusApp/1.0"})
                if sr.status_code == 200:
                    results = sr.json().get("query", {}).get("search", [])
                    if results:
                        return APIService.fetch_wiki_summary(results[0]["title"])
            return None
        except Exception as e:
            logger.warning(f"Wikipedia fetch error: {e}")
            return None
