import socket
import time
import random # Importar random para los pedidos aleatorios

class Cliente:
    def __init__(self, host, puerto):
        """
        Representa un cliente que se conecta a la central de pedidos.
        :param host: Dirección IP del servidor.
        :param puerto: Puerto del servidor.
        """
        self.host = host
        self.puerto = puerto
        self.cliente_socket = None

    def conectar(self):
        """
        Conecta el cliente al servidor.
        """
        try:
            self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cliente_socket.connect((self.host, self.puerto))
            print("Conexión establecida con el servidor.")
            return True
        except Exception as e:
            print(f"Error al conectar con el servidor: {e}")
            return False

    def realizar_pedido(self):
        """
        Realiza pedidos al servidor de forma interactiva.
        """
        try:
            # Recibir el mensaje de bienvenida y la lista de productos
            bienvenida = self.cliente_socket.recv(1024).decode("utf-8")
            print(bienvenida)

            # Cada cliente puede enviar una cantidad de "pedidos" (número aleatorio entre 1 y 5)
            num_pedidos_a_realizar = random.randint(1, 5)
            print(f"Este cliente realizará {num_pedidos_a_realizar} pedido(s) aleatorio(s).")

            for i in range(num_pedidos_a_realizar):
                print(f"\n--- Pedido {i+1} de {num_pedidos_a_realizar} ---")
                
                # --- Lógica de Selección de Producto ---
                while True:
                    # El servidor primero envía el prompt de selección de producto
                    prompt_producto = self.cliente_socket.recv(1024).decode("utf-8").strip()
                    print(prompt_producto, end="") # Imprimir el prompt sin salto de línea extra

                    # Solicitar producto al usuario
                    producto_idx = input().strip()
                    self.cliente_socket.sendall(producto_idx.encode("utf-8"))

                    # Recibir la respuesta del servidor para la selección del producto
                    respuesta_producto = self.cliente_socket.recv(1024).decode("utf-8").strip()
                    print(respuesta_producto) # Mostrar la respuesta del servidor

                    if "Número de producto inválido" in respuesta_producto or "Entrada inválida" in respuesta_producto:
                        # Si hay un error, el bucle continuará para pedir el producto de nuevo
                        continue
                    else:
                        # Si la selección es válida, se espera el prompt de cantidad.
                        # Salimos de este bucle para ir a la siguiente etapa.
                        break 
                
                # --- Lógica de Cantidad ---
                while True:
                    # El servidor ahora envía el prompt de cantidad
                    prompt_cantidad = self.cliente_socket.recv(1024).decode("utf-8").strip()
                    print(prompt_cantidad, end="") # Imprimir el prompt sin salto de línea extra

                    # Solicitar cantidad al usuario
                    cantidad = input().strip()
                    self.cliente_socket.sendall(cantidad.encode("utf-8"))

                    # Recibir la respuesta del servidor para la cantidad y el estado del pedido
                    respuesta_cantidad = self.cliente_socket.recv(1024).decode("utf-8").strip()
                    print(respuesta_cantidad) # Mostrar la respuesta del servidor

                    if "Pedido de" in respuesta_cantidad and "recibido." in respuesta_cantidad:
                        # Si el pedido fue exitoso, salimos de este bucle para ir al siguiente pedido (o terminar)
                        break
                    elif "Cantidad no válida" in respuesta_cantidad or "insuficiente en stock" in respuesta_cantidad:
                        # Si hay un error con la cantidad, el bucle continuará para pedir la cantidad de nuevo
                        continue
                    else:
                        # Para cualquier otro mensaje inesperado, podemos imprimirlo y reintentar la cantidad
                        print(f"Respuesta inesperada del servidor: {respuesta_cantidad}. Reintentando cantidad.")
                        continue

        except ConnectionResetError:
            print("El servidor ha cerrado la conexión abruptamente.")
        except Exception as e:
            print(f"Error al realizar pedido: {e}")

    def cerrar_conexion(self):
        """
        Cierra la conexión con el servidor.
        """
        if self.cliente_socket:
            self.cliente_socket.close()
            print("Conexión cerrada.")


if __name__ == "__main__":
    cliente = Cliente("127.0.0.1", 9000) # Usa "127.0.0.1" (localhost) para probar en tu propia máquina
    if cliente.conectar():
        cliente.realizar_pedido()
        cliente.cerrar_conexion()