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

            hilo_cliente = threading.Thread(target=self.gestionar_cliente, args=(cliente_socket,))
            hilo_cliente.start()

    def gestionar_cliente(self, cliente_socket):
        """
        Gestiona la conexión con un cliente.
        :param cliente_socket: Socket del cliente conectado.
        """
        cliente_id = cliente_socket.getpeername()
        cliente_socket.sendall("Bienvenido a la central de pedidos.\n".encode('utf-8'))

        while True:
            datos = cliente_socket.recv(1024).decode('utf-8')
            if not datos:
                break

            producto, cantidad = datos.split(',')
            cantidad = int(cantidad)

            pedido = Pedido(cliente_id, producto, cantidad)
            self.encolar_pedido(pedido)

            cliente_socket.sendall(f"Pedido de {producto} recibido.\n".encode('utf-8'))

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