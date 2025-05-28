from cliente import Cliente  # Importar la clase Cliente

if __name__ == "__main__":
    cliente = Cliente("192.168.80.224", 9000)
    cliente.conectar()

    while True:
        comando = input("Escribe tu opción: ").strip()  # El servidor ya envió las opciones
        if comando == "3":  # Salir
            cliente.cerrar_conexion()
            break
        else:
            cliente.enviar_comando(comando)