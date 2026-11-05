from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

FLAG = "CTF{r3s3t_t0k3n_1s_n0t_s3cr3t}"
RESET_TOKENS = {
    "admin": "reset-admin-2026",
}

PAGE = """
<!doctype html>
<title>LNTU account recovery</title>
<h1>Account recovery</h1>
<p>Enter a username to request a password reset link.</p>
<form method="post" action="/reset">
  <input name="username" placeholder="username" required>
  <button>Request reset</button>
</form>
{% if message %}<pre>{{ message }}</pre>{% endif %}
"""


@app.get("/")
def index():
    return render_template_string(PAGE, message=None)


@app.post("/reset")
def reset():
    username = request.form.get("username", "").strip().lower()
    token = RESET_TOKENS.get(username)
    if token is None:
        return render_template_string(PAGE, message="If the account exists, a link was sent.")

    # The token is accidentally included in the support response.
    return render_template_string(
        PAGE,
        message=f"Support preview: /reset/confirm?user={username}&token={token}",
    )


@app.get("/reset/confirm")
def confirm_reset():
    username = request.args.get("user", "")
    token = request.args.get("token", "")
    if username == "admin" and token == RESET_TOKENS["admin"]:
        return jsonify({"status": "ok", "message": "Password reset accepted", "flag": FLAG})
    return jsonify({"status": "error", "message": "Invalid reset link"}), 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
