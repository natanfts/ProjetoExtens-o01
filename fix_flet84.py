"""Script simples para ajustar incompatibilidades comuns com Flet 0.84.

Mantido propositalmente pequeno para servir como utilitário de manutenção.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
FILES = list((ROOT / "views").glob("*.py")) + [ROOT / "main.py"]


def apply_fixes(content: str) -> str:
    fixes = [
        ("ft.alignment.center", "ft.Alignment.CENTER"),
        ("ft.alignment.top_center", "ft.Alignment.TOP_CENTER"),
        ("ft.alignment.top_left", "ft.Alignment.TOP_LEFT"),
        ("ft.alignment.top_right", "ft.Alignment.TOP_RIGHT"),
        ("ft.alignment.bottom_left", "ft.Alignment.BOTTOM_LEFT"),
        ("ft.alignment.bottom_right", "ft.Alignment.BOTTOM_RIGHT"),
    ]

    for old, new in fixes:
        content = content.replace(old, new)

    # Ajusta botões com `text=` para `content=`, compatível com Flet 0.84.
    button_patterns = [
        (r"ft\.ElevatedButton\(", "ft.ElevatedButton("),
        (r"ft\.TextButton\(", "ft.TextButton("),
        (r"ft\.OutlinedButton\(", "ft.OutlinedButton("),
    ]

    for pattern, replacement in button_patterns:
        content = re.sub(
            pattern + r"([^)]*?)\btext=",
            replacement + r"\1content=",
            content,
        )

    return content


def main():
    total = 0

    for path in FILES:
        content = path.read_text(encoding="utf-8")
        updated = apply_fixes(content)

        if updated != content:
            path.write_text(updated, encoding="utf-8")
            total += 1
            print(f"Fixed: {path.name}")
        else:
            print(f"OK: {path.name}")

    print(f"\nTotal files modified: {total}")


if __name__ == "__main__":
    main()
