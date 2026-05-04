THEMES = {
    "Studio Creme": {
        "primary": "#C98A4A",
        "secondary": "#EFE4D4",
        "accent": "#1F8A70",
        "bg": "#F7F1E6",
        "sidebar": "#F1E8D7",
        "card": "#FFFDF8",
        "text": "#2E2A25",
        "text_sec": "#8C7B6A",
        "success": "#1F8A70",
        "danger": "#C45144",
        "warning": "#D6982F",
        "button": "#C98A4A",
        "button_hover": "#B6783B",
        "entry_bg": "#FFF9F1",
        "entry_border": "#DCC9AF",
        "progress": "#C98A4A",
        "surface_alt": "#F9F2E7",
        "surface_soft": "#FCF6EC",
        "shadow_dark": "#12000000",
        "shadow_light": "#70FFFFFF",
        "border_soft": "#E9DCC9",
        "border_strong": "#D9C4A6",
        "chip_bg": "#F4E8D7",
        "chip_text": "#5E4835",
        "emoji": "SB",
        "desc": "Paleta clara premium com tons creme e caramelo.",
        "greeting": "{saudacao}, {nome}!",
        "welcome": "Bem-vindo ao seu espaco de foco.",
        "focus_label": "Sessao de foco",
        "short_break_label": "Pausa curta",
        "long_break_label": "Pausa longa",
        "timer_title": "Pomodoro",
        "study_title": "Estudar",
        "celebration": "Excelente progresso hoje.",
        "new_achievement": "Nova conquista: {emoji} {title}",
        "level_prefix": "Nivel",
        "streak_msg": "{dias} dias de constancia",
        "xp_name": "XP",
    },
    "Areia Solar": {
        "primary": "#B57D41",
        "secondary": "#EFE6DA",
        "accent": "#2D7E69",
        "bg": "#F8F3EA",
        "sidebar": "#F2EBDD",
        "card": "#FFFEFA",
        "text": "#332B24",
        "text_sec": "#8E7C69",
        "success": "#2D7E69",
        "danger": "#BE5145",
        "warning": "#CD9635",
        "button": "#B57D41",
        "button_hover": "#A56E34",
        "entry_bg": "#FFF9F0",
        "entry_border": "#DFC9A9",
        "progress": "#B57D41",
        "surface_alt": "#F9F4EB",
        "surface_soft": "#FEF9F1",
        "shadow_dark": "#12000000",
        "shadow_light": "#75FFFFFF",
        "border_soft": "#EBDDCC",
        "border_strong": "#D9C5A7",
        "chip_bg": "#F4E7D4",
        "chip_text": "#634933",
        "emoji": "AS",
        "desc": "Tons claros quentes para um look de produto editorial.",
        "greeting": "{saudacao}, {nome}!",
        "welcome": "Bem-vindo ao seu espaco de foco.",
        "focus_label": "Sessao de foco",
        "short_break_label": "Pausa curta",
        "long_break_label": "Pausa longa",
        "timer_title": "Pomodoro",
        "study_title": "Estudar",
        "celebration": "Excelente progresso hoje.",
        "new_achievement": "Nova conquista: {emoji} {title}",
        "level_prefix": "Nivel",
        "streak_msg": "{dias} dias de constancia",
        "xp_name": "XP",
    },
    "Marfim Urbano": {
        "primary": "#A8733B",
        "secondary": "#EFE5D8",
        "accent": "#1E7A63",
        "bg": "#F6F0E4",
        "sidebar": "#F0E7D8",
        "card": "#FFFDF8",
        "text": "#2F2923",
        "text_sec": "#897765",
        "success": "#1E7A63",
        "danger": "#BA4A3F",
        "warning": "#C88D32",
        "button": "#A8733B",
        "button_hover": "#966534",
        "entry_bg": "#FFF8EF",
        "entry_border": "#D8C2A4",
        "progress": "#A8733B",
        "surface_alt": "#F8F2E8",
        "surface_soft": "#FDF7ED",
        "shadow_dark": "#12000000",
        "shadow_light": "#75FFFFFF",
        "border_soft": "#E9DCC8",
        "border_strong": "#D2BE9F",
        "chip_bg": "#F2E5D3",
        "chip_text": "#5A4430",
        "emoji": "MU",
        "desc": "Visual limpo, elegante e neutro para produtividade diaria.",
        "greeting": "{saudacao}, {nome}!",
        "welcome": "Bem-vindo ao seu espaco de foco.",
        "focus_label": "Sessao de foco",
        "short_break_label": "Pausa curta",
        "long_break_label": "Pausa longa",
        "timer_title": "Pomodoro",
        "study_title": "Estudar",
        "celebration": "Excelente progresso hoje.",
        "new_achievement": "Nova conquista: {emoji} {title}",
        "level_prefix": "Nivel",
        "streak_msg": "{dias} dias de constancia",
        "xp_name": "XP",
    },
}

VIEW_ACCENTS = {
    "dashboard": "#C98A4A",
    "pomodoro": "#1F8A70",
    "tasks": "#C36A4E",
    "study": "#5677B9",
    "flashcards": "#7A6BC8",
    "shorts": "#C56B7E",
    "history": "#6F7B8A",
    "settings": "#886F58",
    "theory": "#3D80A0",
    "enem_editais": "#9D7344",
    "login": "#2A8D72",
    "more": "#A77644",
}

DEFAULT_THEME = "Studio Creme"


class ThemeManager:
    def __init__(self):
        self.current_theme = DEFAULT_THEME
        self.active_view = "dashboard"

    def set_active_view(self, name: str):
        self.active_view = name or "dashboard"

    def _build_view_theme(self, base: dict, view_name: str | None = None) -> dict:
        t = dict(base)
        accent = VIEW_ACCENTS.get(view_name or self.active_view)
        if not accent:
            return t

        t["primary"] = accent
        t["button"] = accent
        t["progress"] = accent
        t["entry_border"] = accent
        return t

    def get_theme(self, name=None):
        theme_name = name or self.current_theme
        base = THEMES.get(theme_name, THEMES[DEFAULT_THEME])
        return self._build_view_theme(base)

    def set_theme(self, name):
        if name in THEMES:
            self.current_theme = name

    def list_themes(self):
        return list(THEMES.keys())

    def get_color(self, key, name=None):
        theme = self.get_theme(name)
        return theme.get(key, "#FFFFFF")
