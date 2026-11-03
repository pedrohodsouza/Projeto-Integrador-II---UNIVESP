from django import template


register = template.Library()
ICONES = {
    'inicio': 'fa-solid fa-house',
    'atendimentos': 'fa-solid fa-screwdriver-wrench',
    'novo-atendimento': 'fa-solid fa-screwdriver-wrench',
    'estoque': 'fa-solid fa-boxes-stacked',
    'fornecedores': 'fa-solid fa-truck-field',
    'clientes': 'fa-solid fa-user',
    'veiculos': 'fa-solid fa-car',
    'novo-cliente': 'fa-solid fa-user-plus',
    'entrada-peca': 'fa-solid fa-box-open',
    'plus': 'fa-solid fa-plus',
    'sucesso': 'fa-solid fa-circle-check',
    'relogio': 'fa-solid fa-clock',
    'mecanico': 'fa-solid fa-wrench',
    'usuarios': 'fa-solid fa-users-gear',
    'configuracoes': 'fa-solid fa-gear',
    'sair': 'fa-solid fa-right-from-bracket',
}


@register.inclusion_tag('oficina/_icon.html')
def icono(name):
    return {'icon_class': ICONES.get(name)}
