# ЛР10 · воспроизводимый регрессионный набор

Из корня, Python 3.10 и проектное .venv:

```bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python scripts/run_tests.py
```

Одна последняя команда запускает **весь** pytest-набор, сохраняет полный вывод
`test_run.txt`, JUnit XML, coverage JSON/XML и метаданные версии/хешей исходников.
Для быстрого запуска без отчёта: `python -m pytest tests testing/lab10 -q`.
Существующий сервер, сеть, Docker и рабочая БД не требуются.
Каждый тест получает tmp_path SQLite; секрет теста генерируется в памяти.

## Критические сценарии и почему автоматизированы

| Сценарий ЛР9 | Автотест | Причина |
|---|---|---|
| Создание и автор | test_create_defaults_and_author, test_api_create_success_and_location | Частая операция, проверяемые ID/статус/Location |
| Чтение/изменение | test_persistent_update_new_connection, test_patch_data_persist | Ошибки сохранения не всегда видны без повторного чтения |
| Поиск/фильтры | test_unicode_search_and_combined_filters | Риск SQLite NOCASE для кириллицы |
| Назначение и статусы | test_full_status_workflow, test_start_requires_assignee | Общая бизнес-цепочка, нельзя пропускать условия |
| Архив | test_archive_is_non_destructive_and_idempotent | Риск необратимой потери данных |
| BUG-01 | test_regression_bug01_strict_integer_ids, tests/test_validation_regression.py | Реальный исправленный дефект; bool должен дать 422 |
| Роли/CSRF | test_regression_role_scope_and_direct_http, test_csrf_enforced_even_with_cookie | Прямой HTTP обходит скрытые кнопки |
| Аудит/транзакция | test_audit_failure_rolls_back_request | Fault injection выявляет неатомарную запись |

57 параметризованных запусков: ≥3 бизнес-проверки, ≥3 API, ≥2 негативных/валидации,
≥2 регрессии (BUG-01 и рискованные права/архив/поиск). Файлы test_business.py,
test_api.py, test_auth_config.py разделяют компоненты; conftest.py содержит
подготовку/изоляцию. Два ранних smoke и регрессия ЛР9 также включены.

**Способность выявить ошибку:** перед исправлением BUG-01 тот же запрос
`cafe_id=true` реально дал 201 и 13 строк вместо 422 и 12; исходный FAIL
в `../lab9/evidence/BUG-01_before_fix.*`. Assert кода 422 и количества строк
поймает повторное ослабление типа. Fault injection подменяет только метод
в рамках pytest monkeypatch; продукт не оставляется сломанным.

Человеческую оценку UX и голосовую демонстрацию не автоматизируем: сценарий
и техническая запись не заменяют собственную приёмку студента.
Первый сбой TC-02 был ошибкой ожидания теста, не продукта; сохранён и исправлен
ожиданием заголовка, а не ослаблением assert. Детали в docs/ai_log.md.

Покрытие измеряется **по строкам Python**, не по всем сочетаниям ролей и не
по UI/JS. Coverage не доказывает отсутствие дефектов; незапущенный subprocess
CLI по методике pytest-cov уменьшает общий процент. Внешний стенд и голосовое
видео остаются BLOCKED до реального выполнения.
