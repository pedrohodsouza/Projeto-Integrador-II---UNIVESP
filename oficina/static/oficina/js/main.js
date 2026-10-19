function updateGreeting() {
    const greetingEl = document.getElementById('greeting');
    if (!greetingEl) return;
    const hour = new Date().getHours();
    let greeting = 'Olá';
    if (hour >= 5 && hour < 12) {
        greeting = 'Bom dia';
    } else if (hour >= 12 && hour < 18) {
        greeting = 'Boa tarde';
    } else {
        greeting = 'Boa noite';
    }
    greetingEl.textContent = greeting;
}

function updateClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    clockEl.textContent = new Date().toLocaleString('pt-BR');
}

function setupUserMenu() {
    const toggle = document.getElementById('user-menu-toggle');
    const menu = toggle ? toggle.closest('.user-menu') : null;
    if (!toggle || !menu) return;

    const close = () => {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
    };

    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        const isOpen = menu.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('click', (event) => {
        if (!menu.contains(event.target)) close();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') close();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    updateGreeting();
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(updateGreeting, 60000);
    setupUserMenu();
});

// Parallax: as camadas do painel esquerdo acompanham o mouse
(function () {
    const panel = document.querySelector('.login-panel-left');
    if (!panel || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    let frame = null;

    function setPos(x, y) {
        if (frame) cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
            panel.style.setProperty('--mx', x.toFixed(3));
            panel.style.setProperty('--my', y.toFixed(3));
        });
    }

    panel.addEventListener('mousemove', (e) => {
        const r = panel.getBoundingClientRect();
        const x = ((e.clientX - r.left) / r.width - 0.5) * 2;   // vai de -1 a 1
        const y = ((e.clientY - r.top) / r.height - 0.5) * 2;
        setPos(x, y);
    });

    panel.addEventListener('mouseleave', () => setPos(0, 0));
})();
