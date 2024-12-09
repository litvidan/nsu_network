import socket
import select
import threading


class SOCKS5Proxy:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"SOCKS5 Proxy server running on {self.host}:{self.port}")

    def handle_client(self, client_socket):
        # Аутентификация
        version, nmethods = client_socket.recv(2)

        methods = []
        for i in range(nmethods):
            methods.append(ord(client_socket.recv(1)))
        if methods != [0]:
            return

        client_socket.sendall(b'\x05\x00')  # Выбор метода аутентификации (no authentication)

        # Команда подключения
        request = client_socket.recv(4)
        if request[1] != 1:  # Если команда не CONNECT
            client_socket.close()
            return

        addr_type = request[3]
        if addr_type == 1:  # IPv4
            addr = socket.inet_ntoa(client_socket.recv(4))
        elif addr_type == 3:  # DNS
            domain_length = client_socket.recv(1)[0]
            addr = client_socket.recv(domain_length)
            addr = addr.decode()
        elif addr_type == 4:  # IPv6
            addr = socket.inet_ntop(socket.AF_INET6, client_socket.recv(16))
        else:
            client_socket.close()
            return

        port = int.from_bytes(client_socket.recv(2), 'big')

        # Подключение к целевому хосту
        try:
            if addr_type == 3:  # Если это доменное имя, мы должны использовать getaddrinfo
                remote_address = socket.getaddrinfo(addr, port)[0][4]  # Получаем IP-адрес
            else:
                remote_address = (addr, port)

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect(remote_address)
            client_socket.sendall(b'\x05\x00\x00\x01' + socket.inet_aton(remote_address[0]) + port.to_bytes(2, 'big'))
        except Exception as e:
            print(f"Connection failed: {e}")
            client_socket.sendall(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
            client_socket.close()
            return

            # Перенаправление данных между клиентом и удаленным сервером
        while True:
            r, _, _ = select.select([client_socket, remote_socket], [], [])
            if client_socket in r:
                data = client_socket.recv(4096)
                if not data:
                    break
                remote_socket.sendall(data)
            if remote_socket in r:
                data = remote_socket.recv(4096)
                if not data:
                    break
                client_socket.sendall(data)

        client_socket.close()
        remote_socket.close()

    def start(self):
        while True:
            client_socket, addr = self.server.accept()
            print(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()


if __name__ == '__main__':
    proxy = SOCKS5Proxy()
    proxy.start()