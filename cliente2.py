from cliente import Cliente  # Importar la clase Cliente

def manejar_opcion(cliente, comando):
    if comando == "1":  # Listar productos
        cliente.enviar_comando("1")
        respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
        print(respuesta)
    elif comando == "2":  # Hacer pedido
        cliente.enviar_comando("2")
        respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
        print(respuesta)
        while True:
            pedido = input("Escribe el producto y cantidad: ").strip()
            if pedido.upper() == "FIN":
                cliente.enviar_comando("FIN")
                respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
                print(respuesta)
                break
            cliente.enviar_comando(pedido)
            respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
            print(respuesta)
    elif comando == "3":  # Salir
        cliente.enviar_comando("3")
        respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
        print(respuesta)
        cliente.cerrar_conexion()
        return False
    else:
        cliente.enviar_comando(comando)
        respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
        print(respuesta)
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