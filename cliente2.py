from cliente import Cliente  # Importar la clase Cliente

def manejar_opcion(cliente, comando):
    if comando == "1":  # Listar productos
        cliente.enviar_comando("1")
    elif comando == "2":  # Hacer pedido
        cliente.enviar_comando("2")
        while True:
            pedido = input("Escribe el producto y cantidad: ").strip()
            if pedido.upper() == "FIN":
                cliente.enviar_comando("FIN")
                break
            cliente.enviar_comando(pedido)
    elif comando == "3":  # Salir
        cliente.enviar_comando("3")
        cliente.cerrar_conexion()
        return False
    else:
        cliente.enviar_comando(comando)
    return True

if __name__ == "__main__":
    cliente = Cliente("192.168.80.224", 9000)
    cliente.conectar()

    respuesta_inicial = cliente.cliente_socket.recv(1024).decode("utf-8")
    print(respuesta_inicial)

    while True:
        comando = input("Escribe tu opción: ").strip()
        if not manejar_opcion(cliente, comando):
            break