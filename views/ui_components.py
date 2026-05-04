import flet as ft


def with_alpha(color: str, alpha: str) -> str:
    raw = (color or "").lstrip("#")
    if len(raw) == 8:
        raw = raw[2:]
    if len(raw) != 6:
        raw = "000000"
    return f"#{alpha}{raw}"


def soft_shadow(color: str = "#14000000", blur: int = 24, spread: int = 0, y: int = 8):
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
        border=border or ft.border.all(1, theme.get("border_soft", "#E9DCC9")),
        gradient=gradient,
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
                size=20,
                weight=ft.FontWeight.W_700,
                color=theme["text"],
            ),
            ft.Text(
                subtitle or "",
                size=12,
                color=theme["text_sec"],
            ),
        ],
        spacing=4,
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


def _press_overlay(theme: dict):
    return {
        ft.ControlState.HOVERED: with_alpha(theme["button"], "1E"),
        ft.ControlState.PRESSED: with_alpha(theme["button"], "36"),
        ft.ControlState.FOCUSED: with_alpha(theme["button"], "24"),
    }


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
        content=ft.Text(label, color="#FFFFFF", weight=ft.FontWeight.W_600),
        icon=icon,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height,
        bgcolor=theme["button"],
        color="#FFFFFF",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=16),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 6,
                ft.ControlState.PRESSED: 1,
            },
            overlay_color=_press_overlay(theme),
            animation_duration=160,
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
        content=ft.Text(label, color=theme["text"], weight=ft.FontWeight.W_600),
        icon=icon,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height,
        style=ft.ButtonStyle(
            color=theme["text"],
            side=ft.BorderSide(1, theme.get("border_strong", "#D9C4A6")),
            bgcolor={
                ft.ControlState.DEFAULT: theme.get("surface_soft", "#FCF6EC"),
                ft.ControlState.HOVERED: with_alpha(theme["primary"], "14"),
                ft.ControlState.PRESSED: with_alpha(theme["primary"], "1F"),
            },
            shape=ft.RoundedRectangleBorder(radius=16),
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            overlay_color=_press_overlay(theme),
            animation_duration=160,
        ),
    )


def filled_button(
    theme: dict,
    label: str,
    on_click,
    *,
    bgcolor: str | None = None,
    color: str = "#FFFFFF",
    icon: str | None = None,
    expand: bool = False,
    width=None,
    height: int = 44,
):
    base = bgcolor or theme["button"]
    return ft.ElevatedButton(
        content=ft.Text(label, color=color, weight=ft.FontWeight.W_600),
        icon=icon,
        on_click=on_click,
        expand=expand,
        width=width,
        height=height,
        bgcolor=base,
        color=color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=14),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            elevation={
                ft.ControlState.DEFAULT: 2,
                ft.ControlState.HOVERED: 5,
                ft.ControlState.PRESSED: 1,
            },
            overlay_color={
                ft.ControlState.HOVERED: "#14FFFFFF",
                ft.ControlState.PRESSED: "#24FFFFFF",
            },
            animation_duration=160,
        ),
    )


def field_style(theme: dict):
    return {
        "bgcolor": theme["entry_bg"],
        "border_color": theme.get("border_soft", theme["entry_border"]),
        "focused_border_color": theme["primary"],
        "color": theme["text"],
        "label_style": ft.TextStyle(color=theme["text_sec"]),
    }


def stat_pill(theme: dict, label: str, value: str, tone: str | None = None):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=999,
        bgcolor=tone or theme.get("chip_bg", "#F4E8D7"),
        border=ft.border.all(1, theme.get("border_soft", "#E9DCC9")),
        content=ft.Row(
            [
                ft.Text(value, size=14, weight=ft.FontWeight.BOLD, color=theme["text"]),
                ft.Text(label, size=11, color=theme.get("chip_text", theme["text_sec"])),
            ],
            spacing=6,
            tight=True,
        ),
    )


def metric_card(theme: dict, icon: str, label: str, value: str, helper: str = ""):
    return soft_card(
        theme,
        ft.Column(
            [
                ft.Text(icon, size=22),
                ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=theme["text"]),
                ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=theme["text_sec"]),
                ft.Text(helper, size=10, color=theme["text_sec"]) if helper else ft.Container(height=0),
            ],
            spacing=5,
            tight=True,
        ),
        padding=18,
        radius=20,
        expand=True,
        bgcolor=theme["card"],
    )


def progress_track(theme: dict, value: float, color: str | None = None, bgcolor: str | None = None, height: int = 10):
    return ft.ProgressBar(
        value=value,
        height=height,
        color=color or theme["primary"],
        bgcolor=bgcolor or with_alpha(theme["primary"], "20"),
        border_radius=height,
    )
