import socket

class Cliente:
    def __init__(self, host, puerto):
        self.host = host
        self.puerto = puerto

    def mostrar_productos(self):
        try:
            cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_socket.connect((self.host, self.puerto))
            
            # Solicitar productos al servidor
            cliente_socket.sendall(b"LISTAR_PRODUCTOS")
            
            # Recibir y mostrar productos
            productos = cliente_socket.recv(1024).decode("utf-8")
            print("Productos disponibles:")
            print(productos)
            
            cliente_socket.close()
        except Exception as e:
            print(f"Error al mostrar productos: {e}")