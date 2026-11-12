# Git-workflow и проверка конфликта (ЛР2)

Git 2.53.0, исходная ветка main. Репозиторий уже создан пользователем, в нём
настроены имя `Daniil` и GitHub noreply email. Повторный `git init` и смена
личности разработчика не требуются. Первая попытка доступа по SSH завершилась
`Permission denied (publickey)`. Пользователь исправил SSH; повторная проверка
`git ls-remote origin HEAD` и последующие push успешны.

## Выполняемый процесс

```bash
git status --short --branch
git --version
git config --get user.name
git config --get user.email
git remote -v
git add <явно выбранные файлы этапа>
git commit -m "docs: describe completed milestone"
git push origin main
git switch -c develop
git add docs/git_workflow.md
git commit -m "docs: document develop workflow and safe conflict resolution"
git push -u origin develop
git switch main
git merge --no-ff develop -m "merge: integrate laboratory 2 Git workflow"
git push origin main
git switch develop
git merge --ff-only main
git push origin develop
```

`commit` сохраняет локальный снимок, `push` публикует коммиты. `merge --no-ff`
сохраняет факт интеграции ветки и может остановиться на конфликте; сначала
проверяют status/diff, затем содержательно разрешают конфликт. `--ff-only`
допускает только безопасное продвижение указателя, иначе завершится ошибкой.
`reset --hard` стирает незакоммиченные изменения, `push --force` переписывает
удалённую историю: они не нужны и не выполнялись. Существующие файлы задания
и `.venv` не удаляются.

## Осмысленные этапы истории

1. Исходный пользовательский Initial commit.
2. Структура, исходные задания и контрольная таблица.
3. ТЗ, роли и критерии приёмки.
4. Диаграмма Use Case и её генератор.
5. DOCX ЛР1 и воспроизводимая сборка отчётов.
6. Отдельное изменение в develop: текущая инструкция и разбор конфликта.

Новые функции идут в feature/lab6, feature/lab7, feature/lab8, минимум по три
содержательных коммита; после проверки сливаются в develop. Отчёты и проверки
также версионируются. После финальной регрессии develop сливается в main.

## Конфликт

Скрипт `scripts/git_evidence.py` создаёт **отдельный учебный репозиторий** в
`.local/git-conflict-*`. Две ветки меняют одну строку README по-разному; merge
действительно останавливается с конфликтом. Сохраняются status, diff с
`<<<<<<< / ======= / >>>>>>>`, итоговое объединённое содержание и успешный commit.
Конфликт не вносится искусственно в рабочую историю проекта. Полный вывод:
`docs/evidence/git_conflict.txt`.

Разрешение выполняется осмысленно: объединяется назначение и порядок учёта
заявок, а не выбирается случайная сторона. Команды запускаются агентом;
самостоятельное повторение студентом по этой инструкции ещё требуется.

## Проверка доступа преподавателя

URL: https://github.com/jnkd0g-the-creator/Reshetov_Daniil_ISIP-308_RequestSystem
Push и `git ls-remote` подтверждают доступ владельца, но не гарантируют
публичность. Анонимная HTTP-проверка репозитория фиксируется отдельно;
для private-репозитория владелец должен пригласить преподавателя.
