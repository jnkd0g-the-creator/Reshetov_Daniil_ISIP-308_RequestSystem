"""Record real UI/API/test execution, explicitly a silent rehearsal, not student voice."""

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import imageio_ffmpeg
from browser_support import configure_browser
from playwright.sync_api import expect, sync_playwright
from test_environment import isolated_server

ROOT = Path(__file__).resolve().parents[1]


def main():
    configure_browser()
    output = ROOT / "docs/demo"
    output.mkdir(parents=True, exist_ok=True)
    private = ROOT / ".local/video"
    private.mkdir(parents=True, exist_ok=True)
    state = {"output": "", "running": False, "returncode": None}

    def tests():
        command = [sys.executable, "scripts/run_tests.py"]
        state["output"] = "$ python scripts/run_tests.py\n"
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            state["output"] += line
        process.wait()
        state["returncode"] = process.returncode
        state["running"] = False

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/state":
                body = json.dumps(state).encode()
                content_type = "application/json"
            else:
                body = ('<!doctype html><html lang="ru"><meta charset="utf-8"><style>body{margin:28px;background:#102b20;color:#e5efdf;font:16px monospace}h1{font:28px Arial}button{padding:12px 22px;font:18px Arial}pre{white-space:pre-wrap;height:620px;overflow:auto;line-height:1.35;padding:16px;background:#0a1c14}.note{color:#d6b17f}</style><h1>Реальный запуск регрессионного набора CoffeeDesk</h1><p class="note">Техническая запись без голоса · для финальной сдачи студент записывает собственный комментарий.</p><button id="start" onclick="fetch(\'/start\',{method:\'POST\'});this.disabled=true">Запустить все тесты</button><pre id="terminal"></pre><p id="result">Готов к запуску</p><p>BUG-01: assert HTTP 422 и неизменного числа строк ловит повторное принятие boolean как ID.</p><script>setInterval(async()=>{const r=await fetch(\'/state\');const s=await r.json();const t=document.querySelector(\'#terminal\');t.textContent=s.output;t.scrollTop=t.scrollHeight;document.querySelector(\'#result\').textContent=s.running?\'Тесты выполняются…\':s.returncode===null?\'Готов к запуску\':\'Завершено. Код выхода: \'+s.returncode;},250)</script></html>').encode()
                content_type = "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path == "/start" and not state["running"] and state["returncode"] is None:
                state["running"] = True
                threading.Thread(target=tests, daemon=True).start()
            self.send_response(204)
            self.end_headers()

    terminal = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=terminal.serve_forever, daemon=True).start()
    try:
        with isolated_server(private / "environment") as (base, _, credentials, _), sync_playwright() as p:
            browser = p.chromium.launch(slow_mo=200)
            # Authenticate through the context API before creating a recorded page.
            context = browser.new_context(viewport={"width":1440,"height":900}, record_video_dir=str(private), record_video_size={"width":1440,"height":900})
            auth = context.request.post(base + "/auth/login", data={"username":"admin","password":credentials["admin"]})
            assert auth.status == 200
            csrf = auth.json()["csrf_token"]
            context.add_init_script("if(location.origin==="+json.dumps(base)+"){sessionStorage.setItem('coffee_csrf',"+json.dumps(csrf)+")}")
            page = context.new_page()

            def caption(text, milliseconds=1600):
                page.evaluate("text => {let n=document.getElementById('demo-caption');if(!n){n=document.createElement('div');n.id='demo-caption';n.style='position:fixed;bottom:10px;left:15px;right:15px;padding:12px 18px;background:#122d22ee;color:#f9edce;border-radius:8px;font:17px Arial;z-index:10000;pointer-events:none';document.body.append(n)}n.textContent=text}", text)
                page.wait_for_timeout(milliseconds)

            page.goto(base)
            page.get_by_role("heading",name="Заявки кофе-баров").wait_for()
            caption("CoffeeDesk · Решетов Даниил · ИСИП-308. Техническая запись агента БЕЗ голосового комментария студента.",3500)
            page.get_by_role("link",name="＋ Создать заявку",exact=True).first.click()
            page.get_by_label("Тема заявки").fill("Починить кран в кофе-баре Центр")
            page.get_by_label("Описание *").fill("После начала смены заметили течь у основания крана рабочей мойки. Требуется замена уплотнения.")
            page.get_by_label("Приоритет").select_option("high")
            caption("Создаём настоящую заявку: бар Центр, категория Сантехника, высокий приоритет.",2500)
            page.get_by_role("button",name="Создать заявку",exact=True).click()
            page.get_by_role("heading",name="Починить кран в кофе-баре Центр").wait_for()
            request_id = int(page.url.split("#requests/")[1])
            caption("Заявка получила номер и сохранена в SQLite. Открываем редактирование.")
            page.get_by_role("link",name="Редактировать",exact=True).click()
            page.get_by_label("Описание *").fill("Место течи уточнено: соединение у основания крана. Заменить уплотнение, проверить герметичность.")
            page.get_by_role("button",name="Сохранить изменения").click()
            page.get_by_label("Назначение").select_option("3")
            page.get_by_role("button",name="Назначить",exact=True).click()
            expect(page.locator(".meta")).to_contain_text("Мастер 1")
            caption("Оператор или администратор назначает действующего мастера. История сохраняется атомарно.",2500)
            page.get_by_role("button",name="Взять в работу").click()
            expect(page.locator(".badge.in_progress")).to_be_visible()
            caption("Новая → В работе. Без исполнителя этот переход был бы запрещён.",2300)
            page.get_by_label("Новый комментарий").fill("Уплотнение заменено. Течь устранена, рабочая мойка исправна.")
            page.get_by_role("button",name="Отправить",exact=True).click()
            expect(page.get_by_text("Уплотнение заменено. Течь устранена, рабочая мойка исправна.",exact=True)).to_be_visible()
            page.get_by_role("button",name="Отметить выполнение").click()
            page.get_by_role("button",name="Закрыть заявку").click()
            page.reload()
            expect(page.locator(".badge.closed")).to_be_visible()
            caption("Выполнена → Закрыта. Перезагрузка подтверждает сохранение данных.",2500)
            page.goto(base+"/#requests")
            page.get_by_label("Поиск по номеру, теме или описанию").fill("КРАН")
            page.get_by_role("button",name="Найти",exact=True).click()
            expect(page.locator("tbody")).to_contain_text("Починить кран")
            caption("Поиск кириллицы работает без учёта регистра. Фильтры применяются совместно.",2300)
            response = page.goto(base+"/health")
            assert response.status == 200
            caption("Реальный GET /health → HTTP 200: приложение и база доступны.",3000)
            response = page.goto(base+"/requests/99999999")
            assert response.status == 404
            caption("Реальный GET отсутствующей заявки → HTTP 404, единый формат ошибки.",3000)
            page.goto(f"http://127.0.0.1:{terminal.server_port}")
            page.get_by_role("button",name="Запустить все тесты").click()
            expect(page.locator("#result")).to_have_text("Завершено. Код выхода: 0",timeout=120000)
            caption("Весь набор реально выполнен сейчас. Подробные результаты и покрытие сохранены в testing/lab10.",4500)
            page.goto(base+f"/#requests/{request_id}")
            expect(page.locator(".badge.closed")).to_be_visible()
            caption("Готовы заявки, роли, поиск, история, REST и локальный Docker. Внешний деплой, ручная приёмка и голос студента ещё требуются.",4500)
            video = page.video
            context.close()
            raw = Path(video.path())
            browser.close()
        target = output / "coffeedesk_rehearsal.mp4"
        command = [imageio_ffmpeg.get_ffmpeg_exe(),"-y","-i",str(raw),"-c:v","libx264","-preset","fast","-crf","24","-pix_fmt","yuv420p","-movflags","+faststart",str(target)]
        result = subprocess.run(command,capture_output=True,text=True)
        assert result.returncode == 0, result.stderr
        info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-i",str(target)],capture_output=True,text=True)
        (output / "video_metadata.txt").write_text(info.stderr)
        assert state["returncode"] == 0
        print("Recorded actual UI, HTTP and full live pytest run. Silent rehearsal MP4; student voice still required.")
    finally:
        terminal.shutdown()
        terminal.server_close()


if __name__ == "__main__":
    main()
