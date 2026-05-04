import flet as ft
import sys
import os
import traceback

# garantir que o diretório do script esteja no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main(page: ft.Page):
    try:
        from views.app import SwitchFocusApp
        app = SwitchFocusApp(page)
        app.initialize()
    except Exception as e:
        error_msg = f"Erro fatal:\n{e}\n\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        page.add(ft.Text(error_msg, color=ft.Colors.RED))


if __name__ == "__main__":
    ft.run(main)
