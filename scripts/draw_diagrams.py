"""Reproducible project diagrams, editable SVG plus PNG (no cloud service)."""

import argparse
import html
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


class Canvas:
    def __init__(self, width, height, title):
        self.width, self.height = width, height
        self.image = Image.new("RGB", (width, height), "#f7f5f0")
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#f7f5f0"/>']
        self.text(50, 35, title, 32, "#183e35")

    def text(self, x, y, text, size=22, color="#213c35"):
        font = ImageFont.truetype(FONT, size)
        for i, line in enumerate(text.split("\n")):
            self.draw.text((x, y + i * (size + 9)), line, font=font, fill=color)
            self.svg.append(f'<text x="{x}" y="{y + size + i * (size + 9)}" font-family="DejaVu Sans,sans-serif" font-size="{size}" fill="{color}">{html.escape(line)}</text>')

    def line(self, points, color="#91a79f", width=3):
        self.draw.line(points, fill=color, width=width)
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="{width}"/>')

    def box(self, x, y, w, h, title, body="", fill="#ffffff", ellipse=False):
        fn = self.draw.ellipse if ellipse else self.draw.rounded_rectangle
        opts = {} if ellipse else {"radius": 16}
        fn((x, y, x + w, y + h), fill=fill, outline="#557d6e", width=2, **opts)
        if ellipse:
            self.svg.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="#557d6e" stroke-width="2"/>')
        else:
            self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="#557d6e" stroke-width="2"/>')
        self.text(x + 22, y + 19, title, 23)
        if body:
            self.text(x + 22, y + 62, body, 18, "#496459")

    def actor(self, x, y, label):
        self.draw.ellipse((x - 17, y, x + 17, y + 34), outline="#294f40", width=3)
        self.svg.append(f'<circle cx="{x}" cy="{y+17}" r="17" fill="none" stroke="#294f40" stroke-width="3"/>')
        self.line([(x, y + 34), (x, y + 94)], "#294f40")
        self.line([(x - 34, y + 57), (x + 34, y + 57)], "#294f40")
        self.line([(x - 29, y + 125), (x, y + 94), (x + 29, y + 125)], "#294f40")
        self.text(x - 100, y + 137, label, 21)

    def save(self, name):
        base = ROOT / name
        base.parent.mkdir(parents=True, exist_ok=True)
        self.image.save(base.with_suffix(".png"))
        base.with_suffix(".svg").write_text("\n".join(self.svg + ["</svg>"]), encoding="utf-8")


def use_case():
    c = Canvas(1600, 1240, "CoffeeDesk · UML Use Case · четыре роли")
    c.box(430, 100, 730, 1050, "Система учёта заявок кофе-баров", fill="#edf2eb")
    cases = ["UC-01 · Вход и выход", "UC-02 · Создать заявку", "UC-03 · Поиск и просмотр", "UC-04 · Назначить мастера", "UC-05 · Выполнить ремонт", "UC-06 · Принять и закрыть", "UC-07 · Изменить заявку", "UC-08 · Архивировать"]
    mapping = [(220, 170, "Администратор", range(8)), (220, 690, "Оператор", range(7)), (1370, 170, "Исполнитель", [0, 2, 4]), (1370, 690, "Заявитель", [0, 1, 2, 6])]
    for x, y, name, links in mapping:
        edge = 490 if x < 800 else 1100
        for i in links:
            c.line([(x + (40 if x < 800 else -40), y + 60), (edge, 205 + i * 118)], width=2)
    for i, case in enumerate(cases):
        c.box(490, 160 + i * 118, 610, 90, case, ellipse=True)
    for x, y, name, _ in mapping:
        c.actor(x, y, name)
    c.text(55, 1175, "Условия доступа: заявитель — только свои; мастер — назначенные; архив — только закрытые, admin.", 21)
    c.save("docs/architecture/use_case")


def architecture():
    c = Canvas(1500, 970, "CoffeeDesk · слоистая архитектура")
    layers = [
        ("1 · Presentation / controller", "HTML/CSS/JS + FastAPI routes\nHTTP, JSON, cookie, коды, доступ к сервисам"),
        ("2 · Service", "AuthService / RequestService\nПрава, валидация, переходы, атомарные сценарии"),
        ("3 · Repository / data access", "Repository + unit of work\nПараметризованный SQL, чтение и запись"),
        ("4 · Database", "SQLite · schema.sql\nFK, CHECK, UNIQUE, индексы, персистентность"),
    ]
    for i, (title, body) in enumerate(layers):
        y = 115 + i * 195
        c.box(90, y, 930, 150, title, body)
        if i < 3:
            c.line([(545, y + 150), (545, y + 185)], "#29634d", 5)
            c.text(570, y + 152, "↓", 23)
    c.box(1080, 150, 360, 610, "Границы", "Controller: без SQL\nService: без HTML\nRepository: без ролей\nDatabase: без UI\n\nТесты изолируют БД.\nНастройки через env.\nТранзакция на сценарий.\nОдин процесс записи.", fill="#e8eee5")
    c.text(90, 915, "Зависимости направлены вниз; API и веб-интерфейс используют одни бизнес-правила.", 23)
    c.save("docs/architecture/layers")
    c = Canvas(1500, 1000, "CoffeeDesk · диаграмма компонентов")
    c.box(55, 160, 360, 200, "Web UI", "Вход, список, формы\nКарточка, архив\nfetch + CSRF")
    c.box(55, 500, 360, 150, "API client / Swagger", "JSON over HTTP\nOpenAPI contract")
    c.box(535, 260, 400, 200, "FastAPI controllers", "auth, requests, catalogs\nHTTP → service\nединый формат ошибок")
    c.box(535, 565, 400, 200, "Services", "RequestService, AuthService\nРоли, статусы, назначение\nКомментарии и аудит")
    c.box(1060, 565, 380, 200, "Repository", "users, requests, catalogs\ncomments, history, sessions\nпараметризованный SQL")
    c.box(1060, 130, 380, 230, "SQLite", "9 таблиц\nFK + ограничения\nschema.sql / seed.sql\nСохраняемый том Docker")
    for points in [[(415, 260), (535, 330)], [(415, 575), (475, 575), (475, 390), (535, 390)], [(730, 460), (730, 565)], [(935, 660), (1060, 660)], [(1250, 565), (1250, 360)]]:
        c.line(points, "#29634d", 5)
    c.text(60, 885, "Модули предметной области: пользователи · заявки · статусы · категории · бары · комментарии · история.", 22)
    c.save("docs/architecture/components")


def er():
    c = Canvas(1800, 1320, "CoffeeDesk · ER-модель · PK/FK и связи 1:M")
    tables = [
        (55, 125, "Roles", "PK code\nname UNIQUE"),
        (650, 125, "Users", "PK id, username UNIQUE\nFK role_code → Roles\npassword_hash, active, name"),
        (1240, 125, "Sessions", "PK token_hash, csrf_hash\nFK user_id → Users\nexpires_at"),
        (55, 465, "Cafes", "PK id\nname UNIQUE\naddress"),
        (650, 465, "Requests", "PK id, title, description\nFK cafe/category/status\nFK applicant/assignee → Users\npriority, archived, dates"),
        (1240, 465, "Categories / Statuses", "PK Categories.id, name UNIQUE\nPK Statuses.code, name UNIQUE\nДва отдельных справочника"),
        (350, 930, "Comments", "PK id, body, created_at\nFK request_id → Requests\nFK author_id → Users"),
        (1030, 930, "RequestHistory", "PK id, event, old/new, date\nFK request_id → Requests\nFK actor_id → Users"),
    ]
    for a, b, label in [((535, 205), (650, 205), "1:M"), ((1130, 205), (1240, 205), "1:M"), ((535, 575), (650, 575), "1:M"), ((1240, 575), (1130, 575), "1:M"), ((890, 365), (890, 465), "1:M ×2"), ((805, 765), (590, 930), "1:M"), ((1000, 765), (1270, 930), "1:M")]:
        c.line([a, b], "#29634d", 4)
        c.text((a[0] + b[0]) // 2, (a[1] + b[1]) // 2 - 28, label, 18)
    for x, y, title, body in tables:
        c.box(x, y, 480, 240 if y != 465 else 300, title, body)
    c.text(55, 1230, "Также Users 1:M Comments/RequestHistory. NOT NULL, FK RESTRICT; sessions удаляются с пользователем.", 21)
    c.save("docs/database/er")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["use_case", "architecture", "er", "all"])
    args = parser.parse_args()
    for name, func in {"use_case": use_case, "architecture": architecture, "er": er}.items():
        if args.kind in (name, "all"):
            func()
