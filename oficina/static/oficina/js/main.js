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

function closeMenuGroup(menuRoot, selector) {
    menuRoot.querySelectorAll(selector).forEach((item) => {
        item.classList.remove('is-open');
        const button = item.querySelector('.nav-submenu-toggle');
        if (button) button.setAttribute('aria-expanded', 'false');
    });
}

function setupTopNav() {
    const nav = document.querySelector('[data-topnav]');
    const toggle = nav ? nav.querySelector('.nav-toggle') : null;
    const panel = nav ? nav.querySelector('[data-topnav-panel]') : null;
    if (!nav || !toggle || !panel) return;

    const closePanel = () => {
        panel.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
    };

    const closeSubmenus = () => {
        closeMenuGroup(nav, '.topnav-item--submenu');
    };

    toggle.addEventListener('click', (event) => {
        event.stopPropagation();
        const isOpen = panel.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', String(isOpen));
        if (!isOpen) closeSubmenus();
    });

    nav.querySelectorAll('.nav-submenu-toggle').forEach((button) => {
        button.addEventListener('click', (event) => {
            event.stopPropagation();
            const item = button.closest('.topnav-item--submenu');
            if (!item) return;

            const shouldOpen = !item.classList.contains('is-open');
            closeSubmenus();
            if (shouldOpen) {
                item.classList.add('is-open');
                button.setAttribute('aria-expanded', 'true');
            }
        });
    });

    document.addEventListener('click', (event) => {
        if (!nav.contains(event.target)) {
            closePanel();
            closeSubmenus();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closePanel();
            closeSubmenus();
        }
    });
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
    setupTopNav();
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
