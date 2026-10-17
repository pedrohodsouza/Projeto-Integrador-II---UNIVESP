# Sistema para Oficina Mecânica

Repositório do App para o Projeto Integrador II - Eixo Computação - UNIVESP.

## Sobre o Projeto

Este projeto consiste em um **Sistema Web de Gestão para Oficinas Mecânicas**, com o objetivo de organizar o dia a dia da oficina, permitindo o controle de:
- Usuários do sistema;
- Clientes;
- Veículos e seus vínculos com os clientes;
- Atendimentos (ordens de serviço): qual veículo está na oficina, de quem é, em que etapa está, quem é o mecânico responsável, o que está sendo feito e quanto vai custar;
- Estoque de peças e fornecedores, com entradas, saídas, ajustes de inventário e baixa automática pelas ordens de serviço.

## Tecnologias

- **Backend:** Django (Python), com banco de dados via migrations.
- **Frontend:** Templates Django + **Vue.js 3** (framework JavaScript).
  - O Vue é carregado via CDN (sem etapa de build) e usado em:
    - **Painel de Atendimentos:** quadro por etapa (estilo kanban) ou lista, com indicadores clicáveis (em aberto, em execução, prontos, atrasados), busca e filtros por etapa, prioridade e mecânico.
    - **Painel de Estoque:** indicadores (peças, valor em estoque, abaixo do mínimo, sem estoque), busca, filtros por categoria e situação, e ordenação.
    - **Combobox pesquisável:** todo campo que referencia outro cadastro (cliente, veículo, mecânico, peça, fornecedor) mostra apenas o que já está cadastrado e permite digitar para filtrar, com navegação por teclado e destaque do termo buscado. Categoria e fabricante da peça sugerem os valores já usados.
    - **Listagens de Clientes, Veículos e Fornecedores:** busca em tempo real (ignora acentos e maiúsculas).
  - Os dados são enviados pelo Django com o filtro `json_script` e renderizados pelo Vue no navegador. Para não conflitar com a sintaxe `{{ }}` do Django, o Vue usa os delimitadores `[[ ]]`.
  - Código em `oficina/static/oficina/js/` (`atendimentos-vue.js`, `estoque-vue.js`, `lista-vue.js` e `combobox-vue.js`).
- **Banco de Dados:** PostgreSQL em nuvem (Supabase), compartilhado por todo o grupo e já configurado no projeto. Os testes automatizados usam SQLite local, para não alterar os dados reais.

## Como Executar

Pré-requisito: [Python 3.12 ou mais recente](https://www.python.org/downloads/) (no Windows, marque "Add Python to PATH" na instalação).

Depois de baixar o repositório, dentro da pasta dele rode **um único comando**:

```bash
python iniciar.py
```

Ele cria o ambiente virtual e instala as dependências (só na primeira vez ou quando o `requirements.txt` mudar), conecta ao banco compartilhado na nuvem, aplica atualizações pendentes, sobe o servidor e abre o navegador em `http://127.0.0.1:8000/login/`. É só entrar com o seu usuário e senha. Para encerrar, `Ctrl+C`.

O banco em nuvem (Supabase) já tem as tabelas e os dados do grupo, então não é preciso criar banco nem usuário.

> Para usar outro banco (por exemplo, um SQLite local para experimentos), copie `.env.example` para `.env` e defina `DATABASE_URL`. Num banco novo, rode `python manage.py createsuperuser` para criar o primeiro usuário.

Para rodar os testes automatizados:

```bash
python manage.py test oficina
```

## Funcionalidades Principais

- **Login e Autenticação:** Acesso ao sistema por usuário e senha.
- **Cadastro de Usuários:** Gestão de contas de acesso ao sistema (restrito a administradores).
- **Cadastro de Clientes:** Registro dos dados dos clientes da oficina.
- **Cadastro de Veículos:** Registro dos veículos, vinculados aos respectivos clientes.
- **Gestão de Atendimentos (Ordens de Serviço):**
  - Abertura de OS com veículo, km de entrada, relato do cliente, prioridade, mecânico responsável, data de entrada e previsão de entrega.
  - Etapas do atendimento: Aguardando atendimento → Em diagnóstico → Aguardando aprovação → Aguardando peças → Em execução → Controle de qualidade → Pronto para retirada → Entregue (ou Cancelado).
  - Histórico de cada mudança de etapa (quem mudou, quando e comentário), com registro automático das datas de conclusão e entrega.
  - Lançamento de serviços e peças com quantidade e valor, e totais calculados automaticamente. Peças podem vir do estoque (com baixa automática) ou ser avulsas.
  - Alerta de atraso quando a previsão de entrega passa e o veículo ainda não está pronto.
  - Histórico de atendimentos anteriores do mesmo veículo.
  - Resumo na tela inicial (em aberto, prontos para retirada, atrasados).
- **Controle de Estoque de Peças:**
  - Cadastro de peças com código, nome, categoria, fabricante, unidade de medida, fornecedor principal, preço de custo e de venda, estoque mínimo, localização na oficina e situação (ativa/inativa).
  - Movimentações: **entrada** (compra/reposição, com nº da nota e atualização do preço de custo), **saída** (perda, uso interno, devolução) e **ajuste de inventário** (corrige o saldo após contagem).
  - O saldo só muda por movimentações, e cada uma guarda quantidade, saldo resultante, usuário, data e origem.
  - Integração com os atendimentos: lançar uma peça do estoque na OS dá baixa automática; remover o item ou cancelar a OS devolve ao estoque; reabrir uma OS cancelada baixa novamente. O sistema impede saídas maiores que o saldo.
  - Alertas de peças abaixo do mínimo ou sem estoque (também na tela inicial).
  - Histórico geral de movimentações, com filtro por tipo.
- **Cadastro de Fornecedores:** nome, CNPJ, contato, telefone, e-mail e observações, com a quantidade de peças vinculadas.
- **Códigos automáticos:** todo cadastro recebe um código gerado pelo sistema a partir da chave primária, sem digitação: clientes `CLI-00001`, veículos `VEI-00001`, fornecedores `FOR-00001`, peças `PEC-00001` e ordens de serviço `OS-00001`. Na peça, o código do catálogo do fabricante pode ser informado à parte (opcional).
- **Busca em tempo real (Vue.js):** Pesquisa instantânea nas listagens de clientes e veículos, sem recarregar a página.

## Autores

Projeto desenvolvido pelos alunos da Universidade Virtual do Estado de São Paulo (UNIVESP):
- Nicole Cristine da Silva Cota
- Renan Souza Oliveira
- Pedro Henrique Oliveira de Souza
- Emilly Soares Moitinho
- Matheus Santos Moitinho
- Fabiano Inácio
- João Vitor Chaves Romão de Souza

**Tutor(a):** Marco Tulio Vilela Bueno Jardim
**Ano:** 2026

<img src="univesp-logo.jpg" alt="Logo UNIVESP" height="120">
