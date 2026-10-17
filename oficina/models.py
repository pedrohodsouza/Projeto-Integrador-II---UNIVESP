from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone


class EstoqueInsuficiente(Exception):
    pass


class CodigoAutomaticoMixin:
    """Código de exibição gerado a partir da chave primária (ex.: CLI-00001)."""

    PREFIXO_CODIGO = ''

    @property
    def codigo(self):
        return f'{self.PREFIXO_CODIGO}-{self.pk:05d}' if self.pk else f'{self.PREFIXO_CODIGO}-novo'


class Cliente(CodigoAutomaticoMixin, models.Model):
    PREFIXO_CODIGO = 'CLI'

    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.codigo})'


class Veiculo(CodigoAutomaticoMixin, models.Model):
    PREFIXO_CODIGO = 'VEI'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='veiculos')
    placa = models.CharField(max_length=10)
    marca = models.CharField(max_length=60)
    modelo = models.CharField(max_length=60)
    ano = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['placa']

    def __str__(self):
        return f'{self.placa} - {self.marca} {self.modelo}'


class Fornecedor(CodigoAutomaticoMixin, models.Model):
    PREFIXO_CODIGO = 'FOR'

    nome = models.CharField(max_length=120)
    cnpj = models.CharField('CNPJ', max_length=18, blank=True)
    contato = models.CharField('pessoa de contato', max_length=120, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    observacoes = models.TextField('observações', blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'fornecedores'

    def __str__(self):
        return self.nome


class Peca(CodigoAutomaticoMixin, models.Model):
    PREFIXO_CODIGO = 'PEC'

    class Unidade(models.TextChoices):
        UNIDADE = 'UN', 'Unidade'
        PECA = 'PC', 'Peça'
        JOGO = 'JG', 'Jogo'
        LITRO = 'L', 'Litro'
        QUILO = 'KG', 'Quilo'
        METRO = 'M', 'Metro'
        CAIXA = 'CX', 'Caixa'

    referencia = models.CharField(
        'código do fabricante', max_length=40, blank=True,
        help_text='Opcional. Código/part number da peça no catálogo do fabricante.',
    )
    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=60, blank=True, help_text='Ex.: Freios, Motor, Suspensão, Óleos e fluidos')
    fabricante = models.CharField(max_length=60, blank=True)
    unidade = models.CharField(max_length=2, choices=Unidade.choices, default=Unidade.UNIDADE)
    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pecas', verbose_name='fornecedor principal',
    )
    preco_custo = models.DecimalField('preço de custo (R$)', max_digits=10, decimal_places=2, default=0)
    preco_venda = models.DecimalField('preço de venda (R$)', max_digits=10, decimal_places=2, default=0)
    estoque_atual = models.DecimalField('estoque atual', max_digits=10, decimal_places=2, default=0, editable=False)
    estoque_minimo = models.DecimalField('estoque mínimo', max_digits=10, decimal_places=2, default=0)
    localizacao = models.CharField('localização', max_length=60, blank=True, help_text='Ex.: Prateleira A3')
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'peça'

    def __str__(self):
        return f'{self.codigo} - {self.nome}'

    @property
    def abaixo_minimo(self):
        return self.estoque_atual <= self.estoque_minimo

    @property
    def valor_em_estoque(self):
        return self.estoque_atual * self.preco_custo

    @transaction.atomic
    def movimentar(self, tipo, quantidade, usuario=None, motivo='', atendimento=None,
                   custo_unitario=None, documento=''):
        """Registra uma movimentação e atualiza o saldo. No ajuste, `quantidade` é o saldo contado."""
        peca = Peca.objects.select_for_update().get(pk=self.pk)
        quantidade = Decimal(quantidade)
        Tipo = MovimentacaoEstoque.Tipo
        if tipo == Tipo.ENTRADA:
            novo_saldo = peca.estoque_atual + quantidade
        elif tipo == Tipo.SAIDA:
            if quantidade > peca.estoque_atual:
                raise EstoqueInsuficiente(
                    f'Estoque insuficiente de "{peca.nome}": disponível {peca.estoque_atual:g} {peca.unidade}.'
                )
            novo_saldo = peca.estoque_atual - quantidade
        else:
            novo_saldo = quantidade
            quantidade = novo_saldo - peca.estoque_atual

        peca.estoque_atual = novo_saldo
        campos = ['estoque_atual']
        if tipo == Tipo.ENTRADA and custo_unitario:
            peca.preco_custo = custo_unitario
            campos.append('preco_custo')
        peca.save(update_fields=campos)
        self.estoque_atual = peca.estoque_atual
        self.preco_custo = peca.preco_custo

        return peca.movimentacoes.create(
            tipo=tipo, quantidade=quantidade, saldo_apos=novo_saldo,
            custo_unitario=custo_unitario if custo_unitario is not None else peca.preco_custo,
            motivo=motivo, documento=documento, atendimento=atendimento, usuario=usuario,
        )


class Atendimento(CodigoAutomaticoMixin, models.Model):
    PREFIXO_CODIGO = 'OS'

    class Status(models.TextChoices):
        AGUARDANDO = 'aguardando', 'Aguardando atendimento'
        DIAGNOSTICO = 'diagnostico', 'Em diagnóstico'
        AGUARDANDO_APROVACAO = 'aguardando_aprovacao', 'Aguardando aprovação'
        AGUARDANDO_PECAS = 'aguardando_pecas', 'Aguardando peças'
        EM_EXECUCAO = 'em_execucao', 'Em execução'
        CONTROLE_QUALIDADE = 'controle_qualidade', 'Controle de qualidade'
        PRONTO = 'pronto', 'Pronto para retirada'
        ENTREGUE = 'entregue', 'Entregue'
        CANCELADO = 'cancelado', 'Cancelado'

    class Prioridade(models.TextChoices):
        BAIXA = 'baixa', 'Baixa'
        NORMAL = 'normal', 'Normal'
        ALTA = 'alta', 'Alta'
        URGENTE = 'urgente', 'Urgente'

    STATUS_FINAIS = (Status.ENTREGUE, Status.CANCELADO)

    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name='atendimentos')
    status = models.CharField('etapa', max_length=30, choices=Status.choices, default=Status.AGUARDANDO)
    prioridade = models.CharField(max_length=10, choices=Prioridade.choices, default=Prioridade.NORMAL)
    responsavel = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='atendimentos', verbose_name='mecânico responsável',
    )
    queixa = models.TextField('relato do cliente')
    diagnostico = models.TextField('diagnóstico', blank=True)
    observacoes = models.TextField('observações', blank=True)
    km_entrada = models.PositiveIntegerField('km na entrada', null=True, blank=True)
    data_entrada = models.DateTimeField('entrada', default=timezone.now)
    previsao_entrega = models.DateField('previsão de entrega', null=True, blank=True)
    data_conclusao = models.DateTimeField('concluído em', null=True, blank=True)
    data_entrega = models.DateTimeField('entregue em', null=True, blank=True)
    criado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )

    class Meta:
        ordering = ['-data_entrada']

    def __str__(self):
        return f'{self.numero} - {self.veiculo.placa}'

    @property
    def numero(self):
        return self.codigo

    @property
    def em_aberto(self):
        return self.status not in self.STATUS_FINAIS

    @property
    def atrasado(self):
        return bool(
            self.em_aberto and self.status != self.Status.PRONTO
            and self.previsao_entrega and self.previsao_entrega < timezone.localdate()
        )

    def _total_por_tipo(self, tipo):
        return sum((i.total for i in self.itens.all() if i.tipo == tipo), Decimal('0'))

    @property
    def total_servicos(self):
        return self._total_por_tipo(ItemAtendimento.Tipo.SERVICO)

    @property
    def total_pecas(self):
        return self._total_por_tipo(ItemAtendimento.Tipo.PECA)

    @property
    def total(self):
        return self.total_servicos + self.total_pecas

    def alterar_status(self, novo_status, usuario=None, comentario=''):
        anterior = self.status
        if novo_status == anterior and not comentario:
            return
        with transaction.atomic():
            self._ajustar_estoque_por_status(anterior, novo_status, usuario)
            self._aplicar_status(anterior, novo_status, usuario, comentario)

    def _ajustar_estoque_por_status(self, anterior, novo_status, usuario):
        """Cancelar devolve as peças ao estoque; reabrir uma OS cancelada baixa de novo."""
        cancelado = self.Status.CANCELADO
        if (anterior == cancelado) == (novo_status == cancelado):
            return
        Tipo = MovimentacaoEstoque.Tipo
        for item in self.itens.filter(peca__isnull=False).select_related('peca'):
            if novo_status == cancelado:
                item.peca.movimentar(Tipo.ENTRADA, item.quantidade, usuario,
                                     f'Estorno: {self.numero} cancelado', atendimento=self)
            else:
                item.peca.movimentar(Tipo.SAIDA, item.quantidade, usuario,
                                     f'Reabertura de {self.numero}', atendimento=self)

    def _aplicar_status(self, anterior, novo_status, usuario, comentario):
        self.status = novo_status
        agora = timezone.now()
        if novo_status == self.Status.PRONTO and not self.data_conclusao:
            self.data_conclusao = agora
        if novo_status == self.Status.ENTREGUE:
            self.data_conclusao = self.data_conclusao or agora
            self.data_entrega = agora
        self.save()
        self.historico.create(
            status_anterior=anterior, status_novo=novo_status,
            usuario=usuario, comentario=comentario,
        )


class ItemAtendimento(models.Model):
    class Tipo(models.TextChoices):
        SERVICO = 'servico', 'Serviço'
        PECA = 'peca', 'Peça'

    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='itens')
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.SERVICO)
    peca = models.ForeignKey(
        Peca, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_atendimento',
        verbose_name='peça do estoque',
    )
    descricao = models.CharField('descrição', max_length=200)
    quantidade = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    valor_unitario = models.DecimalField('valor unitário (R$)', max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-tipo', 'id']

    def __str__(self):
        return self.descricao

    @property
    def total(self):
        return self.quantidade * self.valor_unitario


class HistoricoAtendimento(models.Model):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name='historico')
    status_anterior = models.CharField(max_length=30, choices=Atendimento.Status.choices, blank=True)
    status_novo = models.CharField(max_length=30, choices=Atendimento.Status.choices)
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    comentario = models.TextField(blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-id']


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = 'entrada', 'Entrada'
        SAIDA = 'saida', 'Saída'
        AJUSTE = 'ajuste', 'Ajuste de inventário'

    peca = models.ForeignKey(Peca, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_apos = models.DecimalField('saldo após', max_digits=10, decimal_places=2)
    custo_unitario = models.DecimalField('custo unitário (R$)', max_digits=10, decimal_places=2, default=0)
    documento = models.CharField('documento / NF', max_length=60, blank=True)
    motivo = models.CharField(max_length=200, blank=True)
    atendimento = models.ForeignKey(
        Atendimento, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentacoes',
    )
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-id']
        verbose_name = 'movimentação de estoque'
        verbose_name_plural = 'movimentações de estoque'

    def __str__(self):
        return f'{self.get_tipo_display()} de {self.quantidade:g} - {self.peca.nome}'
