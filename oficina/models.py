from django.db import models


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Veiculo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='veiculos')
    placa = models.CharField(max_length=10)
    marca = models.CharField(max_length=60)
    modelo = models.CharField(max_length=60)
    ano = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['placa']

    def __str__(self):
        return f'{self.placa} - {self.marca} {self.modelo}'
