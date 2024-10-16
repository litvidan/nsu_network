import socket
import threading
import os
import time
import struct
from format import *


def handle_client(client_socket, address):
    print(f"Подключен к клиенту {address}")

    # Получаем имя файла
    filename_size = int(client_socket.recv(4).decode('utf-8'))
    filename = client_socket.recv(filename_size).decode('utf-8')
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Получаем размер файла (8 байт)
    data = client_socket.recv(8)
    filesize = struct.unpack('>Q', data)[0]  # 'Q' - беззнаковое 8-байтовое целое

    total_received = 0
    instant_received = 0
    start_time = time.time()
    last_time = start_time

    print(f"Получаю файл {filename} размера {format_size(filesize)}")
    with open(filepath, 'wb') as f:
        while total_received < filesize:
            data = client_socket.recv(4096)
            if not data:
                break

            f.write(data)
            total_received += len(data)
            instant_received += len(data)

            current_time = time.time()
            elapsed_time = current_time - last_time
            total_elapsed_time = current_time - start_time

            # Выводим скорость раз в 3 секунды
            if elapsed_time >= 3 or total_received == filesize:
                instant_speed = instant_received / elapsed_time if elapsed_time > 0 else 0 # Почему-то мгновенная скорость сильно отличается от средней
                avg_speed = total_received / total_elapsed_time if total_elapsed_time > 0 else 0
                print(f"Клиент {address} - Мгновенная скорость: {format_speed(instant_speed)}, Средняя скорость: {format_speed(avg_speed)}")
                last_time = current_time
                instant_received = 0

    # Проверяем, совпадает ли размер полученных данных с отправленным
    if total_received == filesize:
        print(f"Файл {filename} успешно получен.")
        client_socket.send(b'Success')
    else:
        print("Ошибка при получении файла.")
        client_socket.send(b'Fail')
    client_socket.close()


def start_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    print(f"Сервер запущен на порту {port}. IP адрес {socket.gethostbyname(socket.gethostname())}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()


if __name__ == "__main__":
    import sys

    # Папка для сохранения загруженных файлов
    UPLOAD_DIR = "uploads"

    # Создаем папку для загрузок, если ее нет
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    if len(sys.argv) != 2:
        print("Использование: python server.py <порт>")
        sys.exit(1)

    start_server(int(sys.argv[1]))