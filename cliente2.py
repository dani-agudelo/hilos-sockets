from cliente import Cliente  # Importar la clase Cliente

if __name__ == "__main__":
    cliente = Cliente("192.168.80.224", 9000)  
    cliente.mostrar_productos()