import requests
from bs4 import BeautifulSoup
import sqlite3


rs = requests.get('http://www.7english.ru/dictionary.php?id=2000&letter=all')
root = BeautifulSoup(rs.content, 'html.parser')

en_ru_items = []

for tr in root.select('tr[onmouseover]'):
    td_list = [td.text.strip() for td in tr.select('td')]
    if len(td_list) != 9 or not td_list[1] or not td_list[5]:
        continue

    en = td_list[1]
    ru = td_list[5].split(', ')[0]

    en_ru_items.append((en, ru))


def all_words(items):
    words = sqlite3.connect('words.db')
    cursor = words.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS words(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    eng TEXT,
    rus TEXT);
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_settings(
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        word_count INTEGER,
        is_subscribe BOLLEAN DEFAULT 1);
        ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS "learn_words" (
        "ID"	INTEGER,
        "setting_id"	INTEGER,
        "word_id"	INTEGER,
        "is_learned"	INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY("ID" AUTOINCREMENT),
        FOREIGN KEY("word_id") REFERENCES "words"("ID"),
        FOREIGN KEY("setting_id") REFERENCES "user_settings"("ID"));
        ''')
    print('Подключен к SQLite')

    sqlite_insert_query = '''INSERT INTO words
                              (eng, rus)
                              VALUES (?, ?);'''

    cursor.executemany(sqlite_insert_query, items)
    words.commit()


all_words(en_ru_items)
