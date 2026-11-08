"""Спільний шаблон оформлення для всіх CTF-сайтів."""
from pathlib import Path
from flask import send_file
from markupsafe import escape

_THEME = Path(__file__).parent / "static" / "theme.css"


def setup(app):
    @app.get("/_ui/theme.css")
    def _ui_theme():
        return send_file(_THEME, mimetype="text/css")


def esc(value):
    return str(escape(value))


def page(title, body, brand="ЛНТУ", accent="#38bdf8", nav=(("/", "Головна"),)):
    """Повертає готовий HTML (рядок). Не Jinja-шаблон: фігурні дужки не обробляються."""
    links = "".join(f'<a href="{h}">{t}</a>' for h, t in nav)
    return (
        '<!doctype html><html lang="uk"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title} · {brand}</title>"
        '<link rel="stylesheet" href="/_ui/theme.css"></head>'
        f'<body style="--accent:{accent}">'
        f'<header class="nav"><div class="wrap"><a class="brand" href="/">{brand}</a><nav>{links}</nav></div></header>'
        f'<main class="wrap">{body}</main>'
        '<div class="foot">Навчальний полігон ЛНТУ Cyber Range · усі дані та організації вигадані</div>'
        "</body></html>"
    )
