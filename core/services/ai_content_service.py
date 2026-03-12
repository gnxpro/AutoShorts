import os
from pathlib import Path
from typing import Any, Dict, Optional

from openai import OpenAI

from core.settings_store import load_config, get as cfg_get


class AIContentServiceError(Exception):
    pass


class AIContentService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        cfg = load_config()

        self.provider = str(cfg_get(cfg, "ai.provider", "openai") or "openai").strip().lower()
        self.model = (
            model
            or str(cfg_get(cfg, "ai.model", "gpt-4o-mini") or "gpt-4o-mini").strip()
        )

        openai_key = str(cfg_get(cfg, "ai.openai.api_key", "") or "").strip()
        env_key = os.getenv("OPENAI_API_KEY", "").strip()

        self.api_key = api_key or openai_key or env_key

        if self.provider != "openai":
            raise AIContentServiceError(
                f"AI provider aktif sekarang: {self.provider}. "
                "AI stage file generator saat ini baru disiapkan untuk OpenAI dulu."
            )

        if not self.api_key:
            raise AIContentServiceError("OpenAI API Key belum diisi di AI Settings.")

        self.client = OpenAI(api_key=self.api_key)

    def _video_context_text(self, ctx: Any) -> str:
        meta = getattr(ctx, "meta", {}) or {}

        source_value = ""
        try:
            src = getattr(ctx, "source", None)
            source_value = getattr(src, "value", "") or ""
        except Exception:
            source_value = ""

        duration_policy = meta.get("duration_policy") or {}
        quality = meta.get("quality_profile") or meta.get("quality") or "-"
        face = meta.get("face_centering") or {}

        return (
            f"Source: {source_value}\n"
            f"Quality: {quality}\n"
            f"Duration policy: {duration_policy}\n"
            f"Face centering: {face}\n"
        )

    def _call_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            res = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = getattr(res, "output_text", "") or ""
            return text.strip()
        except Exception as e:
            raise AIContentServiceError(str(e))

    def _write_text(self, output_dir: str, filename: str, content: str) -> str:
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)
        fp = p / filename
        fp.write_text(content, encoding="utf-8")
        return str(fp)

    def generate_hooks(self, ctx: Any, prompt: str = "") -> Dict[str, Any]:
        base_prompt = (
            "Buat 5 hook video pendek yang kuat, singkat, dan siap pakai. "
            "Gunakan bahasa yang natural dan engaging. Output sebagai list bernomor."
        )
        if prompt:
            base_prompt += f"\n\nInstruksi manual user:\n{prompt}"

        text = self._call_text(
            system_prompt="Kamu adalah copywriter short-form video yang sangat kuat dalam hooks.",
            user_prompt=self._video_context_text(ctx) + "\n" + base_prompt,
        )
        return {"text": text}

    def generate_subtitle_notes(self, ctx: Any, prompt: str = "") -> Dict[str, Any]:
        base_prompt = (
            "Buat subtitle notes untuk editor video. "
            "Berikan gaya subtitle, tone, emphasis, dan aturan formatting yang disarankan."
        )
        if prompt:
            base_prompt += f"\n\nInstruksi manual user:\n{prompt}"

        text = self._call_text(
            system_prompt="Kamu adalah subtitle strategist untuk short-form video.",
            user_prompt=self._video_context_text(ctx) + "\n" + base_prompt,
        )
        return {"text": text}

    def generate_niche_analysis(self, ctx: Any, prompt: str = "") -> Dict[str, Any]:
        base_prompt = (
            "Analisis niche video ini untuk short-form content. "
            "Berikan target audience, angle konten, dan positioning."
        )
        if prompt:
            base_prompt += f"\n\nInstruksi manual user:\n{prompt}"

        text = self._call_text(
            system_prompt="Kamu adalah strategist niche content untuk TikTok, Shorts, Reels.",
            user_prompt=self._video_context_text(ctx) + "\n" + base_prompt,
        )
        return {"text": text}

    def generate_hashtags(self, ctx: Any, prompt: str = "") -> Dict[str, Any]:
        base_prompt = (
            "Buat 20 hashtag yang relevan untuk short-form video. "
            "Pisahkan ke kategori broad, niche, dan high-intent."
        )
        if prompt:
            base_prompt += f"\n\nInstruksi manual user:\n{prompt}"

        text = self._call_text(
            system_prompt="Kamu adalah social media growth specialist.",
            user_prompt=self._video_context_text(ctx) + "\n" + base_prompt,
        )
        return {"text": text}

    def run_enabled_tools(self, ctx: Any, output_dir: str) -> Dict[str, Any]:
        meta = getattr(ctx, "meta", {}) or {}
        ai_options = meta.get("ai_options") or {}
        tools = ai_options.get("tools") or {}

        results: Dict[str, Any] = {}

        hook_cfg = tools.get("hook") or {}
        if hook_cfg.get("enabled"):
            hook_res = self.generate_hooks(
                ctx,
                hook_cfg.get("prompt", "") if hook_cfg.get("mode") == "manual_prompt" else ""
            )
            hook_path = self._write_text(output_dir, "ai_hooks.txt", hook_res["text"])
            results["hook"] = {
                "path": hook_path,
                "text": hook_res["text"],
                "mode": hook_cfg.get("mode", "auto")
            }

        subtitle_cfg = tools.get("subtitle") or {}
        if subtitle_cfg.get("enabled"):
            subtitle_res = self.generate_subtitle_notes(
                ctx,
                subtitle_cfg.get("prompt", "") if subtitle_cfg.get("mode") == "manual_prompt" else ""
            )
            subtitle_path = self._write_text(output_dir, "ai_subtitle_notes.txt", subtitle_res["text"])
            results["subtitle"] = {
                "path": subtitle_path,
                "text": subtitle_res["text"],
                "mode": subtitle_cfg.get("mode", "auto")
            }

        niche_cfg = tools.get("niche") or {}
        if niche_cfg.get("enabled"):
            niche_res = self.generate_niche_analysis(
                ctx,
                niche_cfg.get("prompt", "") if niche_cfg.get("mode") == "manual_prompt" else ""
            )
            niche_path = self._write_text(output_dir, "ai_niche_analysis.txt", niche_res["text"])
            results["niche"] = {
                "path": niche_path,
                "text": niche_res["text"],
                "mode": niche_cfg.get("mode", "auto")
            }

        hashtag_cfg = tools.get("hashtag") or {}
        if hashtag_cfg.get("enabled"):
            hashtag_res = self.generate_hashtags(
                ctx,
                hashtag_cfg.get("prompt", "") if hashtag_cfg.get("mode") == "manual_prompt" else ""
            )
            hashtag_path = self._write_text(output_dir, "ai_hashtags.txt", hashtag_res["text"])
            results["hashtag"] = {
                "path": hashtag_path,
                "text": hashtag_res["text"],
                "mode": hashtag_cfg.get("mode", "auto")
            }

        return results