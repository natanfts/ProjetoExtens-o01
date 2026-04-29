import flet as ft


def with_alpha(color: str, alpha: str) -> str:
    if not isinstance(color, str):
        return color

    raw = color.strip().lstrip("#")
    if len(alpha) != 2:
        return color

    hex_chars = "0123456789abcdefABCDEF"
    if any(ch not in hex_chars for ch in raw):
        return color

    if len(raw) == 6:
        return f"#{alpha.upper()}{raw.upper()}"
    if len(raw) == 8:
        return f"#{alpha.upper()}{raw[2:].upper()}"
    return color


def soft_shadow(color: str = "#000000", blur: int = 22, spread: int = 0, y: int = 8):
    return ft.BoxShadow(
        spread_radius=spread,
        blur_radius=blur,
        color=color,
        offset=ft.Offset(0, y),
    )


def soft_card(
    theme: dict,
    content,
    *,
    padding=20,
    radius: int = 24,
    bgcolor: str | None = None,
    border=None,
    height=None,
    width=None,
    expand: bool = False,
    gradient=None,
    on_click=None,
):
    base_color = bgcolor or theme["card"]
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=radius,
        bgcolor=base_color,
        border=border,
        gradient=gradient or ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=[
                theme.get("surface_alt", base_color),
                base_color,
                theme.get("card", base_color),
            ],
        ),
        shadow=[
            soft_shadow(theme.get("shadow_dark", "#38091118"), blur=24, y=10),
            soft_shadow(theme.get("shadow_light", "#0DFFFFFF"), blur=14, y=-3),
        ],
        height=height,
        width=width,
        expand=expand,
        on_click=on_click,
    )


def section_title(theme: dict, title: str, subtitle: str | None = None, action=None):
    text_col = ft.Column(
        controls=[
            ft.Text(
                title,
                size=18,
                weight=ft.FontWeight.W_700,
                color=theme["text"],
            ),
            ft.Text(
                subtitle or "",
                size=12,
                color=theme["text_sec"],
            ),
        ],
        spacing=3,
        tight=True,
    )
    if not subtitle:
        text_col.controls.pop()

    controls = [text_col]
    if action:
        controls.append(action)

    return ft.Row(
        controls=controls,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def primary_button(
    theme: dict,
    label: str,
    on_click,
    *,
    icon: str | None = None,
    expand: bool = False,
    width=None,
    height: int = 48,
):
    return ft.ElevatedButton(
        content=label,
        icon=icon,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height,
        bgcolor=theme["button"],
        color="#FFFFFF",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            elevation=0,
            overlay_color="#14FFFFFF",
        ),
    )


def secondary_button(
    theme: dict,
    label: str,
    on_click,
    *,
    icon: str | None = None,
    expand: bool = False,
    width=None,
    height: int = 48,
):
    return ft.OutlinedButton(
        content=label,
        icon=icon,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height,
        style=ft.ButtonStyle(
            color=theme["text"],
            side=ft.BorderSide(1, "#14FFFFFF"),
            bgcolor=theme.get("surface_soft", "#08FFFFFF"),
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
        ),
    )


def stat_pill(theme: dict, label: str, value: str, tone: str | None = None):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=999,
        bgcolor=tone or "#12FFFFFF",
        content=ft.Row(
            [
                ft.Text(value, size=14, weight=ft.FontWeight.BOLD, color=theme["text"]),
                ft.Text(label, size=11, color=theme["text_sec"]),
            ],
            spacing=6,
            tight=True,
        ),
    )


def metric_card(theme: dict, icon, label: str, value: str, helper: str = ""):
    return soft_card(
        theme,
        ft.Column(
            [
                ft.Container(
                    width=34,
                    height=34,
                    border_radius=10,
                    bgcolor=theme.get("surface_soft", "#12FFFFFF"),
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(icon, size=19, color=theme["primary"]),
                ),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=theme["text"]),
                ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=theme["text_sec"]),
                ft.Text(helper, size=10, color="#66FFFFFF") if helper else ft.Container(height=0),
            ],
            spacing=8,
            tight=True,
        ),
        padding=18,
        radius=22,
        expand=True,
        bgcolor=theme.get("surface_soft", "#08FFFFFF"),
        border=ft.border.all(1, "#12FFFFFF"),
    )


def progress_track(theme: dict, value: float, color: str | None = None, bgcolor: str = "#12FFFFFF", height: int = 10):
    return ft.ProgressBar(
        value=value,
        height=height,
        color=color or theme["primary"],
        bgcolor=bgcolor,
        border_radius=height,
    )
