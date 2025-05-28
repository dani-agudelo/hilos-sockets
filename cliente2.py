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
            cliente.cerrar_conexion()
            break
        elif comando == "2":  # Hacer pedido
            print("Ingrese los pedidos en el formato 'producto,cantidad'. Escriba 'FIN' para terminar:")
            while True:
                pedido = input("Escribe el producto y cantidad: ").strip()
                if pedido.upper() == "FIN":
                    cliente.enviar_comando("FIN")
                    break
                cliente.enviar_comando(pedido)
                respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
                print(respuesta)
        else:
            cliente.enviar_comando(comando)
            respuesta = cliente.cliente_socket.recv(1024).decode("utf-8")
            print(respuesta)