import socket
import threading
import time
import sys
import uuid

class MulticastDiscovery:
    def __init__(self, multicast_group):
        self.multicast_group = multicast_group
        self.port = 50000
        self.active_ips = set()  # Храним активные IP-адреса
        self.running = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))

        group = socket.inet_pton(socket.AF_INET, multicast_group)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                             group + socket.inet_pton(socket.AF_INET, '0.0.0.0'))

    def send_message(self):
        unique_id = str(uuid.uuid4())  # Генерируем уникальный идентификатор
        while self.running:
            message = f"Hello from {socket.gethostbyname(socket.gethostname())} - ID: {unique_id}"
            self.sock.sendto(message.encode(), (self.multicast_group, self.port))
            print(f"Sent: {message}")
            time.sleep(2)

    def receive_messages(self):
        while self.running:
            try:
                data, address = self.sock.recvfrom(50000)
                ip = address[0]
                message = data.decode()
                print(f"Received '{message}' from {ip}")

                if ip not in self.active_ips:
                    self.active_ips.add(ip)
                    self.show_active_ips()
            except Exception as e:
                print(f"Error receiving messages: {e}")

    def show_active_ips(self):
        print("Active IPs in the network:")
        for ip in sorted(self.active_ips):
            print(ip)
        print("-" * 30)

    def run(self):
        sender_thread = threading.Thread(target=self.send_message)
        receiver_thread = threading.Thread(target=self.receive_messages)

        sender_thread.start()
        receiver_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            sender_thread.join()
            receiver_thread.join()
            self.sock.close()
            print("\nMulticast discovery stopped.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python multicast_discovery.py <multicast_group>")
        sys.exit(1)

    multicast_group = sys.argv[1]
    discovery_app = MulticastDiscovery(multicast_group)
    discovery_app.run()