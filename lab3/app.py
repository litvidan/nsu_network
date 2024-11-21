import tkinter as tk
from time import sleep
from tkinter import ttk, messagebox
import requests
import asyncio
import aiohttp
import threading
from tkinter import scrolledtext
import json

GEOCODING_API_KEY = 'KEY_HERE'
WEATHER_API_KEY = 'KEY_HERE'
MISTRAL_API_KEY = 'KEY_HERE'

async def fetch_weather(session, latitude, longitude):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        return None

async def fetch_story_about_place_stream(session, place_name, place_country, place_city, text_widget):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"Расскажи историю о месте: {place_name}, {place_country}, {place_city}. Опиши его атмосферу, историю и то, что там можно увидеть. В трёх предложениях."
    payload = {
        "model": "codestral-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 150,
        "stream": True  # Включение потоковой передачи
    }

    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)  # Удаляем весь текст
    text_widget.config(state=tk.DISABLED)

    async with session.post(url, headers=headers, json=payload) as response:
        if response.status == 200:
            async for line in response.content:
                if line.startswith(b'data: '):
                    chunk = line[6:].decode('utf-8')
                    if chunk.strip() == "[DONE]":
                        break  # Завершение обработки потока данных
                    if chunk.strip():
                        try:
                            data = json.loads(chunk)
                            content = data['choices'][0]['delta']['content']
                            if content:
                                text_widget.config(state=tk.NORMAL)  # Включаем редактирование для вставки текста
                                text_widget.insert(tk.END, content)
                                text_widget.config(state=tk.DISABLED)  # Отключаем редактирование после вставки текста
                                text_widget.update_idletasks()  # Обновление интерфейса
                        except json.JSONDecodeError as e:
                            print(f"JSONDecodeError: {e}")
                            print(f"Chunk: {chunk}")
        else:
            print(f"Error: {response.status}")
            print(await response.text())

def show_weather_results(weather_info):
    """Создает новое окно для отображения результатов погоды."""
    if weather_info:
        description = weather_info.get('weather', [{'description': 'N/A'}])[0]['description']
        temp = weather_info.get('main', {}).get('temp', 'N/A')
        humidity = weather_info.get('main', {}).get('humidity', 'N/A')

        weather_message = (
            f"Погода:\n"
            f"Описание: {description}\n"
            f"Температура: {temp} °C\n"
            f"Влажность: {humidity}%"
        )
    else:
        weather_message = "Не удалось получить информацию о погоде."

    display_message("Информация о погоде", weather_message, "300x150")

def show_story_results(story):
    """Создает новое окно для отображения рассказа о месте."""
    if story:
        display_message("Рассказ о месте", story, "350x300")
    else:
        display_message("Ошибка", "Не удалось получить рассказ о месте.", "200x100")

def display_message(title, message, geometry):
    """Отображает сообщение в новом окне."""
    message_window = tk.Toplevel(root)
    message_window.title(title)
    message_window.geometry(geometry)

    label = tk.Label(message_window, text=message, wraplength=250)
    label.pack(pady=20)

    close_button = tk.Button(message_window, text="Закрыть", command=message_window.destroy)
    close_button.pack(pady=10)

def on_location_select(event):
    """Обработчик выбора места."""
    selected_item = results.selection()
    if not selected_item:
        return

    item = results.item(selected_item)
    details = item['values']

    latitude = details[4]
    longitude = details[5]
    location_name = details[0]
    location_country = details[1]
    location_city = details[2]

    # Запустить асинхронные запросы в отдельных потоках
    threading.Thread(target=asyncio.run, args=(fetch_story_and_show(location_name, location_country, location_city),)).start()
    sleep(1)
    threading.Thread(target=asyncio.run, args=(fetch_weather_and_show(latitude, longitude),)).start()

async def fetch_weather_and_show(latitude, longitude):
    """Асинхронно загружает погоду и показывает результаты."""
    async with aiohttp.ClientSession() as session:
        weather_data = await fetch_weather(session, latitude, longitude)
        show_weather_results(weather_data)

async def fetch_story_and_show(location_name, location_country, location_city):
    """Асинхронно загружает рассказ о месте и показывает результаты."""
    async with aiohttp.ClientSession() as session:
        await fetch_story_about_place_stream(session, location_name, location_country, location_city, story_text)

def search_location():
    """Функция для выполнения поиска мест."""
    global results

    input_location = entry.get()
    if not input_location:
        messagebox.showwarning("Предупреждение", "Пожалуйста, введите название места.")
        return

    url = "https://graphhopper.com/api/1/geocode"
    query = {
        "q": input_location,
        "locale": "en",
        "limit": "5",
        "reverse": "false",
        "debug": "false",
        "point": "-90.0,-90.0",
        "provider": "default",
        "key": GEOCODING_API_KEY
    }

    try:
        response = requests.get(url, params=query)
        data = response.json()

        if 'hits' not in data or not data['hits']:
            messagebox.showwarning("Нет результатов", "Не удалось найти местоположение.")
            return

        results.delete(*results.get_children())  # Удаляем старые результаты
        for city in data['hits']:
            name = city.get('name', 'N/A')
            country = city.get('country', 'N/A')
            city_name = city.get('city', 'N/A')
            state = city.get('state', 'N/A')
            latitude = city['point']['lat'] if 'point' in city else 'N/A'
            longitude = city['point']['lng'] if 'point' in city else 'N/A'
            score = city.get('score', 'N/A')

            results.insert("", "end", values=(name, country, city_name, state, latitude, longitude, score))

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

# Создаем основное окно
root = tk.Tk()
root.title("Поиск мест")

# Создаем виджеты
label = tk.Label(root, text="Введите название места:")
label.pack(pady=10)

entry = tk.Entry(root, width=50)
entry.pack(pady=10)

search_button = tk.Button(root, text="Поиск", command=search_location)
search_button.pack(pady=10)

# Таблица для отображения результатов
columns = ("Name", "Country", "City", "State", "Latitude", "Longitude", "Score")
results = ttk.Treeview(root, columns=columns, show="headings")

# Настраиваем заголовки столбцов
for col in columns:
    results.heading(col, text=col)

results.pack(pady=10)

# Привязываем выбор элемента в таблице к обработчику событий
results.bind("<<TreeviewSelect>>", on_location_select)

# Виджет для отображения рассказа
story_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, state=tk.DISABLED)
story_text.pack(pady=10)

# Запуск основного цикла приложения
root.mainloop()
