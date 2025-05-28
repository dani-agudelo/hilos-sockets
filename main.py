from central_de_pedidos import CentralDePedidos
from cliente import Cliente
import threading

if __name__ == "__main__":
    # Configuración del servidor
    productos_disponibles = {"Producto1": 100, "Producto2": 50, "Producto3": 75}
    central = CentralDePedidos("192.168.80.224", 9000, max_pedidos=10, productos=productos_disponibles)

    # Iniciar el servidor en un hilo
    servidor_hilo = threading.Thread(target=central.iniciar_servidor)
    servidor_hilo.start()

    # Iniciar procesamiento de pedidos en otro hilo
    procesador_hilo = threading.Thread(target=central.procesar_pedidos)
    procesador_hilo.start()