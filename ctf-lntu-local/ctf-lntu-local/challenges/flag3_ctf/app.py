import os
import queue
import threading
import time
from flask import Flask, request, redirect
from ui import page, setup, esc

PORT = int(os.environ.get("PORT", 5000))
FLAG = "CTF{xss_st0r3d_4dm1n_c00k13_st34l}"
app = Flask(__name__)
setup(app)

BRAND, ACCENT = "LNTU Cyber Blog", "#a78bfa"
NAV = (("/", "Блог"), ("/inbox", "Вхідні дані"))
posts = [{"title": "Ласкаво просимо!", "content": "Перша стаття студентського кібер-блогу ЛНТУ."}]
inbox = []  # те, що надіслали на /collect
visit_queue = queue.Queue()


def sanitize(text):
    # «Захист»: прибираємо тег <script> (регістрозалежно) — легко обійти
    return text.replace("<script>", "").replace("</script>", "")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = esc(request.form.get("title", "Без назви"))[:80]
        content = sanitize(request.form.get("content", ""))[:2000]
        posts.append({"title": title, "content": content})
        del posts[:-12]
        visit_queue.put(time.time())  # модератор (бот) перевірить новий пост
        return redirect("/")
    items = "".join(
        f'<div class="card" style="margin-bottom:14px"><h3>{p["title"]}</h3><div>{p["content"]}</div></div>'
        for p in reversed(posts)
    )
    body = f"""<h1>LNTU Cyber Blog</h1>
    <p class="lead">Діліться дослідженнями. Кожну нову статтю переглядає модератор (адміністратор).</p>
    <form method="POST" class="card accent">
      <label>Заголовок</label><input name="title" required>
      <label>Текст статті (підтримується HTML)</label><textarea name="content" required></textarea>
      <button>Опублікувати</button></form>
    <h2>Статті</h2>{items}"""
    return page("Блог", body, BRAND, ACCENT, NAV)


@app.get("/collect")
def collect():
    inbox.append({"t": time.strftime("%H:%M:%S"), "data": request.args.get("d", "")[:500],
                  "ip": request.remote_addr})
    del inbox[:-30]
    return "", 204


@app.get("/inbox")
def show_inbox():
    rows = "".join(f"<tr><td>{i['t']}</td><td>{esc(i['ip'])}</td><td><code>{esc(i['data'])}</code></td></tr>"
                   for i in reversed(inbox)) or '<tr><td colspan="3" class="muted">Поки порожньо</td></tr>'
    body = f"""<h1>Вхідні дані</h1>
    <p class="lead">Вбудований приймач: запит на <code>/collect?d=…</code> потрапляє сюди. Зовнішній сервер не потрібен.</p>
    <table><tr><th>Час</th><th>IP</th><th>Дані</th></tr>{rows}</table>"""
    return page("Вхідні дані", body, BRAND, ACCENT, NAV)


def admin_bot():
    """Адмін-бот: відкриває блог у headless-Chromium з кукою admin_session."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # локальний запуск без playwright
        print("[bot] playwright недоступний:", e, flush=True)
        return
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        while True:
            visit_queue.get()
            time.sleep(0.5)
            while not visit_queue.empty():
                visit_queue.get_nowait()
            try:
                ctx = browser.new_context()
                ctx.add_cookies([{"name": "admin_session", "value": FLAG, "url": f"http://127.0.0.1:{PORT}"}])
                pg = ctx.new_page()
                pg.goto(f"http://127.0.0.1:{PORT}/", timeout=8000)
                pg.wait_for_timeout(3000)
                ctx.close()
                print("[bot] модератор переглянув блог", flush=True)
            except Exception as e:
                print("[bot] помилка:", e, flush=True)


if __name__ == "__main__":
    if os.environ.get("NO_BOT") != "1":
        threading.Thread(target=admin_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
