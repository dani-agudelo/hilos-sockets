import socket
import threading
import random
import time
from queue import Queue
from pedido import Pedido  # Importar la clase Pedido


class CentralDePedidos:
    def __init__(self, host, puerto, max_pedidos, productos):
        """
        Representa la central de pedidos (servidor).
        :param host: Dirección IP del servidor.
        :param puerto: Puerto del servidor.
        :param max_pedidos: Capacidad máxima de la cola de pedidos.
        :param productos: Diccionario con productos y cantidades disponibles.
        """
        self.host = host
        self.puerto = puerto
        self.productos = productos
        self.cola_pedidos = Queue(max_pedidos)
        self.semaforo = threading.Semaphore(max_pedidos)
        self.lock = threading.Lock()
        self.barrera = threading.Barrier(5)

    def iniciar_servidor(self):
        """
        Inicia el servidor y espera conexiones de clientes.
        """
        servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor_socket.bind((self.host, self.puerto))
        servidor_socket.listen(5)
        print(f"Servidor iniciado en {self.host}:{self.puerto}")

        while True:
            print("Esperando conexiones...")
            cliente_socket, cliente_direccion = servidor_socket.accept()
            print(f"Conexión establecida con {cliente_direccion}")

            hilo_cliente = threading.Thread(
                target=self.gestionar_cliente, args=(cliente_socket,)
            )
            hilo_cliente.start()

    def gestionar_cliente(self, cliente_socket):
        """
        Gestiona la conexión con un cliente.
        :param cliente_socket: Socket del cliente conectado.
        """
        cliente_id = cliente_socket.getpeername()

        # Enviar mensaje de bienvenida y opciones al cliente
        bienvenida = "Bienvenido a la central de pedidos.\n"
        opciones = (
            "Opciones disponibles:\n1. Listar productos\n2. Hacer pedido\n3. Salir\n"
        )
        cliente_socket.sendall((bienvenida + opciones).encode("utf-8"))

        while True:
            datos = cliente_socket.recv(1024).decode("utf-8")
            if not datos:
                break

            if datos == "1":  # Listar productos
                productos_str = "\n".join(
                    [
                        f"{producto}: {cantidad}"
                        for producto, cantidad in self.productos.items()
                    ]
                )
                cliente_socket.sendall(
                    ("Productos disponibles:\n" + productos_str).encode("utf-8")
                )
            elif datos == "2":  # Hacer pedido
                cliente_socket.sendall(
                    "Ingrese los pedidos en el formato 'producto,cantidad'. Escriba 'FIN' para terminar:\n".encode("utf-8")
                )
                while True:
                    pedido_datos = cliente_socket.recv(1024).decode("utf-8")
                    if pedido_datos.upper() == "FIN":
                        cliente_socket.sendall("Pedidos finalizados.\n".encode("utf-8"))
                        break
                    try:
                        producto, cantidad = pedido_datos.split(",")
                        producto = producto.upper()  # Convertir a mayúsculas
                        cantidad = int(cantidad)

                        if producto in self.productos and self.productos[producto] >= cantidad:
                            pedido = Pedido(cliente_id, producto, cantidad)
                            self.encolar_pedido(pedido)
                            cliente_socket.sendall(
                                f"Pedido de {producto} recibido.\n".encode("utf-8")
                            )
                        else:
                            cliente_socket.sendall(
                                f"Error: Producto no disponible o cantidad insuficiente.\n".encode("utf-8")
                            )
                    except ValueError:
                        cliente_socket.sendall(
                            "Error: Formato de pedido inválido. Use 'producto,cantidad'.\n".encode("utf-8")
                        )
                
                # ⬇️ Este menú se envía solo cuando ya terminó el bucle de pedidos
                cliente_socket.sendall(
                    "Opciones disponibles:\n1. Listar productos\n2. Hacer pedido\n3. Salir\n".encode("utf-8")
                )

            elif datos == "3":  # Salir
                cliente_socket.sendall(
                    "Gracias por usar la central de pedidos. Adiós!\n".encode("utf-8")
                )
                break
            else:
                cliente_socket.sendall(
                    "Opción inválida. Por favor, elija una opción válida.\n".encode(
                        "utf-8"
                    )
                )

            # Volver a enviar las opciones después de cada acción
            cliente_socket.sendall(opciones.encode("utf-8"))

        cliente_socket.close()

    def encolar_pedido(self, pedido):
        """
        Encola un pedido en la cola compartida.
        :param pedido: Pedido a encolar.
        """
        self.semaforo.acquire()
        with self.lock:
            self.cola_pedidos.put(pedido)
            print(f"Pedido encolado: {pedido.producto} - {pedido.cantidad}")
        self.semaforo.release()

    def procesar_pedidos(self):
        """
        Procesa los pedidos en la cola compartida.
        """
        while True:
            self.barrera.wait()
            with self.lock:
                if not self.cola_pedidos.empty():
                    pedido = self.cola_pedidos.get()
                    print(f"Procesando pedido: {pedido.producto} - {pedido.cantidad}")
                    time.sleep(random.randint(1, 5))
                    print(f"Pedido procesado: {pedido.producto} - {pedido.cantidad}")
