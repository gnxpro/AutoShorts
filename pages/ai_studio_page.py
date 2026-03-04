import customtkinter as ctk
from core.config_manager import ConfigManager
from core.ai.ai_manager import AIManager


PRIMARY = "#b11226"
CARD_BG = "#111111"
TEXT_MUTED = "#aaaaaa"


class AIStudioPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.config = ConfigManager()
        self.ai_conf = self.config.get_ai()

        self.api_valid = self._check_api()

        if self.api_valid:
            self.ai_manager = AIManager(self.ai_conf)
        else:
            self.ai_manager = None

        self._build_ui()

    # =====================================================

    def _check_api(self):
        if self.ai_conf.get("provider") == "openai":
            return bool(self.ai_conf.get("openai_api_key"))
        if self.ai_conf.get("provider") == "gemini":
            return bool(self.ai_conf.get("gemini_api_key"))
        return False

    # =====================================================

    def _build_ui(self):

        title = ctk.CTkLabel(
            self,
            text="AI STUDIO LEVEL 4",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PRIMARY
        )
        title.pack(pady=(20, 10))

        if not self.api_valid:
            ctk.CTkLabel(
                self,
                text="⚠ API Key not configured.\nGo to SYSTEM → Settings.",
                text_color="orange"
            ).pack(pady=20)
            return

        container = ctk.CTkFrame(self, fg_color=CARD_BG)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="Input Topic").pack(anchor="w", padx=15)

        self.input_box = ctk.CTkTextbox(container, height=120)
        self.input_box.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            container,
            text="Generate Hook",
            command=self.generate_hook
        ).pack(pady=10)

        self.output_box = ctk.CTkTextbox(container, height=200)
        self.output_box.pack(fill="both", expand=True, padx=15, pady=10)

    # =====================================================

    def generate_hook(self):

        topic = self.input_box.get("1.0", "end").strip()

        result = self.ai_manager.generate_hook(
            topic,
            tone="Viral",
            style="Emotional"
        )

        self.output_box.delete("1.0", "end")
        self.output_box.insert("1.0", result)