# Writeup: Flag 4 - System Override (PWN)

1. Підключитися до `nc localhost 1337`.
2. Бінарник розроблений з вразливістю `gets()` (Stack Buffer Overflow).
3. Визначити зміщення адреси повернення (Offset = 72 байти).
4. Знайти адресу функції `win()` через gdb або objdump: `nm vuln | grep win`.
5. Сформувати експлойт за допомогою pwntools для перезапису RIP/EIP адресою `win()`.
6. Отримати прапор: `CTF{pwn_th3_s3rv3r_g3t_th3_r00t}`.
