# Используем базовый образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /usr/src/app

# Копируем файл с зависимостями (если есть)
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ваш код в контейнер
COPY . .

# Указываем команду для запуска вашего приложения
CMD ["python", "-u",  "./multicast.py", "224.0.0.1"]