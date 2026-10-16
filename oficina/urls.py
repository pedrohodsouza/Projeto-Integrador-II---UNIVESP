from django.urls import path

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('configuracoes/', views.configuracoes_view, name='configuracoes'),
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('veiculos/', views.veiculo_list, name='veiculo_list'),
    path('veiculos/novo/', views.veiculo_create, name='veiculo_create'),
    path('atendimentos/', views.atendimento_list, name='atendimento_list'),
    path('atendimentos/novo/', views.atendimento_create, name='atendimento_create'),
    path('atendimentos/<int:pk>/', views.atendimento_detail, name='atendimento_detail'),
    path('atendimentos/<int:pk>/editar/', views.atendimento_edit, name='atendimento_edit'),
    path('atendimentos/<int:pk>/etapa/', views.atendimento_status, name='atendimento_status'),
    path('atendimentos/<int:pk>/itens/', views.atendimento_item_add, name='atendimento_item_add'),
    path('atendimentos/<int:pk>/itens/<int:item_pk>/excluir/', views.atendimento_item_delete, name='atendimento_item_delete'),
    path('estoque/', views.peca_list, name='peca_list'),
    path('estoque/nova/', views.peca_form, name='peca_create'),
    path('estoque/movimentacoes/', views.movimentacao_list, name='movimentacao_list'),
    path('estoque/<int:pk>/', views.peca_detail, name='peca_detail'),
    path('estoque/<int:pk>/editar/', views.peca_form, name='peca_edit'),
    path('estoque/<int:pk>/movimentar/', views.peca_movimentar, name='peca_movimentar'),
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_form, name='fornecedor_create'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_form, name='fornecedor_edit'),
    path('usuarios/', views.usuario_list, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create, name='usuario_create'),
]
