"""Усе, що стосується самого CTF, лежить тут.

Щоб зробити завдання складнішим, міняй `sanitize_review`
або додай нові слабкі місця. Решта коду магазину чіпати не треба.
"""
import re

from flask import current_app, request

# Слабкий фільтр: прибирає лише <script> у нижньому регістрі.
# Обійти його можна обробниками подій (onerror, onload) або іншим регістром.
_SCRIPT_TAG = re.compile(r"</?script[^>]*>")


def sanitize_review(text):
    """Stored XSS: відгук проходить цей фільтр, а в шаблоні виводиться через |safe."""
    return _SCRIPT_TAG.sub("", text)


def init_app(app):
    @app.after_request
    def give_flag_cookie(response):
        # Cookie без HttpOnly, тому читається через document.cookie.
        # Уяви, що це сесія модератора.
        if "flag" not in request.cookies:
            response.set_cookie("flag", current_app.config["FLAG"], httponly=False)
        return response
