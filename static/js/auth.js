document.addEventListener('DOMContentLoaded', function () {

    // 1) Ojito para ver la contraseña
    document.querySelectorAll('input[type="password"]').forEach(function (input) {
        var wrap = document.createElement('div');
        wrap.className = 'pass-wrap';
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'pass-toggle';
        btn.setAttribute('aria-label', 'Mostrar u ocultar contraseña');
        btn.innerHTML = '<i class="ti ti-eye"></i>';
        wrap.appendChild(btn);

        btn.addEventListener('click', function () {
            var visible = input.type === 'text';
            input.type = visible ? 'password' : 'text';
            btn.innerHTML = visible
                ? '<i class="ti ti-eye"></i>'
                : '<i class="ti ti-eye-off"></i>';
        });
    });

    // 2) Evitar autocompletado de correo y contraseña
    document.querySelectorAll('form').forEach(function (f) {
        f.setAttribute('autocomplete', 'off');
    });

    document.querySelectorAll('input[type="email"], input[type="password"]').forEach(function (input) {
        input.setAttribute('autocomplete', input.type === 'password' ? 'new-password' : 'off');
        // Truco: Chrome/Firefox ignoran "off" en correos, así que se bloquea hasta hacer clic
        input.setAttribute('readonly', 'readonly');
        input.addEventListener('focus', function () {
            input.removeAttribute('readonly');
        });
    });
});