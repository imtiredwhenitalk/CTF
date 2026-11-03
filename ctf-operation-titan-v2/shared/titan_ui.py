"""Operation Titan shared UI. Single source: shared/titan_ui.py (copied into each task by tools/sync_ui.sh)."""
import os
from flask import render_template_string
from markupsafe import Markup

_CSS = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "titan.css"), encoding="utf-8").read()

LOGO = ('<svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M16 2 28 9v14L16 30 4 23V9z" stroke="#86b4d8" stroke-width="2"/>'
        '<path d="M10 12h12M16 12v11" stroke="#ff7a3d" stroke-width="2.4" stroke-linecap="square"/></svg>')

LAYOUT = """<!DOCTYPE html>
<html lang="uk"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} · Operation Titan</title>
<style>{{ css|safe }}</style></head>
<body>
<header class="topbar"><div class="in">
  <a class="brand" href="/">{{ logo|safe }}<span>Operation Titan</span></a>
  <span class="node"><span class="dot"></span>{{ node }}</span>
</div></header>
<main class="wrap">
  <section class="hero">
    <span class="tag">{{ tag }}</span>
    <h1>{{ heading }}</h1>
    {% if lead %}<p>{{ lead }}</p>{% endif %}
  </section>
  {{ body }}
  <div class="foot">titan-lab · {{ node }}</div>
</main>
<script>
document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){
  var t=document.getElementById(b.dataset.copy);if(!t)return;
  (navigator.clipboard?navigator.clipboard.writeText(t.innerText):Promise.reject()).then(function(){
    b.textContent='Скопійовано';setTimeout(function(){b.textContent='Копіювати'},1200)},function(){
    var r=document.createRange();r.selectNodeContents(t);var s=getSelection();s.removeAllRanges();s.addRange(r)})})});
</script>
</body></html>"""


def page(body_tpl, *, title, heading, lead="", tag="", node="titan-node", **ctx):
    """Render a Jinja body snippet (autoescaped) inside the Titan layout."""
    body = Markup(render_template_string(body_tpl, **ctx))
    return render_template_string(LAYOUT, body=body, title=title, heading=heading, lead=lead,
                                  tag=tag, node=node, css=_CSS, logo=LOGO)
