import socket
import random

class Cliente:
    def __init__(self, host, puerto):
        """
        Representa un cliente que se conecta al servidor.
        :param host: Dirección IP del servidor.
        :param puerto: Puerto del servidor.
        """
        self.host = host
        self.puerto = puerto

    def realizar_pedidos(self):
        """
        Conecta al servidor y envía pedidos aleatorios.
        """
        cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente_socket.connect((self.host, self.puerto))

        print(cliente_socket.recv(1024).decode('utf-8'))

        for _ in range(random.randint(1, 5)):
            producto = random.choice(["Producto1", "Producto2", "Producto3"])
            cantidad = random.randint(1, 10)
            cliente_socket.sendall(f"{producto},{cantidad}".encode('utf-8'))
            print(cliente_socket.recv(1024).decode('utf-8'))

        cliente_socket.close()