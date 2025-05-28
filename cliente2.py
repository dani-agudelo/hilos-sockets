from cliente import Cliente  # Importar la clase Cliente

if __name__ == "__main__":
    cliente = Cliente("192.168.80.224", 9000)
    cliente.conectar()

    # Recibir el mensaje inicial del servidor (bienvenida y opciones)
    respuesta_inicial = cliente.cliente_socket.recv(1024).decode("utf-8")
    print(respuesta_inicial)

    while True:
        comando = input("Escribe tu opción: ").strip()
        if comando == "3":  # Salir
            cliente.enviar_comando("3")  # Enviar opción antes de cerrar
            respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
            print(respuesta)
            cliente.cerrar_conexion()
            break
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
        else:
            cliente.enviar_comando(comando)
            respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
            print(respuesta)
