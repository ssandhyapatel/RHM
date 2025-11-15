
import socket
import json

class SocketStreamer:
    def __init__(self, host='127.0.0.1', port=5010):
        self.host = host
        self.port = port
        # UDP 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.target = (self.host, self.port)
        self.running = False
        print(f"[UDPStreamer] Ready to send UDP packets to {self.host}:{self.port}")

    def start(self):
        self.running = True
       

    def send(self, data_dict):
        if not self.running:
            print("[UDPStreamer] Not started. Call start() first.")
            return
        try:
            message = json.dumps(data_dict)
            self.sock.sendto(message.encode('utf-8'), self.target)
            # print(f"[UDPStreamer] Sent: {message}")
        except Exception as e:
            print(f"[UDPStreamer] Send failed: {e}")

    def stop(self):
        try:
            self.sock.close()
        except Exception:
            pass
        self.running = False
        print("[UDPStreamer] Socket closed.")
