// Listagens reativas com Vue.js 3: busca em tempo real sobre os dados
// enviados pelo Django via {{ dados|json_script:"lista-dados" }}.
(function () {
    const el = document.getElementById('lista-app');
    const dadosEl = document.getElementById('lista-dados');
    if (!el || !dadosEl || !window.Vue) return;

    const normalizar = (valor) =>
        String(valor ?? '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase();

    const campos = (el.dataset.campos || '').split(',').filter(Boolean);

    Vue.createApp({
        // Evita conflito com a sintaxe {{ }} dos templates Django
        delimiters: ['[[', ']]'],
        data() {
            return {
                itens: JSON.parse(dadosEl.textContent),
                busca: '',
            };
        },
        computed: {
            filtrados() {
                const termo = normalizar(this.busca.trim());
                if (!termo) return this.itens;
                return this.itens.filter((item) =>
                    campos.some((campo) => normalizar(item[campo]).includes(termo))
                );
            },
        },
    }).mount(el);
})();
