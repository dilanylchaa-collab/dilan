let carrito = JSON.parse(localStorage.getItem('carrito')) || [];

function actualizarContador() {
    const total = carrito.reduce((sum, item) => sum + item.cantidad, 0);
    const badge = document.getElementById('cart-count');
    if (badge) badge.textContent = total;
}

function agregarAlCarrito(id, nombre, precio, btn) {
    const existe = carrito.find(i => i.id === id);
    if (existe) {
        existe.cantidad++;
    } else {
        carrito.push({ id: id, nombre: nombre, precio: parseFloat(precio), cantidad: 1 });
    }
    localStorage.setItem('carrito', JSON.stringify(carrito));
    actualizarContador();

    btn.innerHTML = '<i class="ti ti-check"></i> Agregado';
    btn.style.background = '#16a34a';
    setTimeout(() => {
        btn.innerHTML = '<i class="ti ti-plus"></i> Agregar';
        btn.style.background = '#f97316';
    }, 1000);
}

function filtrar(categoriaId, btn) {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.food-card').forEach(card => {
        if (categoriaId === 'todos' || card.dataset.categoria == categoriaId) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function renderCarrito() {
    const lista   = document.getElementById('lista-carrito');
    const vacio   = document.getElementById('carrito-vacio');
    const resumen = document.getElementById('resumen-detalle');
    const totalEl = document.getElementById('total-precio');

    if (!lista) return;

    if (carrito.length === 0) {
        lista.innerHTML = '';
        if (vacio) vacio.style.display = 'block';
        if (resumen) resumen.innerHTML = '';
        if (totalEl) totalEl.textContent = 'Bs. 0.00';
        return;
    }

    if (vacio) vacio.style.display = 'none';

    lista.innerHTML = carrito.map(item => `
        <div class="item-carrito">
            <div class="item-info">
                <div class="item-nombre">${item.nombre}</div>
                <div class="item-precio">Bs. ${parseFloat(item.precio).toFixed(2)} c/u</div>
            </div>
            <div class="item-controles">
                <button class="btn-cantidad" onclick="cambiarCantidad(${item.id}, -1)">−</button>
                <span class="cantidad-num">${item.cantidad}</span>
                <button class="btn-cantidad" onclick="cambiarCantidad(${item.id}, 1)">+</button>
                <button class="btn-eliminar" onclick="eliminarItem(${item.id})">
                    <i class="ti ti-trash"></i>
                </button>
            </div>
        </div>
    `).join('');

    const total = carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);

    if (resumen) {
        resumen.innerHTML = carrito.map(item => `
            <div class="resumen-linea">
                <span>${item.nombre} x${item.cantidad}</span>
                <span>Bs. ${(item.precio * item.cantidad).toFixed(2)}</span>
            </div>
        `).join('');
    }

    if (totalEl) totalEl.textContent = `Bs. ${total.toFixed(2)}`;
}

function cambiarCantidad(id, delta) {
    const item = carrito.find(i => i.id === id);
    if (!item) return;
    item.cantidad += delta;
    if (item.cantidad <= 0) {
        carrito = carrito.filter(i => i.id !== id);
    }
    localStorage.setItem('carrito', JSON.stringify(carrito));
    actualizarContador();
    renderCarrito();
}

function eliminarItem(id) {
    carrito = carrito.filter(i => i.id !== id);
    localStorage.setItem('carrito', JSON.stringify(carrito));
    actualizarContador();
    renderCarrito();
}

function limpiarCarrito() {
    carrito = [];
    localStorage.removeItem('carrito');
    actualizarContador();
}

async function confirmarPedido() {
    const btn = document.querySelector('.btn-confirmar');
    if (btn.disabled) return;
    btn.disabled = true;
    btn.innerHTML = '<i class="ti ti-loader"></i> Procesando...';

    const nombre    = document.getElementById('nombre').value.trim();
    const telefono  = document.getElementById('telefono').value.trim();
    const direccion = document.getElementById('direccion').value.trim();

    if (!nombre || !direccion) {
        alert('Por favor completa tu nombre y dirección');
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-check"></i> Confirmar pedido';
        return;
    }
    if (carrito.length === 0) {
        alert('Tu carrito está vacío');
        btn.disabled = false;
        btn.innerHTML = '<i class="ti ti-check"></i> Confirmar pedido';
        return;
    }

    const total = carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);

    const response = await fetch('/pedido', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            nombre:   nombre,
            telefono: telefono,
            direccion: direccion,
            total:    total.toFixed(2),
            items:    carrito
        })
    });

    const data = await response.json();

    if (data.success) {
        document.getElementById('modal-pedido-id').textContent = `Número de pedido: #${data.pedido_id}`;
        document.getElementById('modal-exito').style.display = 'flex';
        localStorage.setItem('ultimo_pedido', data.pedido_id);
        limpiarCarrito();
        renderCarrito();
    } else {
        alert('Error al procesar el pedido. Intenta de nuevo.');
    }
}

function filtrarPedidos(estado, btn) {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.pedido-card').forEach(card => {
        if (estado === 'todos' || card.dataset.estado === estado) {
            card.parentElement.style.display = 'block';
        } else {
            card.parentElement.style.display = 'none';
        }
    });
}

// Enlace de seguimiento en modal
const btnSeguimiento = document.getElementById('btn-seguimiento');
if (btnSeguimiento) {
    const ultimoPedido = localStorage.getItem('ultimo_pedido');
    if (ultimoPedido) {
        btnSeguimiento.href = `/seguimiento?pedido_id=${ultimoPedido}`;
    }
}

actualizarContador();
renderCarrito();