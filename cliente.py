import socket

class Cliente:
    def __init__(self, host, puerto):
        self.host = host
        self.puerto = puerto
        self.cliente_socket = None

    def conectar(self):
        try:
            self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cliente_socket.connect((self.host, self.puerto))
            print("Conexión establecida con el servidor.")
        except Exception as e:
            print(f"Error al conectar con el servidor: {e}")

    def enviar_comando(self, comando):
        try:
            if self.cliente_socket:
                # Enviar comando al servidor
                self.cliente_socket.sendall(comando.encode("utf-8"))
                
                # Recibir respuesta del servidor
                respuesta = self.cliente_socket.recv(1024).decode("utf-8")
                print("Respuesta del servidor:")
                print(respuesta)
            else:
                print("No hay conexión activa con el servidor.")
        except Exception as e:
            print(f"Error al enviar comando: {e}")

    def cerrar_conexion(self):
        if self.cliente_socket:
            self.cliente_socket.close()
            print("Conexión cerrada.")
