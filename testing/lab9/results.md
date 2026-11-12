# Фактические результаты инструментального прогона

Это браузерная/HTTP-автоматизация агента, не ручной прогон студентом.

| ID | Цель | Статус | Факт |
|---|---|---|---|
| TC-01 | Создание формы | PASS | Создана форма, id=13; строка реально в SQLite. |
| TC-02 | Список и карточка | FAIL | Error: LocatorAssertions.to_be_visible: Error: strict mode violation: locator(".badge.new") resolved to 6 elements:
    1) <span class="badge new">Новая</span> aka get_by_role("row", name="CB-00013").locator("span").nth(1)
    2) <span class="badge new">Новая</span> aka get_by_role("row", name="CB-00009").locator("span").nth(1)
    3) <span class="badge new">Новая</span> aka get_by_role("row", name="CB-00007").locator("span").nth(1)
    4) <span class="badge new">Новая</span> aka get_by_role("row", name="CB-00005").locator("span").nth(1)
    5) <span class="badge new">Новая</span> aka get_by_role("row", name="CB-00002").locator("span").nth(1)
    6) <span class="badge new">Новая</span> aka get_by_role("row", name="CB-00001").locator("span").nth(1)

Call log:
  - Expect "to_be_visible" with timeout 5000ms
  - waiting for locator(".badge.new")
 |
| TC-03 | Поиск и пересечение фильтров | PASS | Кириллица верхнего регистра + статус + категория: одна нужная строка. |
| TC-04 | Редактирование | PASS | Изменение видно в карточке и SQLite. |
| TC-05 | Назначение и смена статуса | PASS | Мастер 1 назначен, статус В работе. |
| TC-06 | Пустая тема | PASS | Браузер остановил пустое обязательное поле, строка не создана. |
| TC-07 | BUG-01: неверный тип ID | PASS | 422, число строк не изменилось; BUG-01 не воспроизводится. |
| TC-08 | Отсутствующая заявка | PASS | UI показал понятную ошибку, HTTP 404. |
| TC-09 | Запрещённый скачок статуса | PASS | 409, статус остался in_progress. |
| TC-10 | Минимум темы | PASS | Тема 3 символа сохранена. |
| TC-11 | Максимум темы | PASS | 120 символов сохранены без усечения. |
| TC-12 | Максимум описания | PASS | 4000 символов сохранены. |
| TC-13 | Заявитель видит только свои | PASS | В UI нет чужой CB-00002; все API-объекты автора 5. |
| TC-14 | Исполнителю запрещено создание | PASS | Кнопки создания нет; прямой POST тоже запрещён 403. |
| TC-15 | Форма + БД + аудит | PASS | UI создал id=17; ровно одна история created/new в SQLite. |
| TC-16 | Статус + БД + история | PASS | UI Выполнена = SQLite done = последняя история done. |
| TC-17 | GET списка | PASS | 200, JSON-массив 17 объектов. |
| TC-18 | POST и Location | PASS | 201, id=18, корректный Location. |
| TC-19 | PATCH и повторное чтение | PASS | PATCH 200, повторный GET priority=urgent. |
| TC-20 | DELETE-архив | PASS | 204 без тела; archived=1, бизнес-строка не удалена. |
| TC-21 | CSRF | PASS | 403 csrf_failed без корректного заголовка. |
| TC-22 | Пустой поиск и сброс | PASS | Пустое состояние понятно, сброс возвращает строки. |
| TC-23 | Пробелы и сохранение формы | PASS | Сервер отклонил тему после trim, введённое описание не потерялось. |
| TC-24 | Без авторизации | PASS | 401 unauthenticated, данных заявок нет. |
| TC-25 | Скрытие чужого объекта | PASS | Чужая существующая заявка скрыта тем же 404, что отсутствующая. |
| TC-26 | HTML как текст | PASS | Спецсимволы сохранены, отрисованы текстом; img/обработчик не исполнены. |
| TC-27 | Превышение описания | PASS | 422 при 4001 символе. |
| TC-28 | Отмена опасного действия | PASS | Диалог закрыт, archived=0; отмена не меняет данные. |
| TC-29 | Комментарий | PASS | Комментарий отображён и однажды записан в SQLite. |
| TC-30 | Недопустимые значения | PASS | Неизвестные priority и status отклонены 422. |

{"total": 30, "PASS": 29, "FAIL": 1, "BLOCKED": 0, "manual_review": "BLOCKED (not performed by student)", "remote": "BLOCKED"}
