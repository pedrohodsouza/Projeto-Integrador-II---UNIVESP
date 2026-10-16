from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Atendimento, Cliente, Fornecedor, ItemAtendimento, MovimentacaoEstoque, Peca, Veiculo


class AtendimentoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('mecanico', password='senha-teste', first_name='Carlos')
        self.client.force_login(self.user)
        cliente = Cliente.objects.create(nome='Maria Silva', telefone='11 99999-0000')
        self.veiculo = Veiculo.objects.create(cliente=cliente, placa='ABC1D23', marca='Fiat', modelo='Uno', ano=2015)

    def criar_atendimento(self, **kwargs):
        dados = {'veiculo': self.veiculo, 'queixa': 'Barulho no freio'}
        dados.update(kwargs)
        return Atendimento.objects.create(**dados)

    def test_abrir_atendimento_registra_historico(self):
        resposta = self.client.post(reverse('atendimento_create'), {
            'veiculo': self.veiculo.pk,
            'prioridade': 'alta',
            'responsavel': self.user.pk,
            'data_entrada': timezone.localtime().strftime('%Y-%m-%dT%H:%M'),
            'queixa': 'Barulho no freio',
        })
        atendimento = Atendimento.objects.get()
        self.assertRedirects(resposta, reverse('atendimento_detail', args=[atendimento.pk]))
        self.assertEqual(atendimento.status, Atendimento.Status.AGUARDANDO)
        self.assertEqual(atendimento.criado_por, self.user)
        self.assertEqual(atendimento.historico.count(), 1)

    def test_alterar_etapa_registra_datas_e_historico(self):
        atendimento = self.criar_atendimento()
        self.client.post(reverse('atendimento_status', args=[atendimento.pk]), {'status': 'pronto'})
        atendimento.refresh_from_db()
        self.assertEqual(atendimento.status, 'pronto')
        self.assertIsNotNone(atendimento.data_conclusao)

        self.client.post(reverse('atendimento_status', args=[atendimento.pk]), {'status': 'entregue', 'comentario': 'Retirado pelo cliente'})
        atendimento.refresh_from_db()
        self.assertIsNotNone(atendimento.data_entrega)
        self.assertFalse(atendimento.em_aberto)
        self.assertEqual(atendimento.historico.first().comentario, 'Retirado pelo cliente')

    def test_itens_e_totais(self):
        atendimento = self.criar_atendimento()
        url = reverse('atendimento_item_add', args=[atendimento.pk])
        self.client.post(url, {'tipo': 'servico', 'descricao': 'Troca de pastilhas', 'quantidade': '1', 'valor_unitario': '120.00'})
        self.client.post(url, {'tipo': 'peca', 'descricao': 'Pastilha de freio', 'quantidade': '2', 'valor_unitario': '45.50'})
        self.assertEqual(atendimento.total_servicos, Decimal('120.00'))
        self.assertEqual(atendimento.total_pecas, Decimal('91.00'))
        self.assertEqual(atendimento.total, Decimal('211.00'))

        item = atendimento.itens.get(tipo='peca')
        self.client.post(reverse('atendimento_item_delete', args=[atendimento.pk, item.pk]))
        self.assertEqual(atendimento.itens.count(), 1)

    def test_atrasado(self):
        ontem = timezone.localdate() - timedelta(days=1)
        self.assertTrue(self.criar_atendimento(previsao_entrega=ontem).atrasado)
        self.assertFalse(self.criar_atendimento(previsao_entrega=ontem, status='pronto').atrasado)
        self.assertFalse(self.criar_atendimento(previsao_entrega=ontem, status='entregue').atrasado)

    def test_paginas_carregam(self):
        atendimento = self.criar_atendimento()
        for url in [
            reverse('home'), reverse('atendimento_list'), reverse('atendimento_create'),
            reverse('atendimento_detail', args=[atendimento.pk]), reverse('atendimento_edit', args=[atendimento.pk]),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get(reverse('atendimento_list')), 'ABC1D23')

    def test_exige_login(self):
        self.client.logout()
        resposta = self.client.get(reverse('atendimento_list'))
        self.assertEqual(resposta.status_code, 302)


class EstoqueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('estoquista', password='senha-teste')
        self.client.force_login(self.user)
        cliente = Cliente.objects.create(nome='João')
        veiculo = Veiculo.objects.create(cliente=cliente, placa='XYZ9A87', marca='VW', modelo='Gol')
        self.atendimento = Atendimento.objects.create(veiculo=veiculo, queixa='Troca de óleo')
        self.fornecedor = Fornecedor.objects.create(nome='Auto Peças Central')

    def cadastrar_peca(self, estoque_inicial='10'):
        self.client.post(reverse('peca_create'), {
            'referencia': 'OL-5W30', 'nome': 'Óleo 5W30', 'categoria': 'Óleos e fluidos', 'unidade': 'L',
            'fornecedor': self.fornecedor.pk, 'preco_custo': '30.00', 'preco_venda': '55.00',
            'estoque_minimo': '4', 'ativo': 'on', 'estoque_inicial': estoque_inicial,
        })
        return Peca.objects.get(referencia='OL-5W30')

    def test_cadastro_com_estoque_inicial_gera_entrada(self):
        peca = self.cadastrar_peca()
        self.assertEqual(peca.estoque_atual, Decimal('10'))
        mov = peca.movimentacoes.get()
        self.assertEqual(mov.tipo, MovimentacaoEstoque.Tipo.ENTRADA)
        self.assertEqual(mov.saldo_apos, Decimal('10'))

    def test_entrada_saida_e_ajuste(self):
        peca = self.cadastrar_peca()
        url = reverse('peca_movimentar', args=[peca.pk])
        self.client.post(url, {'tipo': 'entrada', 'quantidade': '5', 'custo_unitario': '32.00', 'documento': 'NF 123'})
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('15'))
        self.assertEqual(peca.preco_custo, Decimal('32.00'))

        self.client.post(url, {'tipo': 'saida', 'quantidade': '3', 'motivo': 'Avaria'})
        self.client.post(url, {'tipo': 'saida', 'quantidade': '100'})
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('12'))

        self.client.post(url, {'tipo': 'ajuste', 'quantidade': '11'})
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('11'))
        self.assertEqual(peca.movimentacoes.first().quantidade, Decimal('-1'))

    def test_peca_na_os_baixa_e_estorna_estoque(self):
        peca = self.cadastrar_peca()
        self.client.post(reverse('atendimento_item_add', args=[self.atendimento.pk]), {
            'tipo': 'servico', 'peca': peca.pk, 'quantidade': '4',
        })
        item = self.atendimento.itens.get()
        self.assertEqual(item.tipo, ItemAtendimento.Tipo.PECA)
        self.assertEqual(item.descricao, 'Óleo 5W30')
        self.assertEqual(item.valor_unitario, Decimal('55.00'))
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('6'))

        self.client.post(reverse('atendimento_item_delete', args=[self.atendimento.pk, item.pk]))
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('10'))

    def test_os_nao_usa_mais_que_o_estoque(self):
        peca = self.cadastrar_peca(estoque_inicial='2')
        self.client.post(reverse('atendimento_item_add', args=[self.atendimento.pk]), {
            'tipo': 'peca', 'peca': peca.pk, 'quantidade': '3',
        })
        self.assertFalse(self.atendimento.itens.exists())
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('2'))

    def test_cancelar_os_devolve_e_reabrir_baixa(self):
        peca = self.cadastrar_peca()
        self.client.post(reverse('atendimento_item_add', args=[self.atendimento.pk]), {
            'tipo': 'peca', 'peca': peca.pk, 'quantidade': '4',
        })
        status_url = reverse('atendimento_status', args=[self.atendimento.pk])
        self.client.post(status_url, {'status': 'cancelado'})
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('10'))

        self.client.post(status_url, {'status': 'em_execucao'})
        peca.refresh_from_db()
        self.assertEqual(peca.estoque_atual, Decimal('6'))

    def test_paginas_de_estoque_carregam(self):
        peca = self.cadastrar_peca()
        for url in [
            reverse('peca_list'), reverse('peca_create'), reverse('peca_detail', args=[peca.pk]),
            reverse('peca_edit', args=[peca.pk]), reverse('movimentacao_list'),
            reverse('movimentacao_list') + '?tipo=entrada', reverse('fornecedor_list'),
            reverse('fornecedor_create'), reverse('fornecedor_edit', args=[self.fornecedor.pk]),
            reverse('atendimento_detail', args=[self.atendimento.pk]), reverse('home'),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)


class CodigoAutomaticoTests(TestCase):
    def test_codigos_gerados_a_partir_da_chave_primaria(self):
        cliente = Cliente.objects.create(nome='Ana')
        veiculo = Veiculo.objects.create(cliente=cliente, placa='AAA0A00', marca='Ford', modelo='Ka')
        fornecedor = Fornecedor.objects.create(nome='Distribuidora')
        peca = Peca.objects.create(nome='Filtro de ar')
        atendimento = Atendimento.objects.create(veiculo=veiculo, queixa='Revisão')

        self.assertEqual(cliente.codigo, f'CLI-{cliente.pk:05d}')
        self.assertEqual(veiculo.codigo, f'VEI-{veiculo.pk:05d}')
        self.assertEqual(fornecedor.codigo, f'FOR-{fornecedor.pk:05d}')
        self.assertEqual(peca.codigo, f'PEC-{peca.pk:05d}')
        self.assertEqual(atendimento.codigo, f'OS-{atendimento.pk:05d}')
        self.assertEqual(atendimento.numero, atendimento.codigo)

    def test_formulario_de_peca_nao_pede_codigo(self):
        from .forms import PecaForm
        self.assertNotIn('codigo', PecaForm().fields)


class UsuarioTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('chefe', password='senha-do-chefe')
        self.client.force_login(self.admin)

    def dados(self, senha):
        return {'username': 'mecanico1', 'first_name': 'Carlos', 'email': 'c@oficina.com',
                'password1': senha, 'password2': senha}

    def test_cria_usuario_que_consegue_entrar(self):
        resposta = self.client.post(reverse('usuario_create'), self.dados('Oficina@2026'), follow=True)
        self.assertRedirects(resposta, reverse('usuario_list'))
        self.assertContains(resposta, 'mecanico1')
        self.client.logout()
        self.assertTrue(self.client.login(username='mecanico1', password='Oficina@2026'))

    def test_senha_fraca_mostra_motivo_e_nao_cria(self):
        resposta = self.client.post(reverse('usuario_create'), self.dados('123'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'O usuário não foi criado.')
        self.assertFalse(User.objects.filter(username='mecanico1').exists())
