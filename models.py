from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id        = db.Column(db.Integer, primary_key=True)
    nombre    = db.Column(db.String(50), nullable=False)
    icono     = db.Column(db.String(10))
    productos = db.relationship('Producto', backref='categoria', lazy=True)

class Producto(db.Model):
    __tablename__ = 'productos'
    id           = db.Column(db.Integer, primary_key=True)
    nombre       = db.Column(db.String(100), nullable=False)
    descripcion  = db.Column(db.Text)
    precio       = db.Column(db.Numeric(10, 2), nullable=False)
    imagen_emoji = db.Column(db.String(10))
    imagen_url   = db.Column(db.String(200))
    disponible   = db.Column(db.Boolean, default=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id               = db.Column(db.Integer, primary_key=True)
    cliente_nombre   = db.Column(db.String(100), nullable=False)
    cliente_telefono = db.Column(db.String(20))
    direccion        = db.Column(db.Text, nullable=False)
    total            = db.Column(db.Numeric(10, 2), nullable=False)
    estado          = db.Column(db.String(20), default='pendiente')
    repartidor_id   = db.Column(db.Integer, db.ForeignKey('repartidores.id'), nullable=True)
    cliente_id      = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    items           = db.relationship('DetallePedido', backref='pedido', lazy=True)
    repartidor      = db.relationship('Repartidor', backref='pedidos')

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedidos'
    id          = db.Column(db.Integer, primary_key=True)
    pedido_id   = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad    = db.Column(db.Integer, nullable=False)
    precio_unit = db.Column(db.Numeric(10, 2), nullable=False)
    producto    = db.relationship('Producto')
from flask_login import UserMixin

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Usuario {self.email}>'
class Resena(db.Model):
    __tablename__ = 'resenas'
    id         = db.Column(db.Integer, primary_key=True)
    pedido_id  = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    estrellas  = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pedido     = db.relationship('Pedido', backref='resena')

    def __repr__(self):
        return f'<Resena pedido#{self.pedido_id} - {self.estrellas}★>'
class Repartidor(db.Model):
    __tablename__ = 'repartidores'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)
    telefono   = db.Column(db.String(20))
    email      = db.Column(db.String(100), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    latitud    = db.Column(db.Float)
    longitud   = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Repartidor {self.nombre}>'


class AsignacionPedido(db.Model):
    __tablename__ = 'asignaciones_pedido'
    id             = db.Column(db.Integer, primary_key=True)
    pedido_id      = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    repartidor_id  = db.Column(db.Integer, db.ForeignKey('repartidores.id'), nullable=False)
    estado         = db.Column(db.String(20), default='pendiente')
    # estados: pendiente | aceptado | rechazado
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    pedido         = db.relationship('Pedido', backref='asignaciones')
    repartidor     = db.relationship('Repartidor', backref='asignaciones')

    def __repr__(self):
        return f'<Asignacion pedido#{self.pedido_id} repartidor#{self.repartidor_id}>'
class Cliente(db.Model, UserMixin):
    __tablename__ = 'clientes'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)
    telefono   = db.Column(db.String(20))
    email      = db.Column(db.String(100), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pedidos    = db.relationship('Pedido', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.email}>'