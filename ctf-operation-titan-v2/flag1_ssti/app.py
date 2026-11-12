from flask import Flask, request, render_template_string
from markupsafe import Markup
from titan_ui import page

app = Flask(__name__)

# ---------------------------------------------------------------------------
# TRAP / RED HERRING: values below are decoys. They are rotated/legacy and are
# NOT accepted by the scoreboard. The live flag is only in /flag.txt.
# ---------------------------------------------------------------------------
LEGACY_FLAG = "CTF{sst1_l3g4cy_c0ns0l3_fl4g}"
BLOCKED_TOKENS = ("flag", "os", "popen", "system", "subprocess", "lipsum", "cycler")

BODY = '''
<div class="grid">
<div class="card"><div class="hd">Термінал зв'язку<span class="sub">POST /</span></div><div class="bd">
  <p>Введіть позивний оператора. Консоль згенерує привітання для поточної зміни.</p>
  <form method="POST" action="/">
    <div class="field"><label for="callsign">Позивний</label>
      <input id="callsign" class="input" type="text" name="callsign" value="{{ callsign }}"
             placeholder="наприклад, NIGHTFALL" autocomplete="off"></div>
    <div class="row"><button class="btn primary" type="submit">Передати на термінал</button></div>
  </form>
</div></div>
{% if output %}
<div class="card"><div class="hd">Відповідь терміналу<span class="sub">stdout</span></div><div class="bd">
  <div class="alert ok">{{ output }}</div>
</div></div>
{% endif %}
<div class="card"><div class="hd">Службова інформація</div><div class="bd">
  <p class="muted">Термінал збирає статистику через вбудований шаблонізатор. Внутрішній файл
  <code>/flag.txt</code> доступний лише процесу консолі.</p>
  <a class="btn" href="/source">Переглянути код консолі</a>
  <a class="btn" href="/backup">Архів конфігурації</a>
</div></div>
</div>
'''


def view(callsign="", output=""):
    return page(
        BODY,
        title="Comms Console",
        heading="Titan Comms Console",
        tag="01 · SSTI",
        node="titan-node-01 · comms",
        lead="Консоль зв'язку рендерить позивні операторів на льоту.",
        callsign=callsign,
        output=Markup(output),
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    output = ""
    callsign = ""
    if request.method == 'POST':
        callsign = request.form.get('callsign', '').strip()
        if callsign:
            # Small WAF: the obvious writeup payloads are blocked on purpose.
            if any(token in callsign.lower() for token in BLOCKED_TOKENS):
                output = "WAF: callsign contains a prohibited token."
            else:
                try:
                    # VULNERABLE BY DESIGN: operator input is concatenated into
                    # the template source instead of being passed as a context
                    # variable.
                    output = render_template_string(
                        "Operator " + callsign + " linked. Systems nominal."
                    )
                except Exception as exc:
                    output = f"Template error: {exc}"
    return view(callsign, output)


@app.route('/backup')
def backup():
    # TRAP: retired configuration snapshot with an old console flag.
    return (
        "Titan Comms Console - legacy configuration\n"
        "==========================================\n"
        "status=decommissioned\n"
        f"console_flag={LEGACY_FLAG}\n"
        "note=retired during the 2023 key rotation; not a live scoring flag\n"
    ), 200, {'Content-Type': 'text/plain'}


@app.route('/source')
def source():
    return open(__file__).read(), 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
