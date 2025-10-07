# build_html.py
# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# ====== HTML генераторы ======

IMAGE_PREFIX = "https://raw.githubusercontent.com/FFF2115/ga56d7806abs7d/refs/heads/main/"

def generate_header(title: str,
                    description: str = "",
                    params: List[Dict[str, str]] | None = None,
                    images: List[Dict[str, str]] | None = None) -> str:
    """
    Генерация блока header-section.
    title: заголовок (str)
    description: описание (str)
    params: список словарей {"Диапазон...": "текст"} (опционально)
    images: список словарей {"src": "...", "alt": "..."} (опционально)
    """
    html = []
    html.append('<div class="header-section">')
    html.append('  <div class="header-text">')

    # блок с заголовком и описанием
    html.append('    <div class="param-block">')
    html.append(f'      <div class="header-title">{title}</div>')
    if description:
        html.append(f'      <div>{description}</div>')
    html.append('    </div>')

    # блок с параметрами (если есть)
    if params:
        html.append('    <div class="param-block">')
        for k, v in params.items():
            html.append(f'      <div><span>{k}:</span> {v}</div>')
        html.append('    </div>')

    html.append('  </div>')  # .header-text

    # блок с картинками (если есть)
    if images:
        html.append('  <div class="header-images">')
        html.append('    <div class="images-label">образец прибора</div>')
        html.append('    <div class="images-wrapper">')
        for img in images:
            html.append(f'      <img src="{IMAGE_PREFIX + img}">')
        html.append('    </div>')
        html.append('  </div>')

    html.append('</div>')
    return "\n".join(html)


def format_cell(value: Any) -> str:
    """Форматирует ячейку: строка/число/список строк."""
    if isinstance(value, list):
        return '<div class="cell-list">' + "".join(f"<div>{v}</div>" for v in value) + "</div>"
    return str(value)


def generate_html_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
    """
    data: список словарей с параметрами
    columns: список столбцов (в нужном порядке)
    """
    if not data:
        return "<!-- empty table -->"

    n = len(data)
    rowspan_map = {col: [1] * n for col in columns}

    # считаем rowspan по столбцам
    for col in columns:
        i = 0
        while i < n:
            j = i + 1
            vi = data[i].get(col)
            while j < n and data[j].get(col) == vi:
                rowspan_map[col][i] += 1
                rowspan_map[col][j] = 0
                j += 1
            i = j

    # строим HTML
    html = [
        "<table>",
        "  <thead>",
        "    <tr>" + "".join(f"<th>{c}</th>" for c in columns) + "</tr>",
        "  </thead>",
        "  <tbody>",
    ]

    for row_idx, row in enumerate(data):
        html.append("    <tr>")
        for col_idx, col in enumerate(columns):
            if rowspan_map[col][row_idx] > 0:
                span = f' rowspan="{rowspan_map[col][row_idx]}"' if rowspan_map[col][row_idx] > 1 else ""
                # добавляем класс только первой колонке
                cls = ' class="br_column"' if col_idx == 0 else ""
                html.append(f'      <td{span}{cls}>{format_cell(row.get(col, ""))}</td>')
        html.append("    </tr>")

    html.append("  </tbody>")
    html.append("</table>")
    return "\n".join(html)


# ====== Вспомогательные функции ======

ALLOWED_COLUMNS = [
    "Модель",
    "Диаметр",
    "Пределы давления",
    "Резьба",
    "Класс точности",
    "Степень IP",
    "Климат",
    "Вибро защита",
]

def infer_columns(all_rows: List[Dict[str, Any]],
                  allowed_order: List[str] = ALLOWED_COLUMNS) -> List[str]:
    """Определяет итоговый порядок столбцов:
    оставляем только поля из allowed_order, которые реально встречаются.
    """
    present = set()
    for r in all_rows:
        present.update(r.keys())

    return [c for c in allowed_order if c in present]



def wrap_page(content: str, title: str = "Каталог приборов") -> str:
    """Оборачивает контент в HTML-страницу, используя template.html"""
    template_path = Path("static/template.html")
    template = template_path.read_text(encoding="utf-8")

    # простая замена плейсхолдеров
    page = template.replace("{{ title }}", title).replace("{{ content }}", content)
    return page


def build_sections_from_json(js: Dict[str, Any]) -> str:
    """Создаёт большой HTML из структуры JSON."""
    items = js
    if not items:
        return "<p>Нет данных.</p>"

    pieces: List[str] = []
    for item in items:
        device = item.get("device", "Без названия")
        description = item.get("description", "")
        params = item.get("params")  # опционально
        images = item.get("images")  # опционально

        # данные таблицы
        rows: List[Dict[str, Any]] = item.get("data", [])
        if not isinstance(rows, list):
            rows = []

        # колонки: либо указаны явно, либо выводим по умолчанию/инференсу
        columns = item.get("columns")
        if not columns:
            columns = infer_columns(rows)

        header_html = generate_header(
            title=device,
            description=description,
            params=params,
            images=images
        )
        table_html = generate_html_table(rows, columns)

        section_html = f'<div class="page-content"><section class="item">\n{header_html}\n\n{table_html}\n</section></div>'
        pieces.append(section_html)

    return "\n\n".join(pieces)


# ====== entrypoint ======

def process(in_json: str, out_html: str):
    input_path = Path(in_json)

    if not input_path.exists():
        print(f"Файл не найден: {input_path}")
        sys.exit(1)

    with input_path.open("r", encoding="utf-8") as f:
        js = json.load(f)

    if not isinstance(js, list):
        print("Ожидался список в JSON (массив).")
        sys.exit(1)

    # Строим все секции сразу
    all_sections_html = build_sections_from_json(js)
    page = wrap_page(all_sections_html, title="Каталог приборов")

    out_path = Path(out_html)
    out_path.write_text(page, encoding="utf-8")
    print(f"Создан общий файл: {out_path.resolve()}")

