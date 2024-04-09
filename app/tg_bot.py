from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
import io
import boto3
import asyncio
import httpx

from app.config import NUM_HUBS, BUCKET

s3_access_key = os.getenv("S3_ACCESS_KEY")
s3_secret_key = os.getenv("S3_SECRET_KEY")

if os.path.exists("/.dockerenv"):
    service_host_url = 'http://server:8000'
else:
    service_host_url = 'http://127.0.0.1:8000'

s3_client = boto3.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=s3_access_key,
    aws_secret_access_key=s3_secret_key
)

# TOKEN_TELEGRAM_API = s3_client.get_object(Bucket=BUCKET, Key="secrets/tg_bot/token.txt").get('Body').read().decode()
TOKEN_TELEGRAM_API = '7033017007:AAGYdBYBE7shqSwWubN2SgBITTPogL6J5Mg'

keyboard = [
    [InlineKeyboardButton("0️⃣", callback_data='0'),
     InlineKeyboardButton("1️⃣", callback_data='1'),
     InlineKeyboardButton("2️⃣", callback_data='2'),
     InlineKeyboardButton("3️⃣", callback_data='3'),
     InlineKeyboardButton("4️⃣", callback_data='4'),
     InlineKeyboardButton("5️⃣", callback_data='5')]
]
markup = InlineKeyboardMarkup(keyboard)


async def start(update, context):
    message = 'Готов к работе!'
    await update.message.reply_text(message)


async def help(update, context):
    message = """Привет! Я бот помогающий подобрать соответствующие хабы для статьи на сайте https://habr.com
Отпрвь мне статью и я предложу топ-5 наиболее подходящих хабов!
- Чтобы изменить количество рекомендуемых хабов воспользуйся командой: /change_num_hubs <желаемое количество хабов>
- Для просмотра текущего рейтинга рекомендаций бота, \
посчитанного по отзывам пользователей, воспользуйся командой: /rating
- Если статья объёмная, отправь текстовый файл со статьёй внутри
Хорошего пользования!"""
    await update.message.reply_text(message)


async def change_num_hubs(update, context):
    text = update.message.text
    try:
        num_hubs = int(text.removeprefix('/change_num_hubs '))
        assert num_hubs > 0
        context.chat_data['num_hubs'] = num_hubs
        message = f'Отлично, количество рекомендуемых хабов изменилось на {num_hubs}!'
    except Exception:
        message = 'Произошла ошибка, попробуйте ещё раз в формате: /change_num_hubs <желаемое количество хабов>'
    await update.message.reply_text(message)


async def predict(update, context):
    text = update.message.text
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    done_flag = False
    async with httpx.AsyncClient() as client:
        for try_num in range(1, 4):
            response = await client.post(service_host_url + '/predict',
                                         json={'text': text, 'num_hubs': num_hubs})
            if response.status_code != 200:
                message = f'Ошибка: {response.status_code}, попыток: {try_num}'
                await asyncio.sleep(2 ** try_num)
                continue
            output = response.json()
            hubs = output['hubs']
            message = 'Наиболее подходящие хабы для данной статьи:\n\n'
            message += '\n'.join(hubs) + '\n\n'
            message += 'Оцените пожалуйста результат рекомендации от 0 до 5:'
            done_flag = True
            break
    if done_flag:
        await update.message.reply_text(message, reply_markup=markup)
    else:
        await update.message.reply_text(message)


async def predict_file(update, context):
    done_flag = False
    async with httpx.AsyncClient() as client:
        for try_num in range(1, 4):
            file = await context.bot.get_file(update.message.document)
            if file is None:
                message = f'Ошибка на стороне Telegram, попыток: {try_num}'
                await asyncio.sleep(2 ** try_num)
                continue
            file_path = file['file_path']
            file_response = await client.get(file_path)
            if file_response.status_code != 200:
                message = f'Ошибка {file_response.status_code} на стороне Telegram, попыток: {try_num}'
                await asyncio.sleep(2 ** try_num)
                continue
            num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
            response = await client.post(service_host_url + '/predict_file' + f'?num_hubs={num_hubs}',
                                         files={'file': ('filename', io.BytesIO(file_response.content))})
            if response.status_code != 200:
                message = f'Ошибка: {response.status_code}, попыток: {try_num}'
                await asyncio.sleep(2 ** try_num)
                continue
            output = response.json()
            hubs = output['hubs']
            if not hubs:
                message = 'Произошла ошибка, попробуйте ещё раз, проверьте, что вы отправляете текстовый файл (.txt)'
                break
            message = 'Наиболее подходящие хабы для данной статьи:\n\n'
            message += '\n'.join(hubs) + '\n\n'
            message += 'Оцените пожалуйста результат рекомендации от 0 до 5:'
            done_flag = True
            break
    if done_flag:
        await update.message.reply_text(message, reply_markup=markup)
    else:
        await update.message.reply_text(message)


async def button_click(update, context):
    query = update.callback_query
    await query.edit_message_reply_markup(None)
    button = query.data
    async with httpx.AsyncClient() as client:
        for try_num in range(1, 4):
            response = await client.post(service_host_url + '/feedback' + f'?button={button}')
            if response.status_code != 200:
                await asyncio.sleep(2 ** try_num)
                continue
            break


async def rating(update, context):
    async with httpx.AsyncClient() as client:
        for try_num in range(1, 4):
            response = await client.get(service_host_url + '/rating')
            if response.status_code != 200:
                await asyncio.sleep(2 ** try_num)
                continue
            output = response.json()
            num_feedbacks = output['num_feedbacks']
            if num_feedbacks == 0:
                message = 'Пока нету ни одного отзыва о рекомендациях, стань первым!'
            else:
                rating_score = output['rating']
                message = f'Текущей рейтинг рекомендаций бота, \
основанный на {num_feedbacks} отзывах пользователей:\n{rating_score}'
            break
    await update.message.reply_text(message)


def main():
    application = Application.builder().token(TOKEN_TELEGRAM_API).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("change_num_hubs", change_num_hubs))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, predict))
    application.add_handler(MessageHandler(filters.Document.ALL, predict_file))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("rating", rating))
    application.run_polling()


if __name__ == '__main__':
    print('TG BOT run!')
    main()
