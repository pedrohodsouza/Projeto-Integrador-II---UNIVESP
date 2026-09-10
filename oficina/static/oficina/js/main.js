function updateClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    clockEl.textContent = new Date().toLocaleString('pt-BR');
}

document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
});
