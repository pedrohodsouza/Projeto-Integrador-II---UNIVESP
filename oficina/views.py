from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AtendimentoForm, ClienteForm, FornecedorForm, ItemAtendimentoForm, MovimentacaoForm, PecaForm,
    StatusAtendimentoForm, UsuarioForm, VeiculoForm,
)
from .models import (
    Atendimento, Cliente, EstoqueInsuficiente, Fornecedor, ItemAtendimento, MovimentacaoEstoque, Peca,
    Veiculo,
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'oficina/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    abertos = Atendimento.objects.exclude(status__in=Atendimento.STATUS_FINAIS)
    context = {
        'cliente_count': Cliente.objects.count(),
        'veiculo_count': Veiculo.objects.count(),
        'atendimento_aberto_count': abertos.count(),
        'atendimento_pronto_count': abertos.filter(status=Atendimento.Status.PRONTO).count(),
        'atendimento_atrasado_count': abertos.exclude(status=Atendimento.Status.PRONTO).filter(
            previsao_entrega__lt=timezone.localdate()
        ).count(),
        'peca_count': Peca.objects.filter(ativo=True).count(),
        'peca_baixa_count': Peca.objects.filter(ativo=True, estoque_atual__lte=F('estoque_minimo')).count(),
        'fornecedor_count': Fornecedor.objects.count(),
    }
    return render(request, 'oficina/home.html', context)


@login_required
def configuracoes_view(request):
    return render(request, 'oficina/configuracoes.html')


@login_required
def cliente_list(request):
    clientes = list(Cliente.objects.values('id', 'nome', 'telefone', 'email'))
    return render(request, 'oficina/cliente_list.html', {'clientes': clientes})


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente cadastrado com sucesso.')
            return redirect('cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'oficina/cliente_form.html', {'form': form})


@login_required
def veiculo_list(request):
    veiculos = list(
        Veiculo.objects.select_related('cliente').values(
            'id', 'placa', 'marca', 'modelo', 'ano', 'cliente__nome'
        )
    )
    return render(request, 'oficina/veiculo_list.html', {'veiculos': veiculos})


@login_required
def veiculo_create(request):
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo cadastrado com sucesso.')
            return redirect('veiculo_list')
    else:
        form = VeiculoForm()
    return render(request, 'oficina/veiculo_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def usuario_list(request):
    usuarios = User.objects.all()
    return render(request, 'oficina/usuario_list.html', {'usuarios': usuarios})


@login_required
@user_passes_test(lambda u: u.is_staff)
def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário cadastrado com sucesso.')
            return redirect('usuario_list')
    else:
        form = UsuarioForm()
    return render(request, 'oficina/usuario_form.html', {'form': form})


def _nome_usuario(user):
    return (user.get_full_name() or user.username) if user else ''


@login_required
def atendimento_list(request):
    atendimentos = Atendimento.objects.select_related('veiculo__cliente', 'responsavel')
    dados = [
        {
            'id': a.pk,
            'numero': a.numero,
            'status': a.status,
            'status_label': a.get_status_display(),
            'prioridade': a.prioridade,
            'prioridade_label': a.get_prioridade_display(),
            'placa': a.veiculo.placa,
            'veiculo': f'{a.veiculo.marca} {a.veiculo.modelo}',
            'cliente': a.veiculo.cliente.nome,
            'responsavel': _nome_usuario(a.responsavel),
            'queixa': a.queixa,
            'entrada': a.data_entrada.isoformat(),
            'previsao': a.previsao_entrega.isoformat() if a.previsao_entrega else None,
            'atrasado': a.atrasado,
            'em_aberto': a.em_aberto,
        }
        for a in atendimentos
    ]
    context = {
        'atendimentos': dados,
        'etapas': [{'valor': v, 'rotulo': r} for v, r in Atendimento.Status.choices],
    }
    return render(request, 'oficina/atendimento_list.html', context)


@login_required
def atendimento_create(request):
    veiculo_id = request.GET.get('veiculo')
    if request.method == 'POST':
        form = AtendimentoForm(request.POST)
        if form.is_valid():
            atendimento = form.save(commit=False)
            atendimento.criado_por = request.user
            atendimento.save()
            atendimento.historico.create(
                status_novo=atendimento.status, usuario=request.user, comentario='Atendimento aberto.',
            )
            messages.success(request, f'Atendimento {atendimento.numero} aberto com sucesso.')
            return redirect('atendimento_detail', pk=atendimento.pk)
    else:
        form = AtendimentoForm(initial={'veiculo': veiculo_id, 'data_entrada': timezone.localtime()})
    return render(request, 'oficina/atendimento_form.html', {'form': form})


@login_required
def atendimento_edit(request, pk):
    atendimento = get_object_or_404(Atendimento, pk=pk)
    if request.method == 'POST':
        form = AtendimentoForm(request.POST, instance=atendimento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atendimento atualizado.')
            return redirect('atendimento_detail', pk=pk)
    else:
        form = AtendimentoForm(instance=atendimento)
    return render(request, 'oficina/atendimento_form.html', {'form': form, 'atendimento': atendimento})


@login_required
def atendimento_detail(request, pk):
    atendimento = get_object_or_404(
        Atendimento.objects.select_related('veiculo__cliente', 'responsavel', 'criado_por')
        .prefetch_related('itens', 'historico__usuario'),
        pk=pk,
    )
    context = {
        'atendimento': atendimento,
        'etapa_atual': Atendimento.Status.values.index(atendimento.status),
        'status_form': StatusAtendimentoForm(initial={'status': atendimento.status}),
        'item_form': ItemAtendimentoForm(),
        'outros_atendimentos': atendimento.veiculo.atendimentos.exclude(pk=pk)[:5],
    }
    return render(request, 'oficina/atendimento_detail.html', context)


@login_required
@require_POST
def atendimento_status(request, pk):
    atendimento = get_object_or_404(Atendimento, pk=pk)
    form = StatusAtendimentoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Não foi possível atualizar a etapa.')
        return redirect('atendimento_detail', pk=pk)
    try:
        atendimento.alterar_status(
            form.cleaned_data['status'], usuario=request.user, comentario=form.cleaned_data['comentario'],
        )
    except EstoqueInsuficiente as erro:
        messages.error(request, f'Não foi possível reabrir o atendimento. {erro}')
    else:
        messages.success(request, f'Etapa atualizada para "{atendimento.get_status_display()}".')
    return redirect('atendimento_detail', pk=pk)


def _erros_do_form(form):
    return '; '.join(erro for lista in form.errors.values() for erro in lista)


@login_required
@require_POST
def atendimento_item_add(request, pk):
    atendimento = get_object_or_404(Atendimento, pk=pk)
    if not atendimento.em_aberto:
        messages.error(request, 'Não é possível lançar itens em um atendimento finalizado.')
        return redirect('atendimento_detail', pk=pk)
    form = ItemAtendimentoForm(request.POST)
    if not form.is_valid():
        messages.error(request, f'Item não adicionado: {_erros_do_form(form)}')
        return redirect('atendimento_detail', pk=pk)
    item = form.save(commit=False)
    item.atendimento = atendimento
    try:
        with transaction.atomic():
            item.save()
            if item.peca:
                item.peca.movimentar(
                    MovimentacaoEstoque.Tipo.SAIDA, item.quantidade, request.user,
                    f'Aplicada em {atendimento.numero}', atendimento=atendimento,
                )
    except EstoqueInsuficiente as erro:
        messages.error(request, str(erro))
    else:
        complemento = ' Estoque atualizado.' if item.peca else ''
        messages.success(request, f'{item.get_tipo_display()} adicionado(a).{complemento}')
    return redirect('atendimento_detail', pk=pk)


@login_required
@require_POST
def atendimento_item_delete(request, pk, item_pk):
    item = get_object_or_404(
        ItemAtendimento.objects.select_related('atendimento', 'peca'), pk=item_pk, atendimento_id=pk,
    )
    atendimento = item.atendimento
    devolvida = bool(item.peca) and atendimento.status != Atendimento.Status.CANCELADO
    with transaction.atomic():
        if devolvida:
            item.peca.movimentar(
                MovimentacaoEstoque.Tipo.ENTRADA, item.quantidade, request.user,
                f'Estorno: item removido de {atendimento.numero}', atendimento=atendimento,
            )
        item.delete()
    complemento = ' Peça devolvida ao estoque.' if devolvida else ''
    messages.success(request, f'Item removido.{complemento}')
    return redirect('atendimento_detail', pk=pk)


@login_required
def peca_list(request):
    pecas = Peca.objects.select_related('fornecedor')
    dados = [
        {
            'id': p.pk,
            'codigo': p.codigo,
            'nome': p.nome,
            'categoria': p.categoria,
            'fabricante': p.fabricante,
            'fornecedor': p.fornecedor.nome if p.fornecedor else '',
            'unidade': p.unidade,
            'estoque': float(p.estoque_atual),
            'minimo': float(p.estoque_minimo),
            'custo': float(p.preco_custo),
            'venda': float(p.preco_venda),
            'localizacao': p.localizacao,
            'ativo': p.ativo,
        }
        for p in pecas
    ]
    return render(request, 'oficina/peca_list.html', {'pecas': dados})


@login_required
def peca_form(request, pk=None):
    peca = get_object_or_404(Peca, pk=pk) if pk else None
    form = PecaForm(request.POST or None, instance=peca)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            salva = form.save()
            inicial = form.cleaned_data.get('estoque_inicial')
            if peca is None and inicial:
                salva.movimentar(MovimentacaoEstoque.Tipo.ENTRADA, inicial, request.user, 'Estoque inicial')
        messages.success(request, f'Peça "{salva.nome}" salva com sucesso.')
        return redirect('peca_detail', pk=salva.pk)
    return render(request, 'oficina/peca_form.html', {'form': form, 'peca': peca})


@login_required
def peca_detail(request, pk):
    peca = get_object_or_404(Peca.objects.select_related('fornecedor'), pk=pk)
    return render(request, 'oficina/peca_detail.html', {
        'peca': peca,
        'movimentacoes': peca.movimentacoes.select_related('usuario', 'atendimento')[:50],
        'form': MovimentacaoForm(initial={
            'tipo': MovimentacaoEstoque.Tipo.ENTRADA, 'custo_unitario': peca.preco_custo,
        }),
    })


@login_required
@require_POST
def peca_movimentar(request, pk):
    peca = get_object_or_404(Peca, pk=pk)
    form = MovimentacaoForm(request.POST)
    if not form.is_valid():
        messages.error(request, f'Movimentação não registrada: {_erros_do_form(form)}')
        return redirect('peca_detail', pk=pk)
    dados = form.cleaned_data
    entrada = dados['tipo'] == MovimentacaoEstoque.Tipo.ENTRADA
    try:
        peca.movimentar(
            dados['tipo'], dados['quantidade'], request.user, dados['motivo'],
            custo_unitario=dados['custo_unitario'] if entrada else None,
            documento=dados['documento'],
        )
    except EstoqueInsuficiente as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, f'Movimentação registrada. Saldo atual: {peca.estoque_atual:g} {peca.unidade}.')
    return redirect('peca_detail', pk=pk)


@login_required
def movimentacao_list(request):
    movimentacoes = MovimentacaoEstoque.objects.select_related('peca', 'usuario', 'atendimento')
    tipo = request.GET.get('tipo', '')
    if tipo in MovimentacaoEstoque.Tipo.values:
        movimentacoes = movimentacoes.filter(tipo=tipo)
    return render(request, 'oficina/movimentacao_list.html', {
        'movimentacoes': movimentacoes[:200],
        'tipos': MovimentacaoEstoque.Tipo.choices,
        'tipo_atual': tipo,
    })


@login_required
def fornecedor_list(request):
    fornecedores = list(
        Fornecedor.objects.annotate(qtd_pecas=Count('pecas')).values(
            'id', 'nome', 'cnpj', 'contato', 'telefone', 'email', 'qtd_pecas',
        )
    )
    return render(request, 'oficina/fornecedor_list.html', {'fornecedores': fornecedores})


@login_required
def fornecedor_form(request, pk=None):
    fornecedor = get_object_or_404(Fornecedor, pk=pk) if pk else None
    form = FornecedorForm(request.POST or None, instance=fornecedor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fornecedor salvo com sucesso.')
        return redirect('fornecedor_list')
    return render(request, 'oficina/fornecedor_form.html', {'form': form, 'fornecedor': fornecedor})
