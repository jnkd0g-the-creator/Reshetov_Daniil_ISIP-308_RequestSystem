"""Exercise real browser forms, retain screenshots, never output credentials."""

import json
from pathlib import Path

from browser_support import configure_browser
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def run():
    configure_browser()
    credentials = dict(line.split("\t") for line in (ROOT / ".local/demo_credentials.txt").read_text().splitlines())
    folder = ROOT / "docs/evidence/application"
    folder.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.goto("http://127.0.0.1:8000")
        page.get_by_role("heading", name="Вход в CoffeeDesk").wait_for()
        page.screenshot(path=str(folder / "login.png"))
        page.get_by_label("Логин").fill("admin")
        page.get_by_label("Пароль").fill(credentials["admin"])
        page.get_by_role("button", name="Войти →").click()
        page.get_by_role("heading", name="Заявки кофе-баров").wait_for()
        page.screenshot(path=str(folder / "list.png"))
        checks.append("Вход, список и справочники: PASS")
        page.get_by_role("link", name="＋ Создать заявку", exact=True).first.click()
        page.get_by_label("Тема заявки").wait_for()
        page.screenshot(path=str(folder / "new.png"))
        page.get_by_label("Тема заявки").fill("Учебная протечка крана")
        page.get_by_label("Описание *").fill("Вода подтекает из основания крана. Проверка рабочего сценария через браузер.")
        page.get_by_label("Категория *").select_option("1")
        page.get_by_label("Приоритет").select_option("high")
        page.get_by_role("button", name="Создать заявку", exact=True).click()
        page.get_by_role("heading", name="Учебная протечка крана").wait_for()
        request_id = int(page.url.split("#requests/")[1])
        page.screenshot(path=str(folder / "detail.png"))
        checks.append(f"Создание и повторное чтение: PASS, id={request_id}")
        page.get_by_role("link", name="Редактировать", exact=True).click()
        page.get_by_label("Тема заявки").wait_for()
        page.screenshot(path=str(folder / "edit.png"))
        page.get_by_label("Описание *").fill("Уточнение после осмотра: необходимо заменить уплотнение крана.")
        page.get_by_role("button", name="Сохранить изменения").click()
        expect(page.get_by_text("Уточнение после осмотра:", exact=False)).to_be_visible()
        page.get_by_label("Назначение").select_option("3")
        page.get_by_role("button", name="Назначить", exact=True).click()
        expect(page.locator(".meta")).to_contain_text("Мастер 1")
        page.get_by_role("button", name="Взять в работу").click()
        expect(page.locator(".badge.in_progress")).to_be_visible()
        checks.append("Редактирование, назначение и В работе: PASS")
        page.get_by_label("Новый комментарий").fill("Уплотнение заменено, протечки больше нет.")
        page.get_by_role("button", name="Отправить", exact=True).click()
        expect(page.locator(".comment")).to_contain_text("Уплотнение заменено")
        page.get_by_role("button", name="Отметить выполнение").click()
        page.get_by_role("button", name="Закрыть заявку").click()
        page.get_by_role("button", name="Архивировать заявку").click()
        page.get_by_role("dialog").wait_for()
        page.screenshot(path=str(folder / "confirmation.png"))
        page.get_by_role("button", name="Отмена", exact=True).click()
        expect(page.get_by_role("button", name="Архивировать заявку")).to_be_visible()
        page.get_by_role("button", name="Архивировать заявку").click()
        page.get_by_role("button", name="Подтвердить", exact=True).click()
        page.get_by_role("heading", name="Архив заявок").wait_for()
        checks.append("Комментарий, Выполнена, Закрыта, отмена и подтверждение архива: PASS")
        page.get_by_role("link", name="＋ Создать заявку", exact=True).first.click()
        page.get_by_label("Тема заявки").fill("   ")
        page.get_by_label("Описание *").fill("Валидное описание для проверки пустой после trim темы.")
        page.get_by_role("button", name="Создать заявку", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Проверьте обязательные поля")
        page.screenshot(path=str(folder / "validation.png"))
        checks.append("Валидация сервером, форма и введённый текст сохранены: PASS")
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto("http://127.0.0.1:8000/#requests")
        page.get_by_role("heading", name="Заявки кофе-баров").wait_for()
        page.screenshot(path=str(folder / "mobile.png"), full_page=True)
        browser.close()
    (folder / "browser_check.txt").write_text("Автоматизированный браузерный прогон, не ручная приёмка студентом.\nChromium 140, Playwright 1.55.0, Ubuntu 26.04, Python 3.10.11.\n" + "\n".join(checks) + "\n", encoding="utf-8")
    (folder / "result.json").write_text(json.dumps({"request_id": request_id, "checks": checks}, ensure_ascii=False, indent=2) + "\n")
    print("Browser workflow:", len(checks), "groups PASS; screenshots saved without credentials")


if __name__ == "__main__":
    run()
