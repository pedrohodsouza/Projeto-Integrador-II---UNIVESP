from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

from .models import Cliente, Veiculo


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
