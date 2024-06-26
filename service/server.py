from fastapi import FastAPI, File, UploadFile
from enum import Enum
import uvicorn
from aioredis import Redis
import hashlib
from pydantic import BaseModel
from typing import List

import os
import io
import json
import pickle
import torch
import boto3

from config import VERSION, NUM_HUBS, BUCKET
from model_class import Model_hubs  # noqa: F401
from preprocessing import del_puncts, get_tokens

device = 'cuda' if torch.cuda.is_available() else 'cpu'

s3_access_key = os.getenv("S3_ACCESS_KEY")
s3_secret_key = os.getenv("S3_SECRET_KEY")

s3_client = boto3.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=s3_access_key,
    aws_secret_access_key=s3_secret_key
)

model = torch.load(
    io.BytesIO(s3_client.get_object(Bucket=BUCKET, Key=f"models/model_v{VERSION}/model.pth").get('Body').read()),
    map_location=device).eval()
tfidf_vectorizer = pickle.loads(
    s3_client.get_object(Bucket=BUCKET, Key=f"models/model_v{VERSION}/tfidf_vectorizer.pkl").get('Body').read())
id2hub = pickle.loads(s3_client.get_object(Bucket=BUCKET, Key=f"models/model_v{VERSION}/id2hub.pkl").get('Body').read())
feedback_s3 = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())

app = FastAPI()

if os.path.exists("/.dockerenv"):
    redis_client = Redis(host='redis', port=6379, db=0)
else:
    redis_client = Redis(host='127.0.0.1', port=6379, db=0)


class PredictRequest(BaseModel):
    text: str
    num_hubs: int = NUM_HUBS


class PredictResponse(BaseModel):
    hubs: List[str]


class PredictRequestFile(BaseModel):
    file: UploadFile = File(...)
    num_hubs: int = NUM_HUBS


class RatingResponse(BaseModel):
    rating: float
    num_feedbacks: int


class PingResponse(BaseModel):
    message: str
    active: bool


class Button(str, Enum):
    button_0 = '0'
    button_1 = '1'
    button_2 = '2'
    button_3 = '3'
    button_4 = '4'
    button_5 = '5'


def generate_cache_key(data: dict):
    """Генерация уникального ключа кэша на основе входящих данных запроса."""
    data_string = json.dumps(data, sort_keys=True)
    return hashlib.md5(data_string.encode('utf-8')).hexdigest()


@app.post("/predict", response_model=PredictResponse)
async def predict(request: PredictRequest):
    # Проверяем, есть ли ответ в кэше
    cache_key = generate_cache_key(request.dict())
    hubs = await redis_client.get(cache_key)

    # Если кэш найден, возвращаем его
    if hubs:
        return PredictResponse(hubs=json.loads(hubs))

    # Если кэша нет, выполняем предсказание
    output = model.predict(request.text, del_puncts, get_tokens,
                           tfidf_vectorizer, id2hub, request.num_hubs, device)
    hubs = [item[0] for item in output]

    # Сохраняем результат в кэше, становим время жизни кэша 1 час
    await redis_client.setex(cache_key, 3600, json.dumps(hubs))

    return PredictResponse(hubs=hubs)


@app.post("/predict_file", response_model=PredictResponse)
async def predict_file(file: UploadFile = File(...), num_hubs: int = NUM_HUBS):
    try:
        text = await file.read()
        text = text.decode('utf-8')
    except Exception:
        return PredictResponse(hubs=[])

    # Проверяем, есть ли ответ в кэше
    cache_key = generate_cache_key({'text': text, 'num_hubs': num_hubs})
    hubs = await redis_client.get(cache_key)

    # Если кэш найден, возвращаем его
    if hubs:
        return PredictResponse(hubs=json.loads(hubs))

    # Если кэша нет, выполняем предсказание
    output = model.predict(text, del_puncts, get_tokens,
                           tfidf_vectorizer, id2hub, num_hubs, device)
    hubs = [item[0] for item in output]

    # Сохраняем результат в кэше, становим время жизни кэша 1 час
    await redis_client.setex(cache_key, 3600, json.dumps(hubs))

    return PredictResponse(hubs=hubs)


@app.post("/feedback")
async def feedback(button: Button) -> bool:
    feedback_s3[button] += 1
    s3_client.put_object(Bucket=BUCKET, Key="feedback.json", Body=json.dumps(feedback_s3))
    return True


@app.get("/rating", response_model=RatingResponse)
async def rating():
    feedback = json.loads(s3_client.get_object(Bucket=BUCKET, Key="feedback.json").get('Body').read())
    num_feedbacks = sum([v for k, v in feedback.items()])
    if num_feedbacks == 0:
        rating = 0.0
    else:
        rating = sum([int(k) * int(v) for k, v in feedback.items()]) / num_feedbacks
    return RatingResponse(rating=rating, num_feedbacks=num_feedbacks)


@app.get("/ping", response_model=PingResponse)
async def ping():
    return PingResponse(message="Сервис готов к работе!", active=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
