from django.contrib.auth.models import User

from .models import Cliente, Veiculo


def menu_counts(request):
    if not request.user.is_authenticated:
        return {}

    return {
        'cliente_count': Cliente.objects.count(),
        'veiculo_count': Veiculo.objects.count(),
        'usuario_count': User.objects.count() if request.user.is_staff else 0,
    }
