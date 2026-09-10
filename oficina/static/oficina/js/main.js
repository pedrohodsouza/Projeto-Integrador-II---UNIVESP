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
    updateClock();
    setInterval(updateClock, 1000);
    setupUserMenu();
});
