class Pedido:
    def __init__(self, cliente_id, producto, cantidad):
        """
        Representa un pedido realizado por un cliente.
        :param cliente_id: Identificador del cliente.
        :param producto: Nombre del producto solicitado.
        :param cantidad: Cantidad del producto solicitado.
        """
        self.cliente_id = cliente_id
        self.producto = producto
        self.cantidad = cantidad

    def __repr__(self):
        return f"Pedido(Cliente: {self.cliente_id}, Producto: {self.producto}, Cantidad: {self.cantidad})"
