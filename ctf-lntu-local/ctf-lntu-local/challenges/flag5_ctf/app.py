import os
from flask import Flask, jsonify, request
from ui import page, setup, esc

app = Flask(__name__)
setup(app)
BRAND, ACCENT = "LNTU Accounts", "#34d399"
NAV = (("/", "Відновлення доступу"),)
FLAG = "CTF{r3s3t_t0k3n_1s_n0t_s3cr3t}"
RESET_TOKENS = {"admin": "reset-admin-2026"}


def render(message=""):
    box = f'<div class="alert warn"><pre style="margin:0;background:none;border:0">{esc(message)}</pre></div>' if message else ""
    body = f"""<h1>Відновлення доступу</h1>
    <p class="lead">Введіть ім'я користувача — ми надішлемо посилання для скидання пароля на пошту.</p>
    <form method="post" action="/reset" class="card accent"><label>Ім'я користувача</label>
    <input name="username" placeholder="username" required><button>Надіслати посилання</button></form>{box}"""
    return page("Відновлення доступу", body, BRAND, ACCENT, NAV)


@app.get("/")
def index():
    return render()


@app.post("/reset")
def reset():
    username = request.form.get("username", "").strip().lower()
    token = RESET_TOKENS.get(username)
    if token is None:
        return render("Якщо акаунт існує, посилання було надіслано.")
    # навмисна помилка: токен потрапляє у відповідь «підтримки»
    return render(f"[support-preview] /reset/confirm?user={username}&token={token}")


@app.get("/reset/confirm")
def confirm():
    if request.args.get("user") == "admin" and request.args.get("token") == RESET_TOKENS["admin"]:
        return jsonify({"status": "ok", "message": "Password reset accepted", "flag": FLAG})
    return jsonify({"status": "error", "message": "Invalid reset link"}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
