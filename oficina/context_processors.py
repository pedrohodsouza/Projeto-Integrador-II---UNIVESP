from .models import Cliente, Veiculo


def menu_counts(request):
    if not request.user.is_authenticated:
        return {}

    return {
        'cliente_count': Cliente.objects.count(),
        'veiculo_count': Veiculo.objects.count(),
    }
