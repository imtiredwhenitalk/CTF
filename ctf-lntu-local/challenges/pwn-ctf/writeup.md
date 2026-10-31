# Writeup: PWN Buffer Overflow

1. Підключитися до таску: `nc localhost 1337`
2. Переповнити буфер вразливої функції `gets()` (offset 72 байти).
3. Перенаправити потік виконання на адресу функції `win()`.
4. Прапор: `CTF{pwn_lntu_st4ck_0v3rfl0w_r00t}`
