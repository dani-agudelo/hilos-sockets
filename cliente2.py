from cliente import Cliente  # Importar la clase Cliente

if __name__ == "__main__":
    cliente = Cliente("192.168.80.224", 9000)
    cliente.conectar()

    while True:
        comando = input("Escribe un comando (LISTAR_PRODUCTOS o SALIR): ").strip()
        if comando.upper() == "SALIR":
            cliente.cerrar_conexion()
            break
        else:
            cliente.enviar_comando(comando)