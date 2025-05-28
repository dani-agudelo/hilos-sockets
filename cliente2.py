import socket

def iniciar_cliente():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('192.168.80.224', 9000)
    print(f"Conectándose a {server_address[0]} puerto {server_address[1]}")
    client.connect(server_address)

    try:
        # Recibir mensaje de bienvenida
        data = client.recv(1024)
        print(data.decode('utf-8'))

        while True:
            comando = input("Escribe tu opción: ").strip()
            client.sendall(comando.encode('utf-8'))

            if comando == "3":  # Salir
                respuesta = client.recv(1024).decode('utf-8')
                print(respuesta)
                break

            respuesta = client.recv(1024).decode('utf-8')
            print(respuesta)
    finally:
        print("Cerrando conexión")
        client.close()

if __name__ == "__main__":
    iniciar_cliente()