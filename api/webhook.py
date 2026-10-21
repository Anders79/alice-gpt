import json
import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Инициализируем клиент AITUNNEL через переменные окружения Vercel
ai_client = OpenAI(
    api_key=os.environ.get("AITUNNEL_API_KEY"),
    base_url="https://api.aitunnel.ru/v1"
)

@app.route('/api/webhook', methods=['POST'])
def handler():
    try:
        # Получаем JSON от Яндекс Диалогов
        data = request.get_json(force=True)
        user_message = data.get("request", {}).get("command", "")
        version = data.get("version", "1.0")

        if not user_message:
            reply_text = "Привет! Я твой ИИ-ассистент на Vercel через AITUNNEL. О чем поговорим?"
        else:
            # Запрос к нейросети через шлюз AITUNNEL
            completion = ai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты полезный голосовой ассистент Алисы."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply_text = completion.choices.message.content

    except Exception as e:
        reply_text = f"Ошибка на сервере Vercel: {str(e)}"
        version = "1.0"

    # Возвращаем ответ в формате Яндекса
    return jsonify({
        "response": {
            "text": reply_text,
            "tts": reply_text,
            "end_session": False
        },
        "version": version
    })