// Painel de atendimentos com Vue.js 3: quadro por etapa (kanban) ou lista,
// com indicadores, busca e filtros reativos. Os dados vêm do Django via json_script.
(function () {
    const el = document.getElementById('atendimentos-app');
    if (!el || !window.Vue) return;

    const lerJson = (id) => JSON.parse(document.getElementById(id).textContent);

    const normalizar = (valor) =>
        String(valor ?? '')
            .normalize('NFD')
            .replace(/[̀-ͯ]/g, '')
            .toLowerCase();

    const PREFERENCIA_VISAO = 'oficina.atendimentos.visao';

    const lerPreferencia = () => {
        try {
            return localStorage.getItem(PREFERENCIA_VISAO) || 'quadro';
        } catch (e) {
            return 'quadro';
        }
    };

    Vue.createApp({
        // Evita conflito com a sintaxe {{ }} dos templates Django
        delimiters: ['[[', ']]'],
        data() {
            return {
                itens: lerJson('atendimentos-dados'),
                etapas: lerJson('etapas-dados'),
                busca: '',
                filtroEtapa: '',
                filtroPrioridade: '',
                filtroResponsavel: '',
                somenteAtrasados: false,
                mostrarFinalizados: false,
                visao: lerPreferencia(),
            };
        },
        computed: {
            responsaveis() {
                return [...new Set(this.itens.map((i) => i.responsavel).filter(Boolean))].sort();
            },
            abertos() {
                return this.itens.filter((i) => i.em_aberto);
            },
            indicadores() {
                return {
                    abertos: this.abertos.length,
                    emExecucao: this.abertos.filter((i) => i.status === 'em_execucao').length,
                    prontos: this.abertos.filter((i) => i.status === 'pronto').length,
                    atrasados: this.abertos.filter((i) => i.atrasado).length,
                };
            },
            filtrados() {
                const termo = normalizar(this.busca.trim());
                return this.itens.filter((i) => {
                    if (!this.mostrarFinalizados && !i.em_aberto && this.filtroEtapa !== i.status) return false;
                    if (this.filtroEtapa && i.status !== this.filtroEtapa) return false;
                    if (this.filtroPrioridade && i.prioridade !== this.filtroPrioridade) return false;
                    if (this.filtroResponsavel === '-' && i.responsavel) return false;
                    if (this.filtroResponsavel && this.filtroResponsavel !== '-' && i.responsavel !== this.filtroResponsavel) return false;
                    if (this.somenteAtrasados && !i.atrasado) return false;
                    if (!termo) return true;
                    return [i.numero, i.placa, i.veiculo, i.cliente, i.responsavel, i.queixa]
                        .some((campo) => normalizar(campo).includes(termo));
                });
            },
            colunas() {
                return this.etapas
                    .filter((e) => this.mostrarFinalizados || !['entregue', 'cancelado'].includes(e.valor) || this.filtroEtapa === e.valor)
                    .filter((e) => !this.filtroEtapa || e.valor === this.filtroEtapa)
                    .map((e) => ({ ...e, itens: this.filtrados.filter((i) => i.status === e.valor) }));
            },
            temFiltro() {
                return Boolean(
                    this.busca || this.filtroEtapa || this.filtroPrioridade
                    || this.filtroResponsavel || this.somenteAtrasados
                );
            },
        },
        watch: {
            visao(valor) {
                try {
                    localStorage.setItem(PREFERENCIA_VISAO, valor);
                } catch (e) { /* sem armazenamento local: ignora */ }
            },
        },
        methods: {
            data(iso) {
                if (!iso) return '-';
                const d = iso.length === 10 ? new Date(iso + 'T00:00:00') : new Date(iso);
                return d.toLocaleDateString('pt-BR');
            },
            dataHora(iso) {
                return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
            },
            diasNaOficina(iso) {
                const dias = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
                return dias <= 0 ? 'hoje' : `há ${dias} dia${dias > 1 ? 's' : ''}`;
            },
            filtrarIndicador(tipo) {
                this.limpar();
                if (tipo === 'execucao') this.filtroEtapa = 'em_execucao';
                if (tipo === 'prontos') this.filtroEtapa = 'pronto';
                if (tipo === 'atrasados') this.somenteAtrasados = true;
            },
            limpar() {
                this.busca = '';
                this.filtroEtapa = '';
                this.filtroPrioridade = '';
                this.filtroResponsavel = '';
                this.somenteAtrasados = false;
            },
            abrir(item) {
                window.location.href = `${el.dataset.baseUrl}${item.id}/`;
            },
        },
    }).mount(el);
})();
