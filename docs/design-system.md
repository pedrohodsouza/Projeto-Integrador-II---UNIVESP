# Design System - Oficina Pro

Este documento define o padrão visual oficial do sistema. Qualquer alteração de UI (templates, CSS) deve seguir esta paleta para manter consistência visual.

## Paleta de Cores

| Tipo de Cor | Nome | Hex Code | Aplicação no Sistema |
|---|---|---|---|
| Primária | Azul Mecânico | `#1E293B` / `#0F172A` | Barras de navegação (sidebar), cabeçalhos e textos principais. |
| Secundária / Destaque | Vermelho Automotivo | `#DC2626` | Botões principais de ação (CTA), como "Nova Ordem de Serviço" ou "Salvar". |
| Suporte / Accent | Azul Tecnologia | `#2563EB` | Links, seleção de menus ativos e indicadores de status em andamento. |
| Fundo Principal | Branco Gelo | `#F8FAFC` | Plano de fundo das páginas principais, para garantir alta legibilidade. |
| Fundo Secundário | Cinza Oficina | `#E2E8F0` | Cards de informações, tabelas e divisores de seção. |
| Texto Secundário | Grafite Escuro | `#475569` | Textos de apoio, legendas e descrições menores. |

## Tipografia

**Fonte padrão do sistema:** [Inter](https://fonts.google.com/specimen/Inter) (Google Fonts), carregada via `<link>` no `base.html`.

- Escolhida por ser uma fonte de interface (UI) desenhada para telas, com ótima legibilidade em tamanhos pequenos (tabelas, formulários) e visual limpo, condizente com o padrão SaaS minimalista do sistema.
- Um único família de fonte é usada em todo o sistema (títulos e corpo de texto), variando apenas o peso — evita poluição visual.

| Uso | Peso | Aplicação |
|---|---|---|
| Títulos (`h1`, `h2`, `h3`) | 700 (Bold) | Cabeçalhos de página, título do card de login. |
| Botões, labels, brand | 600 / 500 (SemiBold / Medium) | CTAs, links de navegação, rótulos de formulário. |
| Corpo de texto | 400 (Regular) | Parágrafos, células de tabela, textos de apoio. |

Fallback stack (caso a fonte não carregue): `system-ui, -apple-system, "Segoe UI", sans-serif`.

## Variáveis CSS

Ao estilizar novos componentes, usar estas variáveis (definidas em `oficina/static/oficina/css/style.css`) em vez de valores hex soltos:

```css
:root {
    --cor-primaria: #1E293B;
    --cor-primaria-escura: #0F172A;
    --cor-destaque: #DC2626;
    --cor-accent: #2563EB;
    --cor-fundo: #F8FAFC;
    --cor-fundo-secundario: #E2E8F0;
    --cor-texto-secundario: #475569;
}
```

## Padrão de Navegação

O sistema segue uma organização inspirada na Apple (barra superior com menu de conta, ao estilo macOS/iOS):

- **Barra superior (`.topbar`)**: fixa no topo, fundo Azul Mecânico. À esquerda, o nome do sistema (link para o Início). À direita, o avatar do usuário.
- **Menu do usuário (`.user-menu` / `.user-dropdown`)**: ao clicar no avatar, abre um dropdown no canto superior direito com os dados da conta e os itens de administração/sistema — hoje: **Usuários** (somente para administradores), **Configurações** e **Sair**. Esse é o lugar para qualquer opção de gestão do sistema em si (não do dia a dia operacional da oficina).
- **Conteúdo principal**: a tela inicial (`home.html`) traz as opções operacionais do dia a dia — hoje **Clientes** e **Veículos** — como uma lista agrupada (`.group-card` / `.group-row`), com ícone colorido, título, subtítulo (contagem de registros) e chevron `›` indicando navegação. Novas funcionalidades de uso frequente (ex.: Ordens de Serviço) devem entrar aqui, não no menu do usuário.
- **Navegação em pilha**: páginas que não são a Início mostram um link "‹ Início" no topo do conteúdo para voltar, como no padrão de navegação por pilha do iOS.
- **Listagens de dados** (clientes, veículos, usuários) usam os mesmos componentes de lista agrupada (`.group-card` / `.group-row`) em vez de tabelas, mantendo consistência visual e melhor comportamento em mobile.

Regra geral: **opções de gestão do sistema/conta** → menu do usuário (canto superior direito). **Opções operacionais da oficina** → lista principal da tela inicial.

## Diretrizes de uso

- **Navegação e cabeçalhos**: usar Azul Mecânico (`--cor-primaria` / `--cor-primaria-escura`).
- **Ações principais** (salvar, criar, confirmar): usar Vermelho Automotivo (`--cor-destaque`) como cor do botão.
- **Ações secundárias** (cancelar, voltar): manter neutras (cinza/transparente), nunca competir com o CTA vermelho.
- **Links e itens de menu ativos**: Azul Tecnologia (`--cor-accent`).
- **Fundo de página**: Branco Gelo (`--cor-fundo`).
- **Cards, tabelas, divisores**: Cinza Oficina (`--cor-fundo-secundario`).
- **Textos de apoio** (legendas, placeholders, metadados): Grafite Escuro (`--cor-texto-secundario`).
- Manter o estilo minimalista já adotado no sistema: poucas cores por tela, bastante espaço em branco, sem gradientes ou sombras pesadas.
- Sempre validar responsividade ao aplicar novos estilos (mobile-first, breakpoints existentes em `style.css`).
