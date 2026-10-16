from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import Atendimento, Cliente, Fornecedor, ItemAtendimento, MovimentacaoEstoque, Peca, Veiculo


class UsuarioForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'email']


class VeiculoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), empty_label='Selecione um cliente')

    class Meta:
        model = Veiculo
        fields = ['cliente', 'placa', 'marca', 'modelo', 'ano']


class VeiculoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.placa} - {obj.marca} {obj.modelo} ({obj.cliente.nome})'


class ResponsavelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class AtendimentoForm(forms.ModelForm):
    veiculo = VeiculoChoiceField(
        queryset=Veiculo.objects.select_related('cliente'),
        empty_label='Selecione um veículo', label='Veículo',
    )
    responsavel = ResponsavelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'username'),
        required=False, empty_label='Sem responsável', label='Mecânico responsável',
    )

    class Meta:
        model = Atendimento
        fields = [
            'veiculo', 'km_entrada', 'prioridade', 'responsavel', 'data_entrada',
            'previsao_entrega', 'queixa', 'diagnostico', 'observacoes',
        ]
        widgets = {
            'data_entrada': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'previsao_entrega': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'queixa': forms.Textarea(attrs={'rows': 3, 'placeholder': 'O que o cliente relatou?'}),
            'diagnostico': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }


class StatusAtendimentoForm(forms.Form):
    status = forms.ChoiceField(choices=Atendimento.Status.choices, label='Etapa')
    comentario = forms.CharField(
        required=False, label='Comentário',
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Opcional: o que foi feito, motivo, etc.'}),
    )


class PecaChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.codigo} - {obj.nome} (estoque: {obj.estoque_atual:g} {obj.unidade} · R$ {obj.preco_venda})'


class ItemAtendimentoForm(forms.ModelForm):
    peca = PecaChoiceField(
        queryset=Peca.objects.filter(ativo=True), required=False,
        empty_label='Avulsa (fora do estoque)', label='Peça do estoque',
    )

    class Meta:
        model = ItemAtendimento
        fields = ['tipo', 'peca', 'descricao', 'quantidade', 'valor_unitario']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.fields['valor_unitario'].required = False

    def clean(self):
        dados = super().clean()
        peca = dados.get('peca')
        if peca:
            dados['tipo'] = ItemAtendimento.Tipo.PECA
            dados['descricao'] = dados.get('descricao') or peca.nome
            if not dados.get('valor_unitario'):
                dados['valor_unitario'] = peca.preco_venda
        if not dados.get('descricao'):
            self.add_error('descricao', 'Informe a descrição ou escolha uma peça do estoque.')
        if dados.get('valor_unitario') is None:
            dados['valor_unitario'] = 0
        quantidade = dados.get('quantidade')
        if quantidade is not None and quantidade <= 0:
            self.add_error('quantidade', 'A quantidade deve ser maior que zero.')
        return dados


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'cnpj', 'contato', 'telefone', 'email', 'observacoes']
        widgets = {'observacoes': forms.Textarea(attrs={'rows': 3})}


class PecaForm(forms.ModelForm):
    fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.all(), required=False, empty_label='Nenhum', label='Fornecedor principal',
    )
    estoque_inicial = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, label='Estoque inicial',
        help_text='Quantidade já disponível na oficina. Registrada como uma entrada.',
    )

    class Meta:
        model = Peca
        fields = [
            'codigo', 'nome', 'categoria', 'fabricante', 'unidade', 'fornecedor',
            'preco_custo', 'preco_venda', 'estoque_minimo', 'localizacao', 'ativo',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields['estoque_inicial']
        categorias = Peca.objects.exclude(categoria='').values_list('categoria', flat=True).distinct()
        self.fields['categoria'].widget.attrs['list'] = 'categorias'
        self.categorias = sorted(set(categorias))


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['tipo', 'quantidade', 'custo_unitario', 'documento', 'motivo']
        labels = {'quantidade': 'Quantidade'}
        help_texts = {
            'quantidade': 'No ajuste de inventário, informe o saldo contado na prateleira.',
            'custo_unitario': 'Só para entradas. Atualiza o preço de custo da peça.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['custo_unitario'].required = False

    def clean_quantidade(self):
        quantidade = self.cleaned_data['quantidade']
        if quantidade < 0 or (quantidade == 0 and self.data.get('tipo') != MovimentacaoEstoque.Tipo.AJUSTE):
            raise forms.ValidationError('Informe uma quantidade maior que zero.')
        return quantidade
