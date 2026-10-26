from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from models import db, Categoria, Producto, Pedido, DetallePedido, Usuario, Resena, Repartidor, AsignacionPedido, Cliente
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mail
import cloudinary
import cloudinary.uploader

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/menu')
def menu():
    categorias = Categoria.query.all()
    productos  = Producto.query.filter_by(disponible=True).all()
    return render_template('menu.html', categorias=categorias, productos=productos)

@main.route('/carrito')
def carrito():
    return render_template('carrito.html')

@main.route('/pedido', methods=['POST'])
def crear_pedido():
    data = request.get_json()
    try:
        pedido = Pedido(
            cliente_nombre   = data['nombre'],
            cliente_telefono = data['telefono'],
            direccion        = data['direccion'],
            total            = data['total'],
            estado           = 'pendiente',
            cliente_id       = session.get('cliente_id')
        )
        db.session.add(pedido)
        db.session.flush()

        for item in data['items']:
            detalle = DetallePedido(
                pedido_id   = pedido.id,
                producto_id = item['id'],
                cantidad    = item['cantidad'],
                precio_unit = item['precio']
            )
            db.session.add(detalle)

        db.session.commit()

        # Asignar repartidor más cercano
        try:
            repartidores = Repartidor.query.filter_by(disponible=True).all()
            if repartidores:
                import math

                def distancia(r):
                    if r.latitud and r.longitud:
                        lat1 = math.radians(r.latitud)
                        lon1 = math.radians(r.longitud)
                        lat2 = math.radians(-16.5)
                        lon2 = math.radians(-68.15)
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                        return math.sqrt(a)
                    return float('inf')

                repartidor_cercano = min(repartidores, key=distancia)
                asignacion = AsignacionPedido(
                    pedido_id     = pedido.id,
                    repartidor_id = repartidor_cercano.id,
                    estado        = 'pendiente'
                )
                db.session.add(asignacion)
                db.session.commit()
        except Exception as e:
            print(f"Error al asignar repartidor: {e}")


        return jsonify({'success': True, 'pedido_id': pedido.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/admin')
@login_required
def admin():
    from datetime import date, timedelta, datetime
    from sqlalchemy import func

    hoy      = date.today()
    semana   = hoy - timedelta(days=6)
    mes      = hoy.replace(day=1)

    fecha_filtro = request.args.get('fecha', str(hoy))
    try:
        fecha_sel = datetime.strptime(fecha_filtro, '%Y-%m-%d').date()
    except:
        fecha_sel = hoy

    pedidos = Pedido.query.filter(
        db.func.date(Pedido.created_at) == fecha_sel
    ).order_by(Pedido.created_at.desc()).all()

    # Ganancias
    ganancia_hoy = db.session.query(
        func.sum(Pedido.total)
    ).filter(
        func.date(Pedido.created_at) == hoy,
        Pedido.estado != 'cancelado'
    ).scalar() or 0

    ganancia_semana = db.session.query(
        func.sum(Pedido.total)
    ).filter(
        func.date(Pedido.created_at) >= semana,
        Pedido.estado != 'cancelado'
    ).scalar() or 0

    ganancia_mes = db.session.query(
        func.sum(Pedido.total)
    ).filter(
        func.date(Pedido.created_at) >= mes,
        Pedido.estado != 'cancelado'
    ).scalar() or 0

    # Pedidos por dia esta semana
    pedidos_semana = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total_dia = db.session.query(
            func.sum(Pedido.total)
        ).filter(
            func.date(Pedido.created_at) == dia,
            Pedido.estado != 'cancelado'
        ).scalar() or 0
        pedidos_semana.append({
            'dia': ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][dia.weekday()],
            'total': float(total_dia)
        })

    # Productos mas vendidos
    productos_top = db.session.query(
        Producto.nombre,
        Producto.imagen_emoji,
        func.sum(DetallePedido.cantidad).label('total_vendido')
    ).join(DetallePedido).group_by(
        Producto.id, Producto.nombre, Producto.imagen_emoji
    ).order_by(
        func.sum(DetallePedido.cantidad).desc()
    ).limit(5).all()

    # Conteo pedidos hoy
    pedidos_hoy = Pedido.query.filter(
        func.date(Pedido.created_at) == hoy
    ).count()

    return render_template('admin.html',
        pedidos         = pedidos,
        ganancia_hoy    = float(ganancia_hoy),
        ganancia_semana = float(ganancia_semana),
        ganancia_mes    = float(ganancia_mes),
        pedidos_semana  = pedidos_semana,
        productos_top   = productos_top,
        pedidos_hoy     = pedidos_hoy,
        fecha_sel       = fecha_sel,
        hoy             = hoy
    )

@main.route('/admin/pedido/<int:id>', methods=['POST'])
@login_required
def actualizar_estado(id):
    pedido = Pedido.query.get_or_404(id)
    pedido.estado = request.form.get('estado')
    db.session.commit()
    return redirect(url_for('main.admin'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        usuario  = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            return redirect(url_for('main.admin'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/admin/crear-usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        nombre   = request.form.get('nombre')
        email    = request.form.get('email')
        password = request.form.get('password')

        if Usuario.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese correo', 'danger')
            return redirect(url_for('main.crear_usuario'))

        usuario = Usuario(
            nombre   = nombre,
            email    = email,
            password = generate_password_hash(password)
        )
        db.session.add(usuario)
        db.session.commit()
        flash('Cuenta creada correctamente', 'success')
        return redirect(url_for('main.login'))

    return render_template('crear_usuario.html')

@main.route('/admin/productos')
@login_required
def admin_productos():
    productos  = Producto.query.all()
    categorias = Categoria.query.all()
    return render_template('admin_productos.html', productos=productos, categorias=categorias)

import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/admin/productos/agregar', methods=['POST'])
@login_required
def agregar_producto():
    nombre       = request.form.get('nombre')
    descripcion  = request.form.get('descripcion')
    precio       = request.form.get('precio')
    imagen_emoji = request.form.get('imagen_emoji')
    categoria_id = request.form.get('categoria_id')
    imagen_url   = None

    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename != '' and allowed_file(file.filename):
            resultado = cloudinary.uploader.upload(file, folder='rapidfood')
            # imagen subida a Cloudinary
            imagen_url = resultado['secure_url']

    producto = Producto(
        nombre       = nombre,
        descripcion  = descripcion,
        precio       = precio,
        imagen_emoji = imagen_emoji,
        imagen_url   = imagen_url,
        categoria_id = categoria_id,
        disponible   = True
    )
    db.session.add(producto)
    db.session.commit()
    flash('Producto agregado correctamente', 'success')
    return redirect(url_for('main.admin_productos'))

@main.route('/admin/productos/editar/<int:id>', methods=['POST'])
@login_required
def editar_producto(id):
    producto              = Producto.query.get_or_404(id)
    producto.nombre       = request.form.get('nombre')
    producto.descripcion  = request.form.get('descripcion')
    producto.precio       = request.form.get('precio')
    producto.imagen_emoji = request.form.get('imagen_emoji')
    producto.categoria_id = request.form.get('categoria_id')
    producto.disponible   = True if request.form.get('disponible') else False

    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads', filename))
            producto.imagen_url = f'uploads/{filename}'

    db.session.commit()
    flash('Producto actualizado correctamente', 'success')
    return redirect(url_for('main.admin_productos'))

@main.route('/admin/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('main.admin_productos'))

@main.route('/seguimiento', methods=['GET', 'POST'])
def seguimiento():
    if 'cliente_id' not in session:
        return redirect(url_for('main.cliente_login'))

    cliente_id = session['cliente_id']
    pedido_buscado = None

    if request.method == 'POST':
        pedido_id      = request.form.get('pedido_id')
        pedido_buscado = Pedido.query.filter_by(id=pedido_id, cliente_id=cliente_id).first()
        if not pedido_buscado:
            flash('No se encontró el pedido', 'danger')
    elif request.args.get('pedido_id') and request.args.get('pedido_id').isdigit():
        pedido_buscado = Pedido.query.filter_by(
            id=int(request.args.get('pedido_id')), cliente_id=cliente_id
        ).first()

    pedidos = Pedido.query.filter_by(
        cliente_id=cliente_id
    ).order_by(Pedido.created_at.desc()).all()

    return render_template('seguimiento.html', pedidos=pedidos, pedido_buscado=pedido_buscado)

@main.route('/resena/<int:pedido_id>', methods=['GET', 'POST'])
def resena(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    if pedido.estado != 'entregado':
        flash('Solo puedes dejar una reseña cuando tu pedido haya sido entregado', 'danger')
        return redirect(url_for('main.seguimiento'))

    if pedido.resena:
        flash('Ya dejaste una reseña para este pedido', 'danger')
        return redirect(url_for('main.seguimiento'))

    if request.method == 'POST':
        estrellas  = request.form.get('estrellas')
        comentario = request.form.get('comentario')
        nueva_resena = Resena(
            pedido_id  = pedido_id,
            estrellas  = int(estrellas),
            comentario = comentario
        )
        db.session.add(nueva_resena)
        db.session.commit()
        flash('¡Gracias por tu reseña!', 'success')
        return redirect(url_for('main.seguimiento'))

    return render_template('resena.html', pedido=pedido)

@main.route('/admin/resenas')
@login_required
def admin_resenas():
    resenas = Resena.query.order_by(Resena.created_at.desc()).all()
    return render_template('admin_resenas.html', resenas=resenas)
from models import Repartidor, AsignacionPedido

@main.route('/repartidor/registro', methods=['GET', 'POST'])
def repartidor_registro():
    if request.method == 'POST':
        nombre   = request.form.get('nombre')
        telefono = request.form.get('telefono')
        email    = request.form.get('email')
        password = request.form.get('password')

        if Repartidor.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese correo', 'danger')
            return redirect(url_for('main.repartidor_registro'))

        repartidor = Repartidor(
            nombre   = nombre,
            telefono = telefono,
            email    = email,
            password = generate_password_hash(password)
        )
        db.session.add(repartidor)
        db.session.commit()
        flash('Solicitud enviada. Podrás ingresar cuando el administrador te apruebe.', 'warning')
        return redirect(url_for('main.repartidor_login'))

    return render_template('repartidor_registro.html')

@main.route('/repartidor/login', methods=['GET', 'POST'])
def repartidor_login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        rep      = Repartidor.query.filter_by(email=email).first()

        if rep and check_password_hash(rep.password, password):
            if not rep.aprobado:
                flash('Tu cuenta está pendiente de aprobación del administrador', 'warning')
                return redirect(url_for('main.repartidor_login'))
            session['repartidor_id'] = rep.id
            return redirect(url_for('main.repartidor_panel'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('repartidor_login.html')

@main.route('/repartidor/logout')
def repartidor_logout():
    session.pop('repartidor_id', None)
    return redirect(url_for('main.repartidor_login'))

@main.route('/repartidor/panel')
def repartidor_panel():
    if 'repartidor_id' not in session:
        return redirect(url_for('main.repartidor_login'))

    repartidor = Repartidor.query.get(session['repartidor_id'])
    asignaciones = AsignacionPedido.query.filter_by(
        repartidor_id = repartidor.id
    ).filter(
        AsignacionPedido.estado.in_(['pendiente', 'aceptado'])
    ).order_by(AsignacionPedido.created_at.desc()).all()

    return render_template('repartidor_panel.html', repartidor=repartidor, asignaciones=asignaciones)

@main.route('/repartidor/ubicacion', methods=['POST'])
def repartidor_ubicacion():
    if 'repartidor_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json()
    rep  = Repartidor.query.get(session['repartidor_id'])
    rep.latitud   = data['latitud']
    rep.longitud  = data['longitud']
    rep.disponible = data.get('disponible', True)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/repartidor/responder/<int:asignacion_id>', methods=['POST'])
def repartidor_responder(asignacion_id):
    if 'repartidor_id' not in session:
        return redirect(url_for('main.repartidor_login'))

    asignacion = AsignacionPedido.query.get_or_404(asignacion_id)
    respuesta  = request.form.get('respuesta')

    if respuesta == 'aceptar':
        # Verificar que nadie lo haya aceptado ya
        ya_aceptado = AsignacionPedido.query.filter_by(
            pedido_id = asignacion.pedido_id,
            estado    = 'aceptado'
        ).first()

        if ya_aceptado:
            asignacion.estado = 'rechazado'
            db.session.commit()
            flash('Este pedido ya fue aceptado por otro repartidor', 'danger')
            return redirect(url_for('main.repartidor_panel'))

        asignacion.estado               = 'aceptado'
        asignacion.pedido.estado        = 'preparando'
        asignacion.pedido.repartidor_id = asignacion.repartidor_id

        # Rechazar automáticamente las otras asignaciones
        otras = AsignacionPedido.query.filter_by(
            pedido_id = asignacion.pedido_id
        ).filter(AsignacionPedido.id != asignacion.id).all()
        for otra in otras:
            otra.estado = 'rechazado'

        db.session.commit()
        flash('Pedido aceptado', 'success')

    elif respuesta == 'rechazar':
        asignacion.estado = 'rechazado'
        db.session.commit()

        # Buscar siguiente repartidor disponible
        repartidores = Repartidor.query.filter_by(disponible=True, aprobado=True).filter(
            Repartidor.id != asignacion.repartidor_id
        ).all()

        if repartidores:
            nueva_asignacion = AsignacionPedido(
                pedido_id     = asignacion.pedido_id,
                repartidor_id = repartidores[0].id,
                estado        = 'pendiente'
            )
            db.session.add(nueva_asignacion)
            db.session.commit()
            flash('Pedido rechazado, asignado a otro repartidor', 'warning')
        else:
            flash('Pedido rechazado, no hay repartidores disponibles', 'danger')

    return redirect(url_for('main.repartidor_panel'))

@main.route('/admin/repartidores')
@login_required
def admin_repartidores():
    from datetime import date
    hoy = date.today()

    repartidores     = Repartidor.query.all()
    asignaciones_hoy = AsignacionPedido.query.filter(
        db.func.date(AsignacionPedido.created_at) == hoy
    ).count()
    aceptados_hoy    = AsignacionPedido.query.filter(
        db.func.date(AsignacionPedido.created_at) == hoy,
        AsignacionPedido.estado == 'aceptado'
    ).count()
    rechazados_hoy   = AsignacionPedido.query.filter(
        db.func.date(AsignacionPedido.created_at) == hoy,
        AsignacionPedido.estado == 'rechazado'
    ).count()

    return render_template('admin_repartidores.html',
        repartidores     = repartidores,
        asignaciones_hoy = asignaciones_hoy,
        aceptados_hoy    = aceptados_hoy,
        rechazados_hoy   = rechazados_hoy
    )
@main.route('/repartidor/estado-pedido/<int:asignacion_id>', methods=['POST'])
def repartidor_estado_pedido(asignacion_id):
    if 'repartidor_id' not in session:
        return redirect(url_for('main.repartidor_login'))

    asignacion = AsignacionPedido.query.get_or_404(asignacion_id)
    estado     = request.form.get('estado')

    asignacion.pedido.estado = estado
    db.session.commit()

    flash(f'Pedido marcado como {estado}', 'success')
    return redirect(url_for('main.repartidor_panel'))
@main.route('/cliente/registro', methods=['GET', 'POST'])
def cliente_registro():
    if request.method == 'POST':
        nombre   = request.form.get('nombre')
        telefono = request.form.get('telefono')
        email    = request.form.get('email')
        password = request.form.get('password')

        if Cliente.query.filter_by(email=email).first():
            flash('Ya existe una cuenta con ese correo', 'danger')
            return redirect(url_for('main.cliente_registro'))

        cliente = Cliente(
            nombre   = nombre,
            telefono = telefono,
            email    = email,
            password = generate_password_hash(password)
        )
        db.session.add(cliente)
        db.session.commit()
        session['cliente_id'] = cliente.id
        return redirect(url_for('main.menu'))

    return render_template('cliente_registro.html')

@main.route('/cliente/login', methods=['GET', 'POST'])
def cliente_login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        cliente  = Cliente.query.filter_by(email=email).first()

        if cliente and check_password_hash(cliente.password, password):
            session['cliente_id'] = cliente.id
            return redirect(url_for('main.menu'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('cliente_login.html')

@main.route('/cliente/logout')
def cliente_logout():
    session.pop('cliente_id', None)
    return redirect(url_for('main.index'))
@main.route('/admin/repartidores/aprobar/<int:id>', methods=['POST'])
@login_required
def aprobar_repartidor(id):
    rep = Repartidor.query.get_or_404(id)
    rep.aprobado = True
    db.session.commit()
    flash(f'{rep.nombre} fue aprobado como repartidor', 'success')
    return redirect(url_for('main.admin_repartidores'))

@main.route('/admin/repartidores/rechazar/<int:id>', methods=['POST'])
@login_required
def rechazar_repartidor(id):
    rep = Repartidor.query.get_or_404(id)
    if rep.aprobado:
        flash('No se puede rechazar un repartidor ya aprobado', 'danger')
    else:
        db.session.delete(rep)
        db.session.commit()
        flash('Solicitud rechazada', 'warning')
    return redirect(url_for('main.admin_repartidores'))

@main.route('/repartidor/verificar-pedidos')
def repartidor_verificar_pedidos():
    if 'repartidor_id' not in session:
        return jsonify({'nuevos': 0})
    nuevos = AsignacionPedido.query.filter_by(
        repartidor_id = session['repartidor_id'],
        estado        = 'pendiente'
    ).count()
    return jsonify({'nuevos': nuevos})
@main.route('/cancelar-pedido/<int:pedido_id>', methods=['POST'])
def cancelar_pedido(pedido_id):
    if 'cliente_id' not in session:
        return redirect(url_for('main.cliente_login'))

    pedido = Pedido.query.filter_by(
        id         = pedido_id,
        cliente_id = session['cliente_id']
    ).first_or_404()

    if pedido.estado in ['entregado', 'cancelado']:
        flash('Este pedido no se puede cancelar', 'danger')
        return redirect(url_for('main.seguimiento'))

    if pedido.estado == 'en_camino':
        flash('No se puede cancelar, el pedido ya está en camino', 'danger')
        return redirect(url_for('main.seguimiento'))

    pedido.estado = 'cancelado'
    db.session.commit()
    flash('Pedido cancelado correctamente', 'success')
    return redirect(url_for('main.seguimiento'))