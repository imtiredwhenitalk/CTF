"""NullByte Forum — навчальний CTF із stored XSS.

Гравець залишає пост на форумі, а «адмін-бот» (headless Chromium)
відкриває цей пост під адмінською сесією. Флаг лежить лише в
адмін-панелі, тому його треба викрасти саме через XSS.

Запуск:
    python run.py                # локально (бот працює, якщо є Playwright)
    docker compose up --build    # повний варіант із ботом у контейнері

УВАГА: це навмисно вразливий застосунок. Не виставляй його в інтернет.
"""
import os
import queue
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("DB_PATH", BASE_DIR / "data" / "forum.db"))

FLAG = os.environ.get("CTF_FLAG") or "CTF{st0r3d_x55_1n_4dm1n_b07}"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
# Якщо пароль не заданий — генеруємо випадковий. Бот знає його,
# а гравець — ні. Саме тому без XSS до адмінки не потрапити.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(18)

APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
BOT_ENABLED = os.environ.get("BOT_ENABLED", "1") != "0"
BOT_COOLDOWN = float(os.environ.get("BOT_COOLDOWN", "10"))
BOT_VISIT_SECONDS = float(os.environ.get("BOT_VISIT_SECONDS", "7"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=64 * 1024,
)


# --------------------------------------------------------------------------
# База даних
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                author     TEXT NOT NULL,
                title      TEXT NOT NULL,
                body       TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reports (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id    INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


app.teardown_appcontext(close_db)
init_db()


# --------------------------------------------------------------------------
# «Слабкий» фільтр — серце вразливості
# --------------------------------------------------------------------------
_SCRIPT_BLOCK = re.compile(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S)
_SCRIPT_TAG = re.compile(r"<\s*/?\s*script\b[^>]*>", re.I)
_JS_URI = re.compile(r"javascript\s*:", re.I)


def sanitize_body(text: str) -> str:
    """Видаляє <script> та javascript:, але залишає обробники подій.

    CTF: цього недостатньо. <img src=x onerror=...> або <svg onload=...>
    проходять фільтр і виконуються в шаблоні через |safe.
    """
    text = _SCRIPT_BLOCK.sub("", text)
    text = _SCRIPT_TAG.sub("", text)
    text = _JS_URI.sub("", text)
    return text[:2000]


# --------------------------------------------------------------------------
# Бот
# --------------------------------------------------------------------------
def _visit_post(post_id: int) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        try:
            context = browser.new_context()
            page = context.new_page()
            page.on("dialog", lambda dialog: dialog.dismiss())

            page.goto(f"{APP_BASE_URL}/login", wait_until="domcontentloaded")
            page.fill("#username", ADMIN_USER)
            page.fill("#password", ADMIN_PASSWORD)
            page.click("button[type=submit]")
            page.wait_for_load_state("domcontentloaded")

            # Саме тут виконується payload гравця.
            page.goto(f"{APP_BASE_URL}/post/{post_id}", wait_until="domcontentloaded")
            page.wait_for_timeout(int(BOT_VISIT_SECONDS * 1000))
        finally:
            browser.close()


def _bot_worker(bot_queue: "queue.Queue[int]") -> None:
    while True:
        post_id = bot_queue.get()
        try:
            _visit_post(post_id)
            app.logger.info("bot visited post %s", post_id)
        except Exception as exc:  # noqa: BLE001 — бот не має падати
            app.logger.warning("bot error on post %s: %s", post_id, exc)
        finally:
            bot_queue.task_done()


bot_queue: "queue.Queue[int]" = queue.Queue(maxsize=20)
_bot_available = False
if BOT_ENABLED:
    try:
        import playwright.sync_api  # noqa: F401

        threading.Thread(
            target=_bot_worker, args=(bot_queue,), daemon=True, name="admin-bot"
        ).start()
        _bot_available = True
    except ImportError:
        app.logger.warning(
            "Playwright is not installed — admin bot disabled. "
            "Docker: docker compose up --build. "
            "Python: pip install playwright && playwright install chromium"
        )

_cooldown_lock = threading.Lock()
_last_report: dict[str, float] = {}


# --------------------------------------------------------------------------
# Сторінки
# --------------------------------------------------------------------------
@app.get("/")
def index():
    posts = get_db().execute(
        "SELECT id, author, title, body, created_at FROM posts ORDER BY id DESC"
    ).fetchall()
    return render_template("index.html", posts=posts)


@app.route("/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        author = request.form.get("author", "").strip()[:40]
        title = request.form.get("title", "").strip()[:80]
        body = request.form.get("body", "").strip()

        if len(author) < 2 or len(title) < 3 or len(body) < 1:
            flash("Заповни ім'я, заголовок і текст поста.", "error")
            return render_template("new.html", author=author, title=title, body=body)

        body = sanitize_body(body)
        db = get_db()
        cur = db.execute(
            "INSERT INTO posts (author, title, body) VALUES (?, ?, ?)",
            (author, title, body),
        )
        db.commit()
        flash("Пост опубліковано.", "ok")
        return redirect(url_for("post", post_id=cur.lastrowid))

    return render_template("new.html", author="", title="", body="")


@app.get("/post/<int:post_id>")
def post(post_id):
    item = get_db().execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if item is None:
        abort(404)
    return render_template("post.html", post=item)


@app.post("/report/<int:post_id>")
def report(post_id):
    db = get_db()
    if db.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone() is None:
        abort(404)

    if not _bot_available:
        flash("Адмін-бот недоступний. Дивись README (Docker або Playwright).", "error")
        return redirect(url_for("post", post_id=post_id))

    ip = request.remote_addr or "unknown"
    now = time.monotonic()
    with _cooldown_lock:
        elapsed = now - _last_report.get(ip, 0.0)
        if elapsed < BOT_COOLDOWN:
            flash(f"Зачекай {int(BOT_COOLDOWN - elapsed) + 1} с перед наступною скаргою.", "error")
            return redirect(url_for("post", post_id=post_id))
        _last_report[ip] = now

    try:
        bot_queue.put_nowait(post_id)
    except queue.Full:
        flash("Черга бота переповнена, спробуй пізніше.", "error")
        return redirect(url_for("post", post_id=post_id))

    db.execute("INSERT INTO reports (post_id) VALUES (?)", (post_id,))
    db.commit()
    flash("Скаргу надіслано. Модератор відкриє пост за кілька секунд.", "ok")
    return redirect(url_for("post", post_id=post_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USER and secrets.compare_digest(password, ADMIN_PASSWORD):
            session.clear()
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Невірний логін або пароль.", "error")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    flash("Сесію завершено.", "ok")
    return redirect(url_for("index"))


@app.get("/admin")
def admin():
    if not session.get("admin"):
        abort(403)
    posts = get_db().execute(
        "SELECT id, author, title, created_at FROM posts ORDER BY id DESC LIMIT 50"
    ).fetchall()
    reports = get_db().execute(
        "SELECT post_id, created_at FROM reports ORDER BY id DESC LIMIT 10"
    ).fetchall()
    return render_template("admin.html", posts=posts, reports=reports, flag=FLAG)


@app.get("/admin/flag")
def admin_flag():
    """JSON для зручності експлуатації. Доступний лише адміну."""
    if not session.get("admin"):
        return jsonify(error="forbidden"), 403
    return jsonify(flag=FLAG)


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", bot=_bot_available)


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, message="Доступ лише для адміністратора."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="Сторінку не знайдено."), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")))
