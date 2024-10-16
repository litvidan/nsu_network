import socket
import os
import sys
import struct
from tqdm import tqdm


def send_file(server_ip, server_port, file_path):
    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))

    # Отправляем размер имени файла
    client.send(f"{len(filename):<4}".encode('utf-8'))
    # Отправляем имя файла
    client.send(filename.encode('utf-8'))
    # Отправляем размер файла (8 байт)
    client.send(struct.pack('>Q', filesize))  # 'Q' - беззнаковое 8-байтовое целое, '>' - big endian

    # Используем tqdm для отображения прогресса
    with open(file_path, 'rb') as f:
        with tqdm(total=filesize, unit='B', unit_scale=True, unit_divisor=1024,
                  desc="Передача файла", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} размер: {postfix}') as pbar:
            total_sent = 0
            while total_sent < filesize:
                data = f.read(4096)
                if not data:
                    break

                client.send(data)
                total_sent += len(data)

                # Обновляем прогресс
                pbar.update(len(data))

    client.shutdown(socket.SHUT_WR)

    response = client.recv(1024)
    if response == b'Success':
        print("Файл успешно передан.")
    else:
        print("Ошибка при передаче файла.")

    client.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Использование: python client.py <IP> <порт> <путь к файлу>")
        sys.exit(1)

    s_ip = sys.argv[1]
    s_port = int(sys.argv[2])
    f_path = sys.argv[3]

    send_file(s_ip, s_port, f_path)