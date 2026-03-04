import customtkinter as ctk
from ui.app_shell import AppShell
from core.engine import Engine
from core.scheduler_engine import SchedulerEngine


def main():
    print("[AI] Provider: openai")

    app = ctk.CTk()
    app.title("GNX PRODUCTION")
    app.geometry("1200x750")

    # INIT CORE SERVICES (ONE INSTANCE ONLY)
    engine = Engine()
    scheduler = SchedulerEngine(engine)

    # Attach to app so pages can access
    app.engine = engine
    app.scheduler = scheduler

    AppShell(app)

    app.mainloop()


if __name__ == "__main__":
    main()