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
        else:
            cliente.enviar_comando(comando)