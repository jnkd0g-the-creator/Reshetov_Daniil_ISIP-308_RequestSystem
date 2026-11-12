# DOCX-отчёты CoffeeDesk

Все документы открываются в Microsoft Word/LibreOffice. Подготовлены для
Решетова Даниила, ИСИП-308, с явным указанием помощи ИИ и фактических проверок.
Неизвестные сведения об учреждении/преподавателе не выдумывались.

| ЛР | Отчёт |
|---|---|
| 1 · требования | [Lab_01_CoffeeDesk.docx](Lab_01_CoffeeDesk.docx) |
| 2 · Git | [Lab_02_CoffeeDesk.docx](Lab_02_CoffeeDesk.docx) |
| 3 · архитектура | [Lab_03_CoffeeDesk.docx](Lab_03_CoffeeDesk.docx) |
| 4 · интерфейс | [Lab_04_CoffeeDesk.docx](Lab_04_CoffeeDesk.docx) |
| 5 · SQLite | [Lab_05_CoffeeDesk.docx](Lab_05_CoffeeDesk.docx) |
| 6 · функционал | [Lab_06_CoffeeDesk.docx](Lab_06_CoffeeDesk.docx) |
| 7 · REST | [Lab_07_CoffeeDesk.docx](Lab_07_CoffeeDesk.docx) |
| 8 · Docker/деплой | [Lab_08_CoffeeDesk.docx](Lab_08_CoffeeDesk.docx) |
| 9 · тест-кейсы | [Lab_09_CoffeeDesk.docx](Lab_09_CoffeeDesk.docx) |
| 10 · автоматизация/итог | [Lab_10_CoffeeDesk.docx](Lab_10_CoffeeDesk.docx) |

Источники: `../reports_src/labNN.md`. Пересобрать все:
`python scripts/build_reports.py`; выбранные: `python scripts/build_reports.py 1 10`.
Полный AI-журнал вынесен в `../ai_log.md`, не дублирует шаблон в каждом разделе.
Диаграммы/скриншоты вложены в DOCX, а исходные SQL/логи/кейсы доступны в Git.

Рендеринг проверяется `python scripts/render_reports.py` с LibreOffice в
контейнере; промежуточные PDF остаются локально в `.local/reports_pdf`,
`render_validation.json` фиксирует число страниц. ЛР1 проверяется на 5–7 страниц.

**Не скрытые недоделанные пункты методички:** внешний сервер ЛР8 не задан;
самостоятельная ручная приёмка ЛР9 и собственный голос в финальном видео ЛР10
ещё нужны. DOCX честно описывают эти ограничения, а не заявляют фиктивный PASS.
