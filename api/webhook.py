import json
import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Инициализируем клиент AITUNNEL через переменные окружения Vercel.
# Убедитесь, что в панели Vercel добавлен ключ AITUNNEL_API_KEY
ai_client = OpenAI(
    api_key=os.environ.get("AITUNNEL_API_KEY"),
    base_url="https://api.aitunnel.ru/v1"
)

@app.route('/api/webhook', methods=['POST'])
def handler():
    try:
        # Безопасно получаем JSON от Яндекс Диалогов, избегая ошибки 400
        data = request.json or request.get_json(silent=True) or {}
        
        user_message = data.get("request", {}).get("command", "")
        version = data.get("version", "1.0")

        # Если это самый первый запуск навыка (пустая команда), приветствуем пользователя
        if not user_message:
            reply_text = "Привет! Я твой персональный ассистент"
        else:
            # Запрос к нейросети через шлюз AITUNNEL
            completion = ai_client.chat.completions.create(
                model="gpt-4o",  
                messages=[
                    {"role": "system", "content": "Ты полезный голосовой ассистент Алисы. Отвечай кратко, емко, без сложных спецсимволов."},
                    {"role": "user", "content": user_message}
                ],
                timeout=3.5  # <-- Защита от долгого ответа AITUNNEL
            )
            
            # Безопасный разбор ответа с учетом индексов списков
            if completion.choices and len(completion.choices) > 0:
                first_choice = completion.choices[0]
                
                # Проверяем, в каком формате вернулся объект ответа
                if hasattr(first_choice, 'message') and first_choice.message:
                    reply_text = first_choice.message.content
                elif isinstance(first_choice, dict) and 'message' in first_choice:
                    reply_text = first_choice['message'].get('content', '')
                else:
                    reply_text = "Не удалось распознать структуру ответа нейросети."
            else:
                reply_text = "Нейросеть прислала пустой список ответов."

    except Exception as e:
        # В случае любой непредвиденной ошибки возвращаем её текст прямо в Алису для отладки
        reply_text = f"Ошибка на сервере Vercel: {str(e)}"
        version = "1.0"

    # Формируем корректный JSON-ответ для Яндекс Диалогов
    return jsonify({
        "response": {
            "text": reply_text,
            "tts": reply_text,  # Текст, который Алиса произнесет голосом
            "end_session": False
        },
        "version": version
    })
