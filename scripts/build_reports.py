"""Build actual DOCX reports from versioned Markdown, preserving tables/images."""

import argparse
import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
TITLES = ["Анализ предметной области и требования", "Создание и ведение Git-репозитория", "Проектирование архитектуры", "Проектирование пользовательского интерфейса", "Проектирование и создание базы данных", "Разработка функционала системы", "Разработка REST API", "Контейнеризация и деплой", "Функциональное, интеграционное и API-тестирование", "Автоматизация, регрессия и итоговая приёмка"]


def clean(text):
    return text.replace("**", "").replace("`", "")


def markdown(doc, text):
    lines = text.splitlines()
    index = 0
    code = False
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        if line.startswith("```"):
            code = not code
            continue
        if line == "<PAGEBREAK>":
            doc.add_page_break()
        elif line.startswith("!["):
            match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if match:
                path = ROOT / match[2]
                if not path.is_file():
                    raise FileNotFoundError(path)
                doc.add_picture(str(path), width=Inches(5.9))
                doc.add_paragraph(match[1], "Caption")
        elif line.startswith("|"):
            rows = [line]
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(lines[index].strip())
                index += 1
            data = [[clean(c.strip()) for c in row.strip("|").split("|")] for row in rows if not re.match(r"^\|[\s:|\-]+\|$", row)]
            table = doc.add_table(rows=0, cols=len(data[0]))
            table.style = "Light Shading Accent 1"
            for row in data:
                cells = table.add_row().cells
                for cell, value in zip(cells, row):
                    cell.text = value
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(9)
            doc.add_paragraph()
        elif line.startswith("#"):
            count = len(line) - len(line.lstrip("#"))
            doc.add_heading(clean(line.lstrip("# ")), min(count, 3))
        elif line:
            style = "List Bullet" if line.startswith("- ") else None
            p = doc.add_paragraph(clean(line[2:] if style else line), style)
            if code:
                for run in p.runs:
                    run.font.name = "DejaVu Sans Mono"
                    run.font.size = Pt(8)
                p.paragraph_format.space_after = Pt(1)


def build(number, source):
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(1.8)
    section.left_margin, section.right_margin = Cm(2.4), Cm(1.7)
    normal = doc.styles["Normal"]
    normal.font.name = "DejaVu Serif"
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.06
    normal.paragraph_format.space_after = Pt(6)
    for style in ["Heading 1", "Heading 2", "Heading 3"]:
        doc.styles[style].font.name = "DejaVu Sans"
        doc.styles[style].font.color.rgb = RGBColor.from_string("245442")
    doc.styles["Heading 1"].font.size = Pt(18)
    doc.styles["Heading 2"].font.size = Pt(14)
    footer = section.footer.paragraphs[0]
    footer.alignment = 2
    footer.add_run(f"CoffeeDesk · ЛР {number} · ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    for text in ["Дисциплина: «Технологии разработки программного обеспечения»", "Форма обучения: заочная"]:
        doc.add_paragraph(text).alignment = 1
    doc.add_paragraph("\n\n")
    doc.add_heading(f"Лабораторная работа № {number}", 0).alignment = 1
    doc.add_heading(TITLES[number - 1], 1).alignment = 1
    doc.add_paragraph("CoffeeDesk\nСоздание и учёт заявок кофе-баров").alignment = 1
    doc.add_paragraph("\n\nВыполнил: Решетов Даниил\nГруппа: ИСИП-308").alignment = 2
    doc.add_paragraph("Материалы подготовлены с помощью ИИ; фактические инструментальные проверки описаны отдельно от ручной приёмки студентом.")
    doc.add_paragraph("2026").alignment = 1
    doc.add_page_break()
    markdown(doc, source.read_text(encoding="utf-8"))
    doc.core_properties.title = f"CoffeeDesk — Лабораторная работа {number}"
    doc.core_properties.author = "Решетов Даниил / AI-assisted"
    out = ROOT / "docs/reports" / f"Lab_{number:02d}_CoffeeDesk.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("numbers", nargs="*", type=int)
    args = parser.parse_args()
    for source in sorted((ROOT / "docs/reports_src").glob("lab*.md")):
        number = int(source.stem[3:])
        if not args.numbers or number in args.numbers:
            build(number, source)
