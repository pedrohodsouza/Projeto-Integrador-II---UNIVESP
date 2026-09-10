from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ClienteForm, UsuarioForm, VeiculoForm
from .models import Cliente, Veiculo


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
    return render(request, 'oficina/home.html')


@login_required
def cliente_list(request):
    clientes = Cliente.objects.all()
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
    veiculos = Veiculo.objects.select_related('cliente').all()
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
