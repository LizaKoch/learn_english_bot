import logging
import sqlite3
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor, types
import aiocron


load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

words = sqlite3.connect('words.db')
cursor = words.cursor()


async def create_new_words(settings_id, word_count):
    # user_setting = cursor.execute('''SELECT ID, word_count FROM user_settings WHERE chat_id = ?;''', (chat_id, ))
    # settings_id, user_count_word = user_setting.fetchone()
    count_unlearned = cursor.execute('''SELECT count(*) FROM learn_words WHERE is_learned = 0 AND setting_id = ?;''', (settings_id, )).fetchone()
    if count_unlearned[0]:
        word_count -= 1
    cursor.execute('''INSERT INTO learn_words (word_id, setting_id, is_learned)
                    SELECT words.id as word_id, ? as setting_id, 0 as is_learned
                    FROM words
                    LEFT JOIN learn_words ON (words.ID=learn_words.word_id)
                    WHERE
                        learn_words.word_id IS NULL
                    ORDER BY RANDOM() LIMIT ?;''', (settings_id, word_count))
    words.commit()


@aiocron.crontab('0 0 * * *')
async def create_all():
    settings = cursor.execute('''SELECT ID, word_count FROM user_settings WHERE is_subscribe=1''').fetchall()
    for setting_id, word_count in settings:
        await create_new_words(setting_id, word_count)


# @dp.message_handler()
async def send_word(message: types.Message):
    user_setting = cursor.execute('''SELECT ID, word_count FROM user_settings WHERE chat_id = ?;''', (message.chat.id, ))
    settings_id, user_count_word = user_setting.fetchone()
    count_unlearned = cursor.execute('''SELECT count(*) FROM learn_words WHERE is_learned = 0 AND setting_id = ?;''', (settings_id, )).fetchone()
    if count_unlearned[0]:
        user_count_word -= 1
    cursor.execute('''INSERT INTO learn_words (word_id, setting_id, is_learned)
                    SELECT words.id as word_id, ? as setting_id, 0 as is_learned
                    FROM words
                    LEFT JOIN learn_words ON (words.ID=learn_words.word_id)
                    WHERE
                        learn_words.word_id IS NULL
                    ORDER BY RANDOM() LIMIT ?;''', (settings_id, user_count_word))
    words.commit()
    list_words = cursor.execute('''SELECT learn_words.ID, learn_words.word_id, words.eng, words.rus from learn_words
                                LEFT JOIN words ON (learn_words.word_id=words.ID)
                                WHERE learn_words.is_learned=0 AND learn_words.setting_id = ?
                                ORDER BY RANDOM() LIMIT ?;''', (settings_id, user_count_word)).fetchall()



@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = [
            [types.KeyboardButton(text="Что я умею?")],
            [types.KeyboardButton(text="Узнать ID")]
        ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer('Выбери', reply_markup=keyboard)


@dp.message_handler(content_types=['text'], text='Что я умею?')
async def what_can(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Хочу выучить английский")],
        [types.KeyboardButton(text="Хочу читать статьи")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)

    await message.answer("Я могу помочь тебе выучить английский или присылать тебе статьи с журнала хакер!", reply_markup=keyboard)


@dp.message_handler(content_types=['text'], text='Узнать ID')
async def know_id(message: types.Message):
    await message.answer(f'Твой ID: {message.from_user.id}')


@dp.message_handler(content_types=['text'], text='Хочу выучить английский')
async def learn_words(message: types.Message):
    await message.answer('Я буду присылать тебе по несколько слов в день, \
а ты должен выучить их. \
Раз в неделю я буду проверять, что ты выучил. \
Напиши сколько слов в день ты готов учить. Например: 5')



@dp.message_handler(content_types=['text'])
async def add_count_words(message: types.Message):
    user_setting = cursor.execute('''SELECT ID FROM user_settings WHERE chat_id = ?;''', (message.chat.id, ))
    a = user_setting.fetchone()
    if a is None:
        cursor.execute('''INSERT INTO user_settings (chat_id, word_count) VALUES (?, ?);''',
        (message.chat.id, message.text))
    else:
        cursor.execute('''UPDATE user_settings SET word_count=?, is_subscribe=? WHERE ID = ?;''', (message.text, 1, a[0]))
    words.commit()
    await message.answer(f'Хорошо! Я буду присылать тебе {message.text} слов в день.')
    await send_word(message)


if __name__ == '__main__':
    # asyncio.get_event_loop().run_forever()
    # create_all.start()
    executor.start_polling(dp, skip_updates=True)


# SELECT *
# FROM words
# LEFT JOIN learn_words ON (words.ID=learn_words.word_id)
# WHERE learn_words.word_id IS NULL ORDER BY RANDOM() LIMIT 2