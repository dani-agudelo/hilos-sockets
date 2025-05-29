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
        self.cola_pedidos = Queue(max_pedidos)  # Cola para pedidos con capacidad máxima
        self.semaforo = threading.Semaphore(max_pedidos)  # Semáforo para controlar la capacidad de la cola
        self.lock = threading.Lock()  # Lock para sincronizar el acceso a la cola y al stock
        
        # **Sincronización para el inicio de procesamiento de pedidos**
        # La barrera ahora espera que 3 hilos de clientes se conecten.
        self.NUM_CLIENTES_REQUERIDOS = 3 
        self.barrera_clientes = threading.Barrier(self.NUM_CLIENTES_REQUERIDOS)
        
        # Variable de condición para indicar a los hilos procesadores que pueden iniciar
        self.procesadores_listos = threading.Condition()
        self.listos_para_procesar = False # Bandera para controlar el estado

        # Los hilos procesadores (operadores)
        self.num_procesadores = 3
        self.hilos_procesadores = []


    def iniciar_servidor(self):
        """
        Inicia el servidor y espera conexiones de clientes.
        """
        servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor_socket.bind((self.host, self.puerto))
        servidor_socket.listen(5)
        print(f"Servidor iniciado en {self.host}:{self.puerto}")

        # Lanzamos los hilos procesadores. Estos hilos se quedarán esperando
        # hasta que la bandera 'listos_para_procesar' sea True.
        for i in range(self.num_procesadores):
            procesador_hilo = threading.Thread(target=self.procesar_pedidos, daemon=True, name=f"Hilo-Procesador-{i+1}")
            self.hilos_procesadores.append(procesador_hilo)
            procesador_hilo.start()
            print(f"{procesador_hilo.name} iniciado y esperando la señal de los clientes.")

        while True:
            print("Esperando conexiones de clientes...")
            try:
                cliente_socket, cliente_direccion = servidor_socket.accept()
                print(f"Conexión establecida con {cliente_direccion}")

                hilo_cliente = threading.Thread(
                    target=self.gestionar_cliente, args=(cliente_socket, cliente_direccion), daemon=True
                )
                hilo_cliente.start()
            except Exception as e:
                print(f"Error al aceptar conexión: {e}")
                break

    def gestionar_cliente(self, cliente_socket, cliente_direccion):
        """
        Gestiona la conexión con un cliente.
        Este es el hilo de cliente que participará en la barrera.
        :param cliente_socket: Socket del cliente conectado.
        :param cliente_direccion: Dirección del cliente.
        """
        cliente_id = cliente_direccion
        print(f"Hilo de cliente para {cliente_id} iniciado.")

        # Cada hilo de cliente se bloqueará aquí hasta que 3 clientes se conecten.
        try:
            print(f"Cliente {cliente_id} esperando a que {self.NUM_CLIENTES_REQUERIDOS} clientes se conecten...")
            # El valor de retorno indica si este hilo es el último en llegar a la barrera
            # (es el "lider" de la barrera). Solo el líder notificará a los procesadores.
            is_leader = (self.barrera_clientes.wait() == 0) # true si es el último en llegar

            if is_leader:
                print(f"¡{self.NUM_CLIENTES_REQUERIDOS} clientes conectados! La barrera se ha cruzado.")
                with self.procesadores_listos:
                    self.listos_para_procesar = True
                    self.procesadores_listos.notify_all() # Despierta a todos los hilos procesadores
            else:
                print(f"Cliente {cliente_id} cruzó la barrera. Esperando señal de inicio de procesamiento.")

        except threading.BrokenBarrierError:
            print(f"Cliente {cliente_id} Barrera rota, terminando gestión de cliente.")
            cliente_socket.close()
            return
        
        # Continuar con la interacción del cliente
        productos_lista = list(self.productos.keys())
        productos_str = "\n".join(
            [
                f"{idx + 1}. {producto}: {self.productos[producto]}"
                for idx, producto in enumerate(productos_lista)
            ]
        )
        bienvenida = f"Bienvenido a la central de pedidos.\nProductos disponibles:\n{productos_str}\n"
        cliente_socket.sendall(bienvenida.encode("utf-8"))

        while True:
            try:
                cliente_socket.sendall(
                    "Seleccione un producto (número):\n".encode("utf-8")
                )
                producto_idx_raw = cliente_socket.recv(1024).decode("utf-8").strip()

                if not producto_idx_raw: 
                    print(f"Cliente {cliente_id} desconectado.")
                    break

                producto = None
                try:
                    producto_idx = int(producto_idx_raw) - 1
                    if producto_idx < 0 or producto_idx >= len(productos_lista):
                        cliente_socket.sendall(
                            "Número de producto inválido. Intente nuevamente.\n".encode("utf-8")
                        )
                        continue 
                    producto = productos_lista[producto_idx]
                except ValueError:
                    cliente_socket.sendall(
                        "Entrada inválida. Debe ser un número.\n".encode("utf-8")
                    )
                    continue 

                cliente_socket.sendall(
                    f"Indique la cantidad para {producto}:\n".encode("utf-8")
                )
                cantidad_raw = cliente_socket.recv(1024).decode("utf-8").strip()

                if not cantidad_raw: 
                    print(f"Cliente {cliente_id} desconectado.")
                    break

                try:
                    cantidad = int(cantidad_raw)
                    with self.lock: # Proteger acceso al stock
                        if cantidad <= 0 or self.productos[producto] < cantidad:
                            cliente_socket.sendall(
                                "Cantidad no válida o insuficiente en stock.\n".encode("utf-8")
                            )
                            continue 
                        
                        pedido = Pedido(cliente_id, producto, cantidad)
                        self.encolar_pedido(pedido)
                        self.productos[producto] -= cantidad
                        cliente_socket.sendall(
                            f"Pedido de {producto} x {cantidad} recibido.\n".encode("utf-8")
                        )

                except ValueError:
                    cliente_socket.sendall(
                        "Cantidad no válida. Debe ser un número.\n".encode("utf-8")
                    )
                    continue 

            except ConnectionResetError:
                print(f"Cliente {cliente_id} ha cerrado la conexión abruptamente.")
                break
            except Exception as e:
                print(f"Error con el cliente {cliente_id}: {e}")
                break

        cliente_socket.close()
        print(f"Conexión con {cliente_id} cerrada.")

    def encolar_pedido(self, pedido):
        """
        Encola un pedido en la cola compartida.
        Adquiere un permiso del semáforo para limitar la cantidad de pedidos en la cola.
        :param pedido: Pedido a encolar.
        """
        self.semaforo.acquire() # Espera si la cola está llena (semáforo en 0)
        with self.lock: # Protege el acceso a la cola
            self.cola_pedidos.put(pedido)
            print(f"Pedido encolado: {pedido.producto} - {pedido.cantidad} (Cola actual: {self.cola_pedidos.qsize()})")
        # El semáforo no se libera aquí; se libera cuando el procesador saca un pedido de la cola.

    def procesar_pedidos(self):
        """
        Procesa los pedidos en la cola compartida.
        """
        thread_name = threading.current_thread().name
        
        # **CAMBIO AQUÍ: Los hilos procesadores esperan una señal.**
        with self.procesadores_listos:
            while not self.listos_para_procesar:
                print(f"{thread_name} esperando que los clientes crucen la barrera para empezar...")
                self.procesadores_listos.wait() # Se libera el lock y el hilo espera

        print(f"{thread_name} ha recibido la señal. Empezando a procesar pedidos.")

        while True:
            try:
                # Obtener un pedido de la cola. Esto se bloqueará si la cola está vacía.
                pedido = self.cola_pedidos.get()
                self.semaforo.release() # Libera un permiso del semáforo porque un pedido ha sido procesado

                print(f"{thread_name} procesando pedido: {pedido.producto} - {pedido.cantidad}")
                time.sleep(random.randint(1, 5))  # Simula el tiempo de procesamiento
                print(f"{thread_name} pedido procesado: {pedido.producto} - {pedido.cantidad}")

            except Exception as e:
                print(f"{thread_name} error al procesar pedido: {e}")
                time.sleep(0.5) 


# Clase Pedido (guárdala en un archivo 'pedido.py')
class Pedido:
    def __init__(self, cliente_id, producto, cantidad):
        self.cliente_id = cliente_id
        self.producto = producto
        self.cantidad = cantidad

    def __repr__(self):
        return f"Pedido(Cliente: {self.cliente_id}, Producto: {self.producto}, Cantidad: {self.cantidad})"

if __name__ == "__main__":
    # Configuración del servidor
    productos_disponibles = {"Producto1": 100, "Producto2": 50, "Producto3": 75}
    central = CentralDePedidos(
        "127.0.0.1", 9000, max_pedidos=10, productos=productos_disponibles
    ) 

    # Iniciar el servidor en un hilo
    servidor_hilo = threading.Thread(target=central.iniciar_servidor, daemon=True)
    servidor_hilo.start()

    print("Servidor iniciado. Presione Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        print("\nServidor detenido.")