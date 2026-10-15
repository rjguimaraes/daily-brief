# Instruções da tarefa diária — Daily Brief

Lido pela tarefa agendada antes de cada edição. Mudou uma preferência? Atualize este arquivo
(e registre em `memory/feedback.jsonl`), não o prompt da tarefa.

## Entrega
- Até **07h30 (America/Sao_Paulo)**, todos os dias.
- Terça a domingo: Daily (formato abaixo). Sábado e domingo: mesmos 13 blocos, mas Aprenda, Ideia e
  Ideias & Perspectivas mais abertos e exploratórios (história, ciência, cultura, viagens, natureza).
- Segunda-feira: Weekly Brief (13 blocos + últimos 7 dias, próximos 7 dias com agenda, evolução
  semanal dos indicadores e do clima, síntese para a Fazenda, 5 leituras em Ideias & Perspectivas).
- Formato: **documento no Claude** (conector Claude Docs), título `Daily Brief — DD/MM/AAAA`
  (`Weekly Brief — DD/MM/AAAA` na segunda). Português do Brasil. Leitura de 15–20 min.
- Modelo de referência (estrutura, tom, nível de verificação): a edição de teste de 10/10/2026,
  link em `editions/index.jsonl`.

## Ordem de trabalho
1. `git pull`. Ler: `memory/perfil.md`, `memory/criterios_conteudo.md`, os `memory/*.jsonl`
   (últimos 30 dias), `config/indicators.yaml`.
2. **Painel primeiro.** Ler `output/panel.json`, `output/quality.json`, `output/weather.json`.
   - **Terça a sábado:** se `quality.json` não for de hoje, disparar o workflow `panel.yml`
     (`gh api .../dispatches`), esperar terminar e dar `git pull`.
   - **Domingo e segunda:** mercados fechados desde sexta; não gastar esforço atualizando o painel.
     Só atualizar o Bitcoin: disparar `panel.yml` com o input `only=btc` (ou rodar
     `python scripts/run_panel.py --only btc`), dar `git pull` e usar o painel resultante. Os demais
     indicadores aparecem com o fechamento de sexta, com a data visível. Leitura curta, sem análise
     indicador por indicador. Nunca digitar, estimar ou completar número do painel: copiar
   do JSON. Célula ausente = "—" com o motivo do JSON. Escrever só a coluna Leitura.
3. Clima: a partir de `output/weather.json`. Rotular sempre: recente = estimativa de modelo;
   normal = ERA5 1995–2024; previsão = modelo. Foco em histórico e projeção; não declarar
   "águas estabelecidas" com base em evento isolado.
4. Radar: pesquisar notícias das últimas 24–48 h (WebSearch). Até 3 por categoria (Mundo, Brasil,
   Política, Agro, Pecuária); uma excelente vale mais que três medianas — dizer quando uma categoria
   tiver menos. Não repetir evento central de `memory/radar.jsonl` sem fato novo. O Radar não é
   extensão do painel. Nenhum veículo com mais de 1/3 das notícias.
5. Descoberta: Aprenda, Conhecimento Rápido, Ideia de Negócio, 2 artigos — seguindo
   `memory/criterios_conteudo.md` (padrão ousado e prático) e sem repetir os últimos 30 dias.
6. Escrever o documento: criar o esqueleto (título, byline, um bloco pendente por seção) e preencher
   uma seção por chamada.
7. Auditoria (checklist abaixo). Corrigir antes de publicar.
8. Persistir: acrescentar registros do dia em cada `memory/*.jsonl` e uma linha em
   `editions/index.jsonl` (data, URL do documento, data de referência do painel, qualidade);
   exportar o documento em Markdown para `editions/AAAA-MM-DD.md`; commit e push.

## Formato de cada bloco (como na edição de 10/10)
1. **Abertura** — 2 parágrafos: a leitura central do dia, ligando os fatos.
2. **Painel** — tabela: Indicador | Atual (data) | vs. dia anterior | vs. ~1 mês | YTD | vs. ~1 ano | Leitura.
3. **Fazenda — clima** — tabela por propriedade: recente | próximos 7 dias | distribuição; e uma
   linha de implicação operacional.
4–8. **Radar** — por notícia: manchete em negrito; O que aconteceu; Por que importa (marcar
   "leitura minha" quando for interpretação); Fonte com link direto da matéria.
9. **Hoje em 3 pontos** — Fazenda Laçada, Investimentos, Tema a monitorar. Interpretação, não manchete.
10. **Aprenda** — provocação, fenômeno, mecanismo, evidências e debate, limitações, "Onde isso
    aparece na sua vida", ideia para guardar, fontes primárias.
11. **Conhecimento Rápido** — O QUE É | COMO USAR/FAZER (exemplo executável com números) | QUANDO É ÚTIL.
12. **Ideia de Negócio** — formato completo da especificação + por que agora, economia em números
    (fonte vs. hipótese), tamanho com cálculo, vantagem do leitor, hipótese que mata, MVP, nota 1–5.
13. **Ideias & Perspectivas** (formato revisto em 15/10/2026) — por artigo, em prosa, não em ficha técnica:
    título exato com link direto, autor, veículo, data, tempo de leitura (estimativa);
    **A pergunta por trás do texto** (uma frase); 2 parágrafos curtos contando o argumento como história,
    com o caso ou número mais marcante; **Onde o texto incomoda** (a ideia que desafia o leitor);
    **Onde eu discordo** (curto, separado do autor); **Por que ler** (e o que procurar na leitura).
    Uma frase de abertura ligando os dois textos. Veículos diferentes. Só indicar artigo cujo texto foi
    aberto e lido. Sem listas de argumentos nem jargão técnico sem explicação.

## Fórmulas
- Nunca usar bloco ```latex nem notação TeX: na exportação para PDF aparece o código cru.
  Escrever fórmulas em texto simples (ex.: "NNT = 1 ÷ redução absoluta de risco"), com × e ÷,
  ou como um passo a passo numerado com números.

## Regras inegociáveis
- Nunca inventar dado, link, título, autor, data ou citação. Abrir toda página citada.
- Distinguir fato, declaração, previsão e interpretação.
- Não recomendar compra ou venda de ativos.
- Contexto patrimonial (carteira, seção 1.2 da especificação) só para explicar implicações.
- Se algo falhar (fonte, painel, conector), publicar mesmo assim com o que houver e dizer no topo
  o que faltou e por quê.

## Checklist antes de publicar
- Painel: números idênticos ao `panel.json`; datas visíveis; taxas em pb; ausências com motivo.
- Clima: locais corretos; histórico, normal e previsão separados e rotulados.
- Radar: links abertos; nada repetido sem novidade; diversidade de temas e veículos.
- Aprenda/Conhecimento/Ideia: fontes conferidas; contas refeitas em código; hipóteses marcadas.
- Artigos: título, autor, data e link conferidos na página; contrapontos próprios separados.
- Os 13 blocos presentes.
