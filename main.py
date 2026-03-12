import customtkinter as ctk

from ui.app_shell import AppShell
from core.engine import Engine


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("GNX Production Studio")
    app.geometry("1440x900")
    app.minsize(1200, 760)

    app.engine = Engine()

    AppShell(app)
    app.mainloop()


if __name__ == "__main__":
    main()