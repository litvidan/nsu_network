import socket
import threading
import time
import sys
import uuid
import ipaddress


class MulticastDiscovery:
    def __init__(self, multicast_group, ttl=10, check_interval=1):
        self.multicast_group = multicast_group
        self.port = 50000
        self.active_ips = {}
        self.running = True
        self.ttl = ttl
        self.check_interval = check_interval

        if ':' in multicast_group:
            self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY,0)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))

        if ':' in multicast_group:
            group = socket.inet_pton(socket.AF_INET6, multicast_group)
            self.sock.setsockopt(socket.IPPROTO_IPV6, socket.IP_ADD_MEMBERSHIP,
                             group + b'\x00\x00\x00\x00\x00\x00\x00\x00')
        else:
            group = socket.inet_pton(socket.AF_INET, multicast_group)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                             group + socket.inet_pton(socket.AF_INET, '0.0.0.0'))


    def send_message(self):
        unique_id = str(uuid.uuid4())
        while self.running:
            message = f"Hello from {socket.gethostbyname(socket.gethostname())} - ID: {unique_id}"
            self.sock.sendto(message.encode(), (self.multicast_group, self.port))
            time.sleep(2)

    def receive_messages(self):
        while self.running:
            try:
                data, address = self.sock.recvfrom(50000)
                ip = address[0]
                message = data.decode()

                if ip not in self.active_ips:
                    self.active_ips[ip] = time.time()
                    self.show_active_ips()
            except Exception as e:
                print(f"Error receiving messages: {e}")

    def check_active_ips(self):
        while self.running:
            current_time = time.time()
            to_remove = [ip for ip, timestamp in self.active_ips.items() if current_time - timestamp > self.ttl]

            for ip in to_remove:
                del self.active_ips[ip]

            if to_remove:
                self.show_active_ips()

            time.sleep(self.check_interval)

    def show_active_ips(self):
        print("Active IPs in the network:")
        for ip in sorted(self.active_ips):
            print(ip)
        print("-" * 30)

    def run(self):
        sender_thread = threading.Thread(target=self.send_message)
        receiver_thread = threading.Thread(target=self.receive_messages)
        checker_thread = threading.Thread(target=self.check_active_ips)

        sender_thread.start()
        receiver_thread.start()
        checker_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            sender_thread.join()
            receiver_thread.join()
            checker_thread.join()
            self.sock.close()
            print("\nMulticast discovery stopped.")

def is_multicast(ip):
    try:
        if ':' in ip:
            ipv6 = ipaddress.IPv6Address(ip)
            return ipv6.is_multicast
        else:
            ipv4 = ipaddress.IPv4Address(ip)
            return ipv4.is_multicast
    except ValueError:
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error. Invalid number of arguments")
        sys.exit(1)

    multicast_group = sys.argv[1]

    if is_multicast(multicast_group):
        discovery_app = MulticastDiscovery(multicast_group)
        discovery_app.run()
    else:
        print("Error. Invalid address")