from django.contrib import admin

from .models import (
    Atendimento, Cliente, Fornecedor, HistoricoAtendimento, ItemAtendimento, MovimentacaoEstoque, Peca,
    Veiculo,
)

admin.site.register(Cliente)
admin.site.register(Veiculo)


class ItemAtendimentoInline(admin.TabularInline):
    model = ItemAtendimento
    extra = 0


class HistoricoAtendimentoInline(admin.TabularInline):
    model = HistoricoAtendimento
    extra = 0
    readonly_fields = ['status_anterior', 'status_novo', 'usuario', 'comentario', 'data']


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'veiculo', 'status', 'prioridade', 'responsavel', 'data_entrada', 'previsao_entrega']
    list_filter = ['status', 'prioridade', 'responsavel']
    search_fields = ['veiculo__placa', 'veiculo__cliente__nome', 'queixa']
    inlines = [ItemAtendimentoInline, HistoricoAtendimentoInline]


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'contato', 'telefone']
    search_fields = ['nome', 'cnpj']


@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'categoria', 'estoque_atual', 'estoque_minimo', 'preco_venda', 'ativo']
    list_filter = ['categoria', 'ativo']
    search_fields = ['nome', 'referencia', 'fabricante']
    readonly_fields = ['estoque_atual']


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['data', 'peca', 'tipo', 'quantidade', 'saldo_apos', 'atendimento', 'usuario']
    list_filter = ['tipo']

    def has_change_permission(self, request, obj=None):
        return False
