// Painel de estoque com Vue.js 3: indicadores, busca, filtros e ordenação
// das peças enviadas pelo Django via json_script.
(function () {
    const el = document.getElementById('estoque-app');
    const dadosEl = document.getElementById('pecas-dados');
    if (!el || !dadosEl || !window.Vue) return;

    const normalizar = (valor) =>
        String(valor ?? '')
            .normalize('NFD')
            .replace(/[̀-ͯ]/g, '')
            .toLowerCase();

    const moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
    const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });

    Vue.createApp({
        // Evita conflito com a sintaxe {{ }} dos templates Django
        delimiters: ['[[', ']]'],
        data() {
            return {
                pecas: JSON.parse(dadosEl.textContent),
                busca: '',
                filtroCategoria: '',
                filtroSituacao: '',
                mostrarInativas: false,
                ordem: 'nome',
            };
        },
        computed: {
            ativas() {
                return this.pecas.filter((p) => p.ativo);
            },
            categorias() {
                return [...new Set(this.pecas.map((p) => p.categoria).filter(Boolean))].sort();
            },
            indicadores() {
                return {
                    itens: this.ativas.length,
                    valor: this.ativas.reduce((total, p) => total + p.estoque * p.custo, 0),
                    baixo: this.ativas.filter((p) => this.situacao(p) === 'baixo').length,
                    zerado: this.ativas.filter((p) => this.situacao(p) === 'zerado').length,
                };
            },
            filtradas() {
                const termo = normalizar(this.busca.trim());
                const lista = this.pecas.filter((p) => {
                    if (!this.mostrarInativas && !p.ativo) return false;
                    if (this.filtroCategoria && p.categoria !== this.filtroCategoria) return false;
                    if (this.filtroSituacao === 'repor' && this.situacao(p) === 'ok') return false;
                    if (this.filtroSituacao && this.filtroSituacao !== 'repor' && this.situacao(p) !== this.filtroSituacao) return false;
                    if (!termo) return true;
                    return [p.codigo, p.nome, p.categoria, p.fabricante, p.fornecedor, p.localizacao]
                        .some((campo) => normalizar(campo).includes(termo));
                });
                const criterios = {
                    nome: (a, b) => a.nome.localeCompare(b.nome, 'pt-BR'),
                    codigo: (a, b) => a.codigo.localeCompare(b.codigo, 'pt-BR'),
                    estoque: (a, b) => a.estoque - b.estoque,
                    valor: (a, b) => b.estoque * b.custo - a.estoque * a.custo,
                };
                return lista.sort(criterios[this.ordem]);
            },
            temFiltro() {
                return Boolean(this.busca || this.filtroCategoria || this.filtroSituacao);
            },
        },
        methods: {
            situacao(p) {
                if (p.estoque <= 0) return 'zerado';
                if (p.estoque <= p.minimo) return 'baixo';
                return 'ok';
            },
            rotuloSituacao(p) {
                return { zerado: 'Sem estoque', baixo: 'Repor', ok: 'OK' }[this.situacao(p)];
            },
            moeda(valor) {
                return moeda.format(valor);
            },
            numero(valor) {
                return numero.format(valor);
            },
            filtrarSituacao(valor) {
                this.limpar();
                this.filtroSituacao = valor;
            },
            limpar() {
                this.busca = '';
                this.filtroCategoria = '';
                this.filtroSituacao = '';
            },
            abrir(p) {
                window.location.href = `${el.dataset.baseUrl}${p.id}/`;
            },
        },
    }).mount(el);
})();
