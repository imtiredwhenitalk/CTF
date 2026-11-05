from flask import Flask, send_from_directory

app = Flask(__name__)

PAGE = """
<!doctype html>
<title>Autumn archive</title>
<h1>Lost field report</h1>
<p>Our volunteer used the public alias <b>autumn_fox</b>.</p>
<p>The original post was deleted, but the recovered camera evidence is still available.</p>
<p>Download <a href="/evidence.png">evidence.png</a> and inspect its metadata and trailing data.</p>
<p>Useful OSINT leads: the alias, the date <b>2026-10-17</b>, and the source name
<code>field-camera-2026-10-17</code>.</p>
"""


@app.get("/")
def index():
    return PAGE


@app.get("/evidence.png")
def evidence():
    return send_from_directory(".", "evidence.png", mimetype="image/png")


@app.get("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /internal/\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
