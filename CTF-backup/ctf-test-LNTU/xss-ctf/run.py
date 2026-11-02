import os

from app import _bot_available, app

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    print(f"[*] NullByte Forum: http://127.0.0.1:{port}")
    print(f"[*] Admin bot: {'enabled' if _bot_available else 'DISABLED (Playwright missing)'}")
    app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)
