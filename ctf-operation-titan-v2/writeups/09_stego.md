# 09. Hidden Archive (300 балів) — розв'язок

Прапор: `CTF{st3g0_4nd_43s_1s_fun}`

## Вразливість

`image.png` — валідний PNG, але після маркера `IEND` до нього дописано ZIP-архів.
Сторінка прямо підказує: «Подивіться, що лежить після його кінця», а пароль до
вкладення — `titan`.

## Експлойт

```bash
curl -O http://10.10.15.124:8009/image.png
file image.png

binwalk image.png                 # покаже PNG + Zip archive
strings -a image.png | tail       # можна побачити імена файлів

python3 - <<'PY'
data = open("image.png", "rb").read()
off = data.find(b"PK\x03\x04")    # початок ZIP
open("secret.zip", "wb").write(data[off:])
print("zip offset:", off)
PY

unzip -P titan secret.zip
cat secret.txt
```

Або одразу:

```bash
unzip -P titan image.png
```

## Прапор

```text
CTF{st3g0_4nd_43s_1s_fun}
```

## Пастки

- `/image_old.png` — архів 2021 року з тим самим паролем `titan`. Усередині
  `CTF{st3g0_l3g4cy_4rch1v3_fl4g}` — це не справжній прапор.
- `/notes.txt` прямо показує цей фальшивий флаг і може здатися «готовою»
  відповіддю. Не вірте йому.
- Справжній ZIP дописаний саме до `image.png`; орієнтуйтеся на розмір/offset
  `PK\x03\x04` і на вміст `secret.txt`.
