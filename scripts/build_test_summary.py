"""Derive final quality metrics from real run artifacts, not model estimates."""

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/"testing/lab10"
    run=json.loads((out/"run_metadata.json").read_text())
    cases=json.loads((ROOT/"testing/lab9/results.json").read_text())
    performance=json.loads((out/"performance/result.json").read_text())
    passed=run["tests"]-run["failures"]-run["errors"]-run["skipped"]
    rate=cases["PASS"]/(cases["PASS"]+cases["FAIL"])*100
    with (ROOT/"testing/lab9/test_cases.csv").open(encoding="utf-8-sig",newline="") as stream:
        manual=sum(row["manual_status"]=="BLOCKED" for row in csv.DictReader(stream,delimiter=";"))
    text=f"""# Итоговый отчёт о тестировании CoffeeDesk

Дата: {run['date']}. Версия приложения 1.0.0, тестировавшийся commit
`{run['commit']}`. SHA256 исходников `src/coffeedesk`:
`{run['source_sha256']}`. Незакоммиченные исходники: {run['source_uncommitted']}.
Документационные коммиты после этой версии не меняют исходный продукт;
совпадение SHA256 связывает браузерную регрессию и pytest с одной реализацией.

## Метрики (не смешивать автоматизацию с ручной приёмкой)

| Набор | Всего | Выполнено | PASS | FAIL | BLOCKED |
|---|---|---|---|---|---|
| Инструментальные кейсы ЛР9 | {cases['total']} | {cases['total']} | {cases['PASS']} | {cases['FAIL']} | {cases['BLOCKED']} |
| Личная ручная проверка студентом | {manual} | 0 | 0 | 0 | {manual} |
| pytest, весь регрессионный набор | {run['tests']} | {run['tests']} | {passed} | {run['failures']+run['errors']} | {run['skipped']} |
| curl на изолированном HTTP-стенде | 29 | 29 | 29 | 0 | 0 |

Инструментальный показатель успешности: PASS/(PASS+FAIL)×100 = {rate:.1f}%.
BLOCKED не входят в знаменатель. Человеческие проверки не выдаются за пройденные.
Первоначальный браузерный прогон 29/1 сохранён в `../lab9/initial_failure/`;
после исправления ожидания повторены все 30, а не исправлен один статус таблицы.

Покрытие **строк Python**: {run['coverage_percent']:.2f}% (`coverage.json/xml`).
Не означает покрытие JS, всех бизнес-комбинаций, внешнего TLS или отсутствие
ошибок. CLI отдельно запускался из нового venv/Docker, но subprocess-проверки
не входят в измерение строк основного pytest-процесса. Warning устаревшего
алиаса AnyIO/Starlette отражён в полном логе; он не является FAIL продукта.

## Дефекты

| Тип / важность | Найдено | Исправлено и перепроверено | Открыто |
|---|---|---|---|
| Продукт BUG-01 / Medium | 1 | 1 | 0 |
| Продукт Critical/High/Low | 0 | 0 | 0 |
| Тестовый инструмент TEST-01 / Low (отдельно) | 1 | 1 | 0 |

BUG-01: JSON bool принимался за ID; строгий int даёт 422 и не создаёт строку.
Доказательства до/после сохранены; регрессия параметризована на оба FK.
TEST-01: ожидание badge старой страницы; исправлено ожиданием heading, продукт
не менялся. Известных открытых **найденных** продуктовых дефектов нет;
это не утверждение, что в системе нет иных ошибок.

## Производительность

NFR-03: {performance['database_rows']} строк, {performance['http_requests']}
последовательных HTTP, limit={performance['limit']}, p95 nearest-rank
**{performance['p95_ms']:.2f} мс** при пороге 1000 мс: {performance['result']}.
Это локальная проверка на текущей машине, не SLA и не тест конкурентной нагрузки.

## Внешние и личные ограничения

1. Удалённый деплой — BLOCKED: согласованный сервер/адрес не указан.
   Локальный контейнер 127.0.0.1:8001 healthy и сохраняет данные при recreate.
2. Самостоятельные ручные действия студентом — BLOCKED: агент выполнил
   браузерную/HTTP-автоматизацию; шаги для человека находятся в ЛР9 CSV.
3. Обязательное видео с **голосом студента** — BLOCKED. Есть реальный
   технический MP4 без аудио, 63.12 с; это репетиция, не полная сдача.
4. Не проверялись промышленный пентест, DNS/TLS внешнего сервера, реальная
   многопользовательская нагрузка, email/вложения/платежи (последние вне ТЗ).
5. Python 3.10 выбран пользователем; для долгосрочного production следует
   согласовать поддерживаемый Python и обновление/аудит зависимостей.

## Вывод

Программная часть готова к **локальной** демонстрации. Весь автоматический
набор проходит, найденный дефект исправлен, факты подтверждены логами.
Полную сдачу лабораторных 8–10 нельзя объявить завершённой до выполнения
трёх BLOCKED-пунктов. Инструкции, AI-журнал и DOCX-отчёты подготовлены.
"""
    (out/"test_summary.md").write_text(text,encoding="utf-8")
    excerpt=(out/"test_run.txt").read_text().splitlines()
    (out/"test_run_excerpt.txt").write_text("Фрагмент фактического полного журнала; оригинал: testing/lab10/test_run.txt\n\n"+"\n".join(excerpt[-23:])+"\n")
    print(f"Quality summary derived: {passed} pytest PASS, {rate:.1f}% instrumented case success, {run['coverage_percent']:.2f}% line coverage")


if __name__=="__main__":
    main()
