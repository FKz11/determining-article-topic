from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import os
import io
import json
import pickle
import torch
import boto3

from config import VERSION, NUM_HUBS, BUCKET
from model_class import Model_hubs
from preprocessing import del_puncts, get_tokens
from private import s3_access_key, s3_secret_key

device = 'cuda' if torch.cuda.is_available() else 'cpu'

s3_client = boto3.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=s3_access_key,
    aws_secret_access_key=s3_secret_key
)

TOKEN_TELEGRAM_API = s3_client.get_object(Bucket=BUCKET, Key="secrets/tg_bot/token.txt").get('Body').read().decode()
model = torch.load(
    io.BytesIO(s3_client.get_object(Bucket=BUCKET, Key=f"models/model_v{VERSION}/model.pth").get('Body').read()),
    map_location=device)
tfidf_vectorizer = pickle.loads(
    s3_client.get_object(Bucket=BUCKET, Key=f"models/model_v{VERSION}/tfidf_vectorizer.pkl").get('Body').read())
id2hub = pickle.loads(s3_client.get_object(Bucket=BUCKET, Key=f"models/model_v{VERSION}/id2hub.pkl").get('Body').read())
feedback = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())

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
    message = (f'Готов к работе!')
    await update.message.reply_text(message)


async def change_num_hubs(update, context):
    text = update.message.text
    try:
        num_hubs = int(text.removeprefix('/change_num_hubs '))
        assert num_hubs > 0
        context.chat_data['num_hubs'] = num_hubs
        message = f'Отлично, количество рекомендуемых хабов изменилось на {num_hubs}!'
    except:
        message = 'Произошла ошибка, попробуйте ещё раз в формате: /change_num_hubs <желаемое количество хабов>'
    await update.message.reply_text(message)


async def predict(update, context):
    text = update.message.text
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    output = model.predict(text, del_puncts, get_tokens, tfidf_vectorizer, id2hub, num_hubs, device)
    hubs = [item[0] for item in output]
    message = 'Наиболее подходящие хабы для данной статьи:\n\n'
    message += '\n'.join(hubs) + '\n\n'
    message += 'Оцените пожалуйста результат рекомендации от 0 до 5:'
    await update.message.reply_text(message, reply_markup=markup)


async def predict_file(update, context):
    file2text_flag = False
    try:
        file = await context.bot.get_file(update.message.document)
        await file.download_to_drive('cache/file.txt')
        with open("cache/file.txt", 'r', encoding="utf8") as f:
            text = f.read()
        os.remove("cache/file.txt")
        file2text_flag = True
    except:
        message = 'Произошла ошибка, попробуйте ещё раз, проверьте, что вы отправляете текстовый файл (.txt)'
        await update.message.reply_text(message)
    if file2text_flag:
        num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
        output = model.predict(text, del_puncts, get_tokens, tfidf_vectorizer, id2hub, num_hubs, device)
        hubs = [item[0] for item in output]
        message = 'Наиболее подходящие хабы для данной статьи:\n\n'
        message += '\n'.join(hubs) + '\n\n'
        message += 'Оцените пожалуйста результат рекомендации от 0 до 5:'
        await update.message.reply_text(message, reply_markup=markup)


async def button_click(update, context):
    query = update.callback_query
    await query.edit_message_reply_markup(None)
    button = query.data
    feedback[button] += 1
    s3_client.put_object(Bucket=BUCKET, Key="feedback.json", Body=json.dumps(feedback))


async def rating(update, context):
    num_feedbacks = sum([v for k, v in feedback.items()])
    if num_feedbacks == 0:
        message = 'Пока нету ни одного отзыва о рекомендациях, стань первым!'
    else:
        rating_score = sum([int(k) * int(v) for k, v in feedback.items()]) / num_feedbacks
        message = f'Текущей рейтинг рекомендаций бота, основанный на {num_feedbacks} отзывах пользователей:\n{rating_score}'
    await update.message.reply_text(message)


def main():
    application = Application.builder().token(TOKEN_TELEGRAM_API).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change_num_hubs", change_num_hubs))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, predict))
    application.add_handler(MessageHandler(filters.Document.ALL, predict_file))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(CommandHandler("rating", rating))
    application.run_polling()


if __name__ == '__main__':
    print('TG BOT run!')
    main()
