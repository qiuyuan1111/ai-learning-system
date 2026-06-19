"""④ 文档 / 思维导图渲染（见 work-person-c.md 4.3.3 DocRenderer）。

支持：
    - Markdown：直接输出 .md
    - PDF：基于 Markdown，使用 reportlab 渲染（中文字体回退）
    - 思维导图：将大纲层级转为 Markmap 兼容的 Markdown，输出 .md（可被 markmap 渲染）
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List

from ..models.dto import Outline, SectionContent

logger = logging.getLogger(__name__)


class DocRenderer:
    """文档 / 思维导图渲染器。"""

    async def render_markdown(self, title: str, sections: List[SectionContent], output_dir: Path) -> Path:
        md = self._compose_markdown(title, sections)
        safe_title = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "_", title).strip("_ ")
        file_path = output_dir / f"{safe_title}.md"
        file_path.write_text(md, encoding="utf-8")
        logger.info("Markdown 已生成：%s", file_path)
        return file_path

    async def render_pdf(self, title: str, sections: List[SectionContent], output_dir: Path) -> Path:
        """Markdown → PDF（reportlab）。中文字体缺失时回退到 ASCII。"""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        safe_title = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "_", title).strip("_ ")
        file_path = output_dir / f"{safe_title}.pdf"

        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("ZhH1", parent=styles["Heading1"], fontSize=20, leading=26)
        normal = ParagraphStyle("ZhBody", parent=styles["Normal"], fontSize=11, leading=18)

        # 尝试注册中文字体（失败则回退，可能中文乱码但不报错）
        font_name = "Helvetica"
        try:
            # Windows 常见中文字体
            for candidate in (
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
                "C:/Windows/Fonts/simsun.ttc",
            ):
                if Path(candidate).exists():
                    pdfmetrics.registerFont(TTFont("ZhFont", candidate))
                    font_name = "ZhFont"
                    h1.fontName = font_name
                    normal.fontName = font_name
                    break
        except Exception:  # noqa: BLE001
            logger.warning("中文字体注册失败，PDF 将使用默认字体")

        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        story = [Paragraph(title, h1), Spacer(1, 12)]
        for section in sections:
            story.append(Paragraph(section.title, h1))
            # 简易转义
            text = (section.markdown or "").replace("\n", "<br/>")
            text = re.sub(r"[*#`>]", "", text)
            story.append(Paragraph(text, normal))
            story.append(Spacer(1, 10))
        doc.build(story)
        logger.info("PDF 已生成：%s", file_path)
        return file_path

    async def render_mindmap(self, outline: Outline, output_dir: Path) -> Path:
        """生成 Markmap 兼容的 Markdown 思维导图（层级即标题层级）。"""
        lines: List[str] = [f"# {outline.title}"]
        for section in outline.sections:
            lines.append(f"## {section.title}")
            for sub in section.subsections or []:
                lines.append(f"### {sub.title}")
        safe_title = re.sub(r"[\\/:*?\"<>|]+", "_", outline.title).strip("_ ")
        file_path = output_dir / f"{safe_title}.mindmap.md"
        file_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("思维导图(Markmap) 已生成：%s", file_path)
        return file_path

    @staticmethod
    def _compose_markdown(title: str, sections: List[SectionContent]) -> str:
        parts = [f"# {title}\n"]
        for section in sections:
            parts.append(section.markdown.rstrip() + "\n")
        return "\n".join(parts)
