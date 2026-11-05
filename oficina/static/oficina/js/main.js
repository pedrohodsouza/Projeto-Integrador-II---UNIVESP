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

function setupAccessibilityToggle() {
    const buttons = document.querySelectorAll('[data-accessibility-toggle]');
    if (!buttons.length) return;

    const storageKey = 'oficina-acessibilidade';
    const root = document.documentElement;
    const updateButtons = (enabled) => {
        root.classList.toggle('accessibility-mode', enabled);
        buttons.forEach((button) => {
            button.setAttribute('aria-pressed', String(enabled));
            button.setAttribute('aria-label', enabled ? 'Desativar alto contraste e texto ampliado' : 'Ativar alto contraste e texto ampliado');
            button.querySelector('[data-accessibility-label]').textContent = enabled
                ? 'Desativar alto contraste'
                : 'Ativar alto contraste';
        });
    };

    updateButtons(root.classList.contains('accessibility-mode'));

    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            const enabled = !root.classList.contains('accessibility-mode');
            updateButtons(enabled);
            localStorage.setItem(storageKey, String(enabled));
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    setupUserMenu();
    setupAccessibilityToggle();
});
