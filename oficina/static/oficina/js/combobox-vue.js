// Combobox pesquisável com Vue.js 3.
// Transforma todo <select data-combobox> em um campo onde é possível digitar
// para filtrar os itens já cadastrados. O <select> original continua no
// formulário (oculto) e é ele que envia o valor, então o Django não muda nada.
(function () {
    if (!window.Vue) return;

    const normalizar = (valor) =>
        String(valor ?? '')
            .normalize('NFD')
            .replace(/[̀-ͯ]/g, '')
            .toLowerCase();

    const LIMITE = 100;
    let sequencia = 0;

    const Combobox = {
        delimiters: ['[[', ']]'],
        props: ['select'],
        data() {
            const opcoes = [...this.select.options].map((o) => ({ valor: o.value, rotulo: o.text.trim() }));
            const vazia = opcoes.find((o) => o.valor === '');
            return {
                id: `combobox-${++sequencia}`,
                opcoes: opcoes.filter((o) => o.valor !== ''),
                placeholder: vazia ? vazia.rotulo : 'Selecione...',
                permiteVazio: Boolean(vazia),
                valor: this.select.value,
                texto: '',
                aberto: false,
                ativo: 0,
            };
        },
        computed: {
            selecionada() {
                return this.opcoes.find((o) => o.valor === this.valor) || null;
            },
            filtradas() {
                const termos = normalizar(this.texto).split(/\s+/).filter(Boolean);
                const lista = termos.length
                    ? this.opcoes.filter((o) => termos.every((t) => normalizar(o.rotulo).includes(t)))
                    : this.opcoes;
                return lista.slice(0, LIMITE);
            },
            total() {
                const termos = normalizar(this.texto).split(/\s+/).filter(Boolean);
                return termos.length
                    ? this.opcoes.filter((o) => termos.every((t) => normalizar(o.rotulo).includes(t))).length
                    : this.opcoes.length;
            },
        },
        created() {
            this.texto = this.selecionada ? this.selecionada.rotulo : '';
        },
        mounted() {
            this.aoClicarFora = (evento) => {
                if (!this.$el.contains(evento.target)) this.fechar();
            };
            document.addEventListener('mousedown', this.aoClicarFora);
        },
        unmounted() {
            document.removeEventListener('mousedown', this.aoClicarFora);
        },
        methods: {
            abrir() {
                if (this.aberto) return;
                this.aberto = true;
                // Ao abrir, mostra a lista completa e seleciona o texto para facilitar a nova busca
                if (this.selecionada && this.texto === this.selecionada.rotulo) {
                    this.$nextTick(() => this.$refs.entrada.select());
                }
                this.ativo = Math.max(0, this.filtradas.findIndex((o) => o.valor === this.valor));
            },
            fechar() {
                if (!this.aberto) return;
                this.aberto = false;
                // Texto que não corresponde a um item cadastrado volta para a seleção atual
                this.texto = this.selecionada ? this.selecionada.rotulo : '';
            },
            digitar() {
                this.aberto = true;
                this.ativo = 0;
                if (this.texto === '' && this.permiteVazio) this.escolher(null, false);
            },
            escolher(opcao, fecharDepois = true) {
                this.valor = opcao ? opcao.valor : '';
                this.select.value = this.valor;
                this.select.dispatchEvent(new Event('change', { bubbles: true }));
                this.texto = opcao ? opcao.rotulo : '';
                if (fecharDepois) {
                    this.aberto = false;
                }
            },
            limpar() {
                this.escolher(null);
                this.$refs.entrada.focus();
            },
            mover(passo) {
                if (!this.aberto) {
                    this.abrir();
                    return;
                }
                const total = this.filtradas.length;
                if (!total) return;
                this.ativo = (this.ativo + passo + total) % total;
                this.$nextTick(() => {
                    const item = this.$el.querySelector('.combobox-opcao.is-ativa');
                    if (item) item.scrollIntoView({ block: 'nearest' });
                });
            },
            confirmar(evento) {
                if (!this.aberto) return;
                evento.preventDefault();
                const opcao = this.filtradas[this.ativo];
                if (opcao) this.escolher(opcao);
            },
            destacar(rotulo) {
                const termos = normalizar(this.texto).split(/\s+/).filter(Boolean);
                if (!termos.length) return [{ texto: rotulo, marcado: false }];
                // Marca os trechos que batem com a busca (comparando sem acentos)
                const base = normalizar(rotulo);
                const marcado = new Array(rotulo.length).fill(false);
                termos.forEach((t) => {
                    let i = base.indexOf(t);
                    while (i !== -1) {
                        for (let j = i; j < i + t.length; j++) marcado[j] = true;
                        i = base.indexOf(t, i + t.length);
                    }
                });
                const partes = [];
                for (let i = 0; i < rotulo.length; i++) {
                    const ultima = partes[partes.length - 1];
                    if (ultima && ultima.marcado === marcado[i]) ultima.texto += rotulo[i];
                    else partes.push({ texto: rotulo[i], marcado: marcado[i] });
                }
                return partes;
            },
        },
        template: `
            <div class="combobox" :class="{ 'is-aberto': aberto }">
                <div class="combobox-campo">
                    <input ref="entrada" type="text" class="combobox-entrada" v-model="texto"
                           :placeholder="placeholder" autocomplete="off" role="combobox"
                           :aria-expanded="aberto" :aria-controls="id + '-lista'"
                           :aria-activedescendant="aberto && filtradas[ativo] ? id + '-' + ativo : null"
                           @focus="abrir" @click="abrir" @input="digitar"
                           @keydown.down.prevent="mover(1)" @keydown.up.prevent="mover(-1)"
                           @keydown.enter="confirmar" @keydown.esc="fechar" @keydown.tab="fechar">
                    <button v-if="permiteVazio && valor" type="button" class="combobox-limpar"
                            title="Limpar seleção" aria-label="Limpar seleção" @click="limpar">×</button>
                    <span class="combobox-seta" aria-hidden="true" @mousedown.prevent="aberto ? fechar() : ($refs.entrada.focus(), abrir())">▾</span>
                </div>
                <ul v-if="aberto" class="combobox-lista" :id="id + '-lista'" role="listbox">
                    <li v-for="(opcao, i) in filtradas" :key="opcao.valor" :id="id + '-' + i"
                        class="combobox-opcao" role="option"
                        :class="{ 'is-ativa': i === ativo, 'is-selecionada': opcao.valor === valor }"
                        :aria-selected="opcao.valor === valor"
                        @mousedown.prevent="escolher(opcao)" @mousemove="ativo = i">
                        <template v-for="(parte, k) in destacar(opcao.rotulo)" :key="k"><mark v-if="parte.marcado">[[ parte.texto ]]</mark><template v-else>[[ parte.texto ]]</template></template>
                    </li>
                    <li v-if="filtradas.length === 0" class="combobox-vazio">Nenhum item encontrado para "[[ texto ]]".</li>
                    <li v-else-if="total > filtradas.length" class="combobox-vazio">
                        Mostrando [[ filtradas.length ]] de [[ total ]]. Digite mais para refinar.
                    </li>
                </ul>
            </div>
        `,
    };

    function montar(select) {
        if (select.dataset.comboboxPronto) return;
        select.dataset.comboboxPronto = '1';
        const alvo = document.createElement('div');
        select.after(alvo);
        select.classList.add('combobox-original');
        select.tabIndex = -1;
        select.setAttribute('aria-hidden', 'true');

        // O <label for="..."> passa a focar o campo de busca
        const label = select.id ? document.querySelector(`label[for="${select.id}"]`) : null;
        const app = Vue.createApp(Combobox, { select });
        const instancia = app.mount(alvo);
        if (label) {
            label.addEventListener('click', (evento) => {
                evento.preventDefault();
                instancia.$refs.entrada.focus();
            });
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('select[data-combobox]').forEach(montar);
    });
})();
