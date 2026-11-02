import os


class Config:
    # Шлях до SQLite. У Docker лежить у /srv/data
    DATABASE = os.environ.get("DATABASE", "data/shop.db")

    # Прапор для CTF. Змінюється через змінну оточення FLAG
    FLAG = os.environ.get("FLAG", "CTF{xss_in_the_darkroom}")
