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

        # **CAMBIO AQUÍ: Definimos el número de hilos procesadores y la barrera para ellos.**
        self.num_procesadores = 3 # Ahora tenemos 3 hilos procesadores
        self.barrera = threading.Barrier(self.num_procesadores) # La barrera espera a 3 hilos


    def iniciar_servidor(self):
        """
        Inicia el servidor y espera conexiones de clientes.
        """
        servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor_socket.bind((self.host, self.puerto))
        servidor_socket.listen(5)
        print(f"Servidor iniciado en {self.host}:{self.puerto}")

        # **CAMBIO AQUÍ: Lanzamos los 3 hilos procesadores.**
        for i in range(self.num_procesadores):
            procesador_hilo = threading.Thread(target=self.procesar_pedidos, daemon=True, name=f"Hilo-Procesador-{i+1}")
            procesador_hilo.start()
            print(f"{procesador_hilo.name} iniciado.")


        while True:
            print("Esperando conexiones...")
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
        :param cliente_socket: Socket del cliente conectado.
        :param cliente_direccion: Dirección del cliente.
        """
        cliente_id = cliente_direccion

        # Enviar lista de productos al cliente
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
                # Solicitar producto por número (y esperar la entrada del cliente)
                cliente_socket.sendall(
                    "Seleccione un producto (número):\n".encode("utf-8")
                )
                producto_idx_raw = cliente_socket.recv(1024).decode("utf-8").strip()

                if not producto_idx_raw: # Cliente se desconectó
                    print(f"Cliente {cliente_id} desconectado.")
                    break

                producto = None
                try:
                    producto_idx = int(producto_idx_raw) - 1
                    if producto_idx < 0 or producto_idx >= len(productos_lista):
                        cliente_socket.sendall(
                            "Número de producto inválido. Intente nuevamente.\n".encode("utf-8")
                        )
                        continue # Pide de nuevo el producto
                    producto = productos_lista[producto_idx]
                except ValueError:
                    cliente_socket.sendall(
                        "Entrada inválida. Debe ser un número.\n".encode("utf-8")
                    )
                    continue # Pide de nuevo el producto

                # Solicitar cantidad (y esperar la entrada del cliente)
                cliente_socket.sendall(
                    f"Indique la cantidad para {producto}:\n".encode("utf-8")
                )
                cantidad_raw = cliente_socket.recv(1024).decode("utf-8").strip()

                if not cantidad_raw: # Cliente se desconectó
                    print(f"Cliente {cliente_id} desconectado.")
                    break

                try:
                    cantidad = int(cantidad_raw)
                    with self.lock: # Proteger acceso al stock
                        if cantidad <= 0 or self.productos[producto] < cantidad:
                            cliente_socket.sendall(
                                "Cantidad no válida o insuficiente en stock.\n".encode("utf-8")
                            )
                            continue # Pide de nuevo la cantidad
                        
                        # Si todo es válido, encolar el pedido
                        pedido = Pedido(cliente_id, producto, cantidad)
                        self.encolar_pedido(pedido)
                        self.productos[producto] -= cantidad
                        cliente_socket.sendall(
                            f"Pedido de {producto} x {cantidad} recibido.\n".encode("utf-8")
                        )
                        # El cliente enviará un nuevo producto/cantidad después de recibir esto.
                        # Aquí puedes agregar un "break" si el cliente solo debe hacer 1 pedido por conexión.

                except ValueError:
                    cliente_socket.sendall(
                        "Cantidad no válida. Debe ser un número.\n".encode("utf-8")
                    )
                    continue # Pide de nuevo la cantidad

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
        print(f"{thread_name} listo para procesar pedidos. Esperando a los demás procesadores en la barrera...")
        
        # **CAMBIO AQUÍ: La barrera se espera UNA VEZ al inicio del ciclo de vida del procesador.**
        try:
            # Los 3 hilos procesadores se bloquearán aquí hasta que todos lleguen a este punto.
            # Una vez que los 3 estén aquí, todos cruzarán la barrera al mismo tiempo.
            self.barrera.wait()
            print(f"{thread_name} cruzó la barrera. Empezando a procesar pedidos.")
        except threading.BrokenBarrierError:
            print(f"{thread_name} Barrera rota, terminando.")
            return # Termina el hilo si la barrera se rompe

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
                time.sleep(0.5) # Pausa para evitar un bucle de error rápido


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
    ) # Usar localhost para pruebas en tu propia máquina

    # Iniciar el servidor en un hilo
    servidor_hilo = threading.Thread(target=central.iniciar_servidor, daemon=True)
    servidor_hilo.start()

    print("Servidor iniciado. Presione Ctrl+C para detener.")
    try:
        while True:
            time.sleep(1) # Mantener el hilo principal activo
    except KeyboardInterrupt:
        print("\nServidor detenido.")