import pytest
from unittest.mock import AsyncMock

import json
import boto3

from app.private import s3_access_key, s3_secret_key
from app.config import NUM_HUBS, BUCKET

# тестирующиеся функции ТГ-бота
from app.tg_bot import start
from app.tg_bot import help
from app.tg_bot import change_num_hubs
from app.tg_bot import predict
from app.tg_bot import predict_file
from app.tg_bot import button_click
from app.tg_bot import rating


class MessageMock(AsyncMock):

    async def reply_text(self, message, *args, **kwargs):
        self.text = message


class FileMock(AsyncMock):

    def __init__(self, to_path, *args, **kwargs):
        super().__init__()
        self.from_path = to_path

    async def download_to_drive(self, to_path, *args, **kwargs):
        with open(self.from_path, 'r') as f_r:
            with open(to_path, 'w') as f_w:
                f_w.write(f_r.read())


class BotMock(AsyncMock):

    async def get_file(self, to_path, *args, **kwargs):
        return FileMock(to_path)


@pytest.mark.asyncio
async def test_start():
    update = AsyncMock()
    context = AsyncMock()
    await start(update, context)
    message = 'Готов к работе!'
    update.message.reply_text.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_help():
    update = AsyncMock()
    context = AsyncMock()
    await help(update, context)
    message = """Привет! Я бот помогающий подобрать соответствующие хабы для статьи на сайте https://habr.com
Отпрвь мне статью и я предложу топ-5 наиболее подходящих хабов!
- Чтобы изменить количество рекомендуемых хабов воспользуйся командой: /change_num_hubs <желаемое количество хабов>
- Для просмотра текущего рейтинга рекомендаций бота, \
посчитанного по отзывам пользователей, воспользуйся командой: /rating
- Если статья объёмная, отправь текстовый файл со статьёй внутри
Хорошего пользования!"""
    update.message.reply_text.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_change_num_hubs():
    update = AsyncMock()
    context = AsyncMock()
    update.message.text = '/change_num_hubs 5'
    context.chat_data = dict()
    await change_num_hubs(update, context)
    assert context.chat_data["num_hubs"] == 5
    update.message.reply_text.assert_called_once_with('Отлично, количество рекомендуемых хабов изменилось на 5!')

    update = AsyncMock()
    context = AsyncMock()
    update.message.text = '/change_num_hubs -1'
    context.chat_data = dict()
    await change_num_hubs(update, context)
    update.message.reply_text.assert_called_once_with(
        'Произошла ошибка, попробуйте ещё раз в формате: /change_num_hubs <желаемое количество хабов>')

    update = AsyncMock()
    context = AsyncMock()
    update.message.text = '/change_num_hubs пять'
    context.chat_data = dict()
    await change_num_hubs(update, context)
    update.message.reply_text.assert_called_once_with(
        'Произошла ошибка, попробуйте ещё раз в формате: /change_num_hubs <желаемое количество хабов>')

    update = AsyncMock()
    context = AsyncMock()
    update.message.text = '/change_num_hubs'
    context.chat_data = dict()
    await change_num_hubs(update, context)
    update.message.reply_text.assert_called_once_with(
        'Произошла ошибка, попробуйте ещё раз в формате: /change_num_hubs <желаемое количество хабов>')


@pytest.mark.asyncio
async def test_predict():
    # проверка пустого сообщения на вход
    update = AsyncMock()
    context = AsyncMock()
    context.chat_data = dict()
    update.message = MessageMock()
    update.message.text = ''
    await predict(update, context)
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    output_text = update.message.text
    output_text = output_text.removeprefix('Наиболее подходящие хабы для данной статьи:\n\n')
    output_text = output_text.removesuffix('\n\nОцените пожалуйста результат рекомендации от 0 до 5:')
    assert len(output_text.split('\n')) == num_hubs

    # проверка количества рекомендаций
    update = AsyncMock()
    context = AsyncMock()
    context.chat_data = dict()
    context.chat_data['num_hubs'] = 7
    update.message = MessageMock()
    update.message.text = ' '
    await predict(update, context)
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    output_text = update.message.text
    output_text = output_text.removeprefix('Наиболее подходящие хабы для данной статьи:\n\n')
    output_text = output_text.removesuffix('\n\nОцените пожалуйста результат рекомендации от 0 до 5:')
    assert len(output_text.split('\n')) == num_hubs

    # проверка рекомендации
    update = AsyncMock()
    context = AsyncMock()
    context.chat_data = dict()
    context.chat_data['num_hubs'] = 1
    update.message = MessageMock()
    input_text = 'Астрономия'
    update.message.text = input_text
    await predict(update, context)
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    output_text = update.message.text
    output_text = output_text.removeprefix('Наиболее подходящие хабы для данной статьи:\n\n')
    output_text = output_text.removesuffix('\n\nОцените пожалуйста результат рекомендации от 0 до 5:')
    assert len(output_text.split('\n')) == num_hubs
    assert input_text == output_text


@pytest.mark.asyncio
async def test_predict_file():
    # проверка файла на вход с пустым сообщением
    update = AsyncMock()
    context = AsyncMock()
    context.chat_data = dict()
    context.bot = BotMock()
    update.message = MessageMock()
    update.message.document = 'test_input_empty.txt'
    await predict_file(update, context)
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    output_text = update.message.text
    output_text = output_text.removeprefix('Наиболее подходящие хабы для данной статьи:\n\n')
    output_text = output_text.removesuffix('\n\nОцените пожалуйста результат рекомендации от 0 до 5:')
    assert len(output_text.split('\n')) == num_hubs

    # проверка файла на вход с неправильным расширением, кодировкой
    update = AsyncMock()
    context = AsyncMock()
    context.chat_data = dict()
    context.bot = BotMock()
    update.message.document = 'test_input_extension.png'
    await predict_file(update, context)
    update.message.reply_text.assert_called_once_with(
        'Произошла ошибка, попробуйте ещё раз, проверьте, что вы отправляете текстовый файл (.txt)')

    # проверка рекомендации с файлом на вход
    update = AsyncMock()
    context = AsyncMock()
    context.chat_data = dict()
    context.chat_data['num_hubs'] = 1
    context.bot = BotMock()
    update.message = MessageMock()
    update.message.document = 'test_input_real.txt'
    await predict_file(update, context)
    num_hubs = context.chat_data.get('num_hubs', NUM_HUBS)
    output_text = update.message.text
    output_text = output_text.removeprefix('Наиболее подходящие хабы для данной статьи:\n\n')
    output_text = output_text.removesuffix('\n\nОцените пожалуйста результат рекомендации от 0 до 5:')
    assert len(output_text.split('\n')) == num_hubs
    with open('test_input_real.txt', 'r', encoding='utf-8') as f_r:
        input_text = f_r.read()
    assert input_text == output_text


@pytest.mark.asyncio
async def test_button_click():
    s3_client = boto3.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )
    # проверка, что кнопки корректно записываются в статистику
    feedback_before = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())
    update = AsyncMock()
    context = AsyncMock()
    button = '4'
    update.callback_query.data = button
    await button_click(update, context)
    feedback_after = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())
    s3_client.put_object(Bucket=BUCKET,
                         Key="feedback.json",
                         Body=json.dumps(feedback_before))  # возвращаем оригинальное значение
    feedback_before[button] += 1
    assert feedback_after == feedback_before


@pytest.mark.asyncio
async def test_rating():
    s3_client = boto3.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key
    )
    # проверка холодного старта
    feedback_orig = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())
    feedback_zero = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
    s3_client.put_object(Bucket=BUCKET, Key="feedback.json", Body=json.dumps(feedback_zero))
    update = AsyncMock()
    context = AsyncMock()
    await rating(update, context)
    s3_client.put_object(Bucket=BUCKET,
                         Key="feedback.json",
                         Body=json.dumps(feedback_orig))  # возвращаем оригинальное значение
    message = 'Пока нету ни одного отзыва о рекомендациях, стань первым!'
    update.message.reply_text.assert_called_once_with(message)

    # проверка, что рейтинг корректно считается
    update = AsyncMock()
    context = AsyncMock()
    await rating(update, context)
    feedback_rating = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())
    num_feedbacks = sum([v for k, v in feedback_rating.items()])
    rating_score = sum([int(k) * int(v) for k, v in feedback_rating.items()]) / num_feedbacks
    message = f'Текущей рейтинг рекомендаций бота, основанный на {num_feedbacks} отзывах пользователей:\n{rating_score}'
    update.message.reply_text.assert_called_once_with(message)
