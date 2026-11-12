# Трассировка ТЗ → реализация → фактическая проверка

| Требование | Реализация | Доказательство |
|---|---|---|
| FR-01 вход/права | AuthService, API dependency | test_auth_config, test_csrf_enforced, TC-13/14/21/24/25 |
| FR-02 валидация | models.py + references service | TC-06/07/10/11/12/23/27/30, BUG-01 regression |
| FR-03 автор/номер/дата | service + SQL defaults + request_dict | test_create_defaults_and_author, TC-01/18 |
| FR-04 список/карточка | list/get + UI hash routing | TC-02/13/17, roles scope regression |
| FR-05 поиск | CASEFOLD UDF, parameterized LIKE | TC-03/22, test_unicode_search, wildcard/injection |
| FR-06 фильтры/страницы | query → service → repository | TC-03, API limit/offset schemas, curl |
| FR-07 изменение | RequestService.update | TC-04/19, closed/own_new tests |
| FR-08 мастер | RequestService.assign | TC-05, assignment_requires_real_technician |
| FR-09 последовательность | NEXT_STATUS, atomic transaction | TC-05/09/16, full_workflow, idempotent/audit rollback |
| FR-10 права мастера | service scope/status rules | technician_cannot_close, TC-14 |
| FR-11 комментарии/история | comments/history repositories | TC-15/16/29, comment trim, rollback |
| FR-12 архив | service archive + native dialog | TC-20/28, archive_non_destructive/idempotent |
| FR-13 ошибки | app error handlers + UI error region | TC-06/08/23/30, health database failure |
| FR-14 REST/OpenAPI | api.py, typed schemas | 29 curl, OpenAPI/Swagger, API pytest |
| FR-15 health/запуск | health + Docker + volume | clean_start.txt, docker_run.txt; внешний сервер BLOCKED |
| FR-16 пять экранов | HTML/CSS/JS | prototype/screens, application screenshots, TC UI |
| NFR-01 UX/адаптивность | labels, native controls, CSS media | 390px screenshot; личная UX/клавиатурная приёмка студентом остаётся |
| NFR-02 целостность | transactions + FK | SQL foreign_key_check, test_audit_failure_rolls_back |
| NFR-03 p95 | HTTP list на 1000 строк | testing/lab10/performance/result.json, PASS |
| NFR-04 безопасность | PBKDF2/session/CSRF/parameterized SQL | auth/config tests, scope tests; внешний TLS BLOCKED, не пентест |
| NFR-05 сопровождение | 4 слоя + pytest | 57 PASS, 90.38% line coverage |
| NFR-06 повторяемость | README, env, init, Docker | clean venv + real HTTP, container recreate |
| NFR-07 отсутствие секретов | ignored private files + inert public DB | scripts/check_deliverables.py targeted scan |

Инструментальные доказательства не подменяют самостоятельную приёмку студентом.
Всё, что зависит от внешнего сервера/личной записи видео, отмечено BLOCKED.
