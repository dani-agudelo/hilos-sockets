import socket
import threading
import random
import time
from queue import Queue
from pedido import Pedido  # Importar la clase Pedido

# Definir un tipo de "pedido" especial para la señal de inicio
# Podría ser una clase simple o un string, para simplicidad usaremos un string.
INICIO_PROCESAMIENTO_SIGNAL = "INICIO_PROCESAMIENTO"

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
        
        # Sincronización para el inicio de procesamiento de pedidos
        # La barrera espera que 3 hilos de clientes se conecten.
        self.NUM_CLIENTES_REQUERIDOS = 3 
        self.barrera_clientes = threading.Barrier(self.NUM_CLIENTES_REQUERIDOS)
        
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
        # en la cola de pedidos hasta que llegue la señal de inicio.
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

        try:
            print(f"Cliente {cliente_id} esperando a que {self.NUM_CLIENTES_REQUERIDOS} clientes se conecten...")
            # El valor de retorno indica si este hilo es el último en llegar a la barrera
            is_leader = (self.barrera_clientes.wait() == 0) # true si es el último en llegar

            if is_leader:
                print(f"¡{self.NUM_CLIENTES_REQUERIDOS} clientes conectados! La barrera se ha cruzado.")
                # El líder de la barrera pone la señal de inicio en la cola para que los procesadores puedan empezar.
                # Encolamos la señal por cada procesador para despertarlos a todos.
                print("El cliente líder encolará la señal de inicio para los procesadores.")
                for _ in range(self.num_procesadores):
                    self.semaforo.acquire() # Adquirimos el semáforo para la señal de inicio
                    self.cola_pedidos.put(INICIO_PROCESAMIENTO_SIGNAL)
                print("Señales de inicio enviadas a los procesadores.")
            else:
                print(f"Cliente {cliente_id} cruzó la barrera.")

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
            # Solo imprimimos si no es la señal de inicio para evitar ruido.
            if pedido != INICIO_PROCESAMIENTO_SIGNAL: 
                print(f"Pedido encolado: {pedido.producto} - {pedido.cantidad} (Cola actual: {self.cola_pedidos.qsize()})")
        # El semáforo no se libera aquí; se libera cuando el procesador saca un pedido de la cola.

    def procesar_pedidos(self):
        """
        Procesa los pedidos en la cola compartida.
        """
        thread_name = threading.current_thread().name
        
        print(f"{thread_name} esperando la señal de inicio de procesamiento...")
        
        # Cada procesador intentará sacar de la cola. Se bloqueará hasta que haya algo.
        # El primer elemento que saca debe ser la señal de inicio.
        inicio_signal = self.cola_pedidos.get()
        self.semaforo.release() # Liberar el semáforo para la señal de inicio

        if inicio_signal == INICIO_PROCESAMIENTO_SIGNAL:
            print(f"{thread_name} ha recibido la señal de inicio. Empezando a procesar pedidos.")
        else:
            # Esto no debería pasar si la lógica es correcta, pero es un buen control.
            print(f"{thread_name} Error: Recibió un elemento inesperado al inicio: {inicio_signal}")
            # Si el primer elemento no es la señal de inicio, lo volvemos a poner y esperamos el correcto.
            self.semaforo.acquire()
            self.cola_pedidos.put(inicio_signal)
            time.sleep(0.1) # Pequeña pausa para evitar un bucle de error agresivo
            return # Podría reiniciar el bucle si fuera más complejo, pero para el ejemplo, terminamos.


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