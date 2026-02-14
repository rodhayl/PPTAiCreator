"""Visual preview worker for slide PNG generation.

Offline-first implementation:
- Generates high-resolution slide preview images from structured slide content.
- Does not require external rendering services.
- Can be replaced later with PPTX-native conversion for pixel-perfect previews.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..state import PipelineState


class PreviewWorker:
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height

    def _line_wrap(self, text: str, max_chars: int = 90) -> list[str]:
        words = (text or "").split()
        if not words:
            return []
        lines: list[str] = []
        current: list[str] = []
        for word in words:
            test = " ".join(current + [word])
            if len(test) <= max_chars:
                current.append(word)
            else:
                lines.append(" ".join(current))
                current = [word]
        if current:  # pragma: no branch
            lines.append(" ".join(current))
        return lines

    def _safe_font(self, size: int):
        try:
            from PIL import ImageFont

            return ImageFont.truetype("arial.ttf", size=size)
        except Exception:
            from PIL import ImageFont

            return ImageFont.load_default()

    def _render_slide(self, title: str, bullets: list[str], output_file: Path) -> None:
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (self.width, self.height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        title_font = self._safe_font(52)
        body_font = self._safe_font(34)

        draw.rectangle(
            (40, 40, self.width - 40, self.height - 40),
            outline=(220, 220, 220),
            width=3,
        )
        draw.text(
            (80, 80), title or "Untitled Slide", fill=(20, 20, 20), font=title_font
        )

        cursor_y = 200
        for bullet in bullets[:8]:
            wrapped = self._line_wrap(str(bullet), max_chars=75)
            if not wrapped:
                continue
            draw.text(
                (110, cursor_y), f"• {wrapped[0]}", fill=(35, 35, 35), font=body_font
            )
            cursor_y += 48
            for continuation in wrapped[1:3]:
                draw.text(
                    (145, cursor_y), continuation, fill=(55, 55, 55), font=body_font
                )
                cursor_y += 42
            cursor_y += 16
            if cursor_y > self.height - 120:
                break

        output_file.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_file, format="PNG")

    def generate_previews(self, state: PipelineState) -> PipelineState:
        try:
            import PIL  # noqa: F401
        except Exception:
            state.warnings.append("Preview generation skipped: Pillow is not installed")
            return state

        run_folder = state.run_id or state.session_id
        preview_dir = Path("artifacts") / "previews" / str(run_folder)

        manifest: Dict[str, str] = {}
        for idx, slide in enumerate(state.content or [], start=1):
            output_file = preview_dir / f"slide_{idx:02d}.png"
            bullets = []
            for bullet in slide.bullets or []:
                if isinstance(bullet, dict):
                    bullets.append(str(bullet.get("text", "")))
                elif hasattr(bullet, "text"):
                    bullets.append(str(bullet.text))
                else:
                    bullets.append(str(bullet))

            self._render_slide(slide.title, bullets, output_file)
            manifest[str(idx)] = str(output_file.resolve())

        state.preview_images = manifest
        state.preview_manifest_path = str((preview_dir / "manifest.json").resolve())

        import json

        with open(preview_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return state
