# Instruções da tarefa diária — Daily Brief

Lido pela tarefa agendada antes de cada edição. Mudou uma preferência? Atualize este arquivo
(e registre em `memory/feedback.jsonl`), não o prompt da tarefa.

## Entrega
- Até **07h30 (America/Sao_Paulo)**, todos os dias.
- Terça a domingo: Daily (formato abaixo). Sábado e domingo: mesmos 14 blocos, mas Aprenda, Ideia e
  Ideias & Perspectivas mais abertos e exploratórios (história, ciência, cultura, viagens, natureza).
- Segunda-feira: Weekly Brief (14 blocos + últimos 7 dias, próximos 7 dias com agenda, evolução
  semanal dos indicadores e do clima, síntese para a Fazenda, **Relatórios do agro** (desde 16/11/2026,
  ver abaixo), 5 leituras em Ideias & Perspectivas).
- Formato: **documento no Claude** (conector Claude Docs), título `Daily Brief — DD/MM/AAAA`
  (`Weekly Brief — DD/MM/AAAA` na segunda). Português do Brasil. Leitura de 15–20 min.
- **E-mail com PDF (desde 15/11/2026):** depois de publicar e auditar, gerar o PDF (A4) **em tema escuro**
  (desde 17/11/2026: fundo #191919, texto #efefef, como o Claude em modo escuro): exportar o documento pelo
  Claude Docs em **HTML** (`export`, format html; vem em `data.bytes_b64`), decodificar e rodar
  `python scripts/dark_pdf.py <export.html> <saida.pdf> "<título>"` (Playwright/Chromium; não usar o export pdf
  do Docs, que sai claro). Conferir 1–2 páginas renderizadas. Gravar o PDF na pasta scratchpad da
  sessão e enviar pelo conector Gmail (`send_message`) para rjg.guimaraes@gmail.com, com assunto igual ao título
  (`Daily Brief — DD/MM/AAAA` ou `Weekly Brief — DD/MM/AAAA`), o PDF anexado por referência
  (`sha256:<hash>:<caminho absoluto>`; caminho fora do scratchpad/diretório de trabalho é recusado), o link do
  documento no corpo e uma linha sobre o que faltou. Se o envio falhar, avisar na notificação final e seguir.
- Modelo de referência (estrutura, tom, nível de verificação): a edição de teste de 10/10/2026,
  link em `editions/index.jsonl`.

## Ordem de trabalho
1. `git pull`. Ler: `memory/perfil.md`, `memory/criterios_conteudo.md`, os `memory/*.jsonl`
   (últimos 30 dias), `config/indicators.yaml`.
2. **Painel primeiro.** (Desde 18/11/2026, os preços do agro — CEPEA, Scot, Datagro — chegam pelo notebook do leitor: o Notícias Agrícolas bloqueia o Actions com 403. Ver `scripts/windows/LEIA-ME.md`. No Brief, esses indicadores trazem a data da última coleta do notebook; não é falha a reportar como nova, só dizer a data.)
   Ler `output/panel.json`, `output/quality.json`, `output/weather.json`.
   - **Terça a sábado:** se `quality.json` não for de hoje, disparar o workflow `panel.yml`
     (`gh api .../dispatches`), esperar terminar e dar `git pull`.
   - **Domingo e segunda:** mercados fechados desde sexta; não gastar esforço atualizando o painel.
     Só atualizar o Bitcoin: disparar `panel.yml` com o input `only=btc` (ou rodar
     `python scripts/run_panel.py --only btc`), dar `git pull` e usar o painel resultante. Os demais
     indicadores aparecem com o fechamento de sexta, com a data visível. Leitura curta, sem análise
     indicador por indicador. Nunca digitar, estimar ou completar número do painel: copiar
   do JSON. Célula ausente = "—" com o motivo do JSON. Escrever só a coluna Leitura.
3. Clima: a partir de `output/weather.json`. Rotular sempre: recente = estimativa de modelo;
   normal = ERA5 1995–2024; previsão = modelo. Apresentar só os números (histórico e projeção),
   sem análise ou implicação operacional (ajuste de 07/11/2026).
4. **Varredura das manchetes do dia (obrigatória, ANTES de qualquer seção do Radar; desde 24/11/2026).** Em 24/11
   a principal manchete global (Jensen Huang reconduzido à Nvidia por pressão de Trump) ficou fora da edição: o agente
   não conseguiu abrir Reuters/AP/BBC, apoiou-se em resumos secundários e aplicou o teste de relevância a ela.
   Regras:
   - Fazer a varredura como uma etapa separada (um subagente só para isso, antes dos de Radar), cujo produto é a
     **lista das 10 maiores notícias do dia**, em ordem, com veículo e link. Os agentes de Radar recebem essa lista.
   - Fontes: as capas de pelo menos 6 veículos globais e 3 brasileiros. Muitos sites bloqueiam leitura automatizada
     (CNN, NBC, Reuters, NYT): por isso, além de tentar abrir as capas (AP News, BBC, Guardian, Al Jazeera, PBS
     NewsHour, Washington Post, Bloomberg, FT, G1, Folha, Estadão), rodar WebSearch em modo extended com consultas
     do tipo "top news today <data>", "biggest stories <data>", "breaking news <data>", "principais notícias <data>",
     "markets today <data>" (o que moveu as bolsas é quase sempre manchete) e em espanhol. Um link que não abre não
     desqualifica a notícia: procurar a mesma história em outro veículo que abra (ex.: AP republicada pela PBS).
   - **Regra das capas:** notícia que aparece como manchete ou destaque em 2+ desses veículos é "grande fato do dia"
     e **entra obrigatoriamente** (Mundo, Brasil ou Política). O teste de relevância de 23/11 NÃO se aplica a ela: ele
     vale para notícias "diferentes"/curiosidades, não para o fato mais importante do dia. Ela só fica de fora se já
     saiu no Brief sem fato novo, e então o status diz isso.
   - No status da edição, listar as capas efetivamente checadas e as 3 maiores manchetes do dia, dizendo onde cada
     uma entrou. Nunca escrever "nenhum outro fato passou no teste" sem essa lista.
5. Radar: pesquisar notícias das últimas 24–48 h (WebSearch). Até 3 por categoria (Mundo, Brasil,
   Política, Agro, Pecuária); uma excelente vale mais que três medianas — dizer quando uma categoria
   tiver menos. Não repetir evento central de `memory/radar.jsonl` sem fato novo. O Radar não é
   extensão do painel. Nenhum veículo com mais de 1/3 das notícias.
   **Relevância (23/11/2026, ver "Ajuste de 23/11/2026" em `criterios_conteudo.md`):** notícia diferente, curiosidade ou
   inovação só entra se passar no teste de relevância (muda regra/preço/risco para ele, tem grande escala ou é tecnologia
   que ele usa ou que muda o setor dele); diferente não basta. Vale sobretudo para Radar Brasil e para as cotas.
   **Diversidade (15/11/2026, ver "Ajuste de 15/11/2026" em `criterios_conteudo.md`):** começar pela varredura
   das manchetes gerais do dia (não perder evento grande fora da agenda); famílias de tema repetidas na semana
   (petróleo/Hormuz, juros EUA, 6x1, fiscal, dívida rural, safra) só com virada de fato e no máximo 1 por
   família; cotas mínimas por edição: 1 tecnologia/ciência, 1 caso de sucesso com lição transferível, 1 agro ou
   pecuária internacional ("pode acontecer no Brasil?"); Brasil + Política com no máximo metade de economia.
6. Descoberta: Aprenda, Conhecimento Rápido, Espanhol, Ideia de Negócio, 2 artigos — seguindo
   `memory/criterios_conteudo.md` (padrão ousado e prático) e sem repetir os últimos 30 dias.
   Diversidade (21/10/2026): rodízio de áreas do perfil; M&A/avaliação no máximo 1 vez a cada 14 dias
   (o leitor não trabalha com M&A); ver "Ajuste de 21/10/2026" em `criterios_conteudo.md`.
7. Escrever o documento: criar o esqueleto (título, byline, um bloco pendente por seção) e preencher
   uma seção por chamada.
8. Auditoria (checklist abaixo). Corrigir antes de publicar.
9. Persistir: acrescentar registros do dia em cada `memory/*.jsonl` e uma linha em
   `editions/index.jsonl` (data, URL do documento, data de referência do painel, qualidade);
   exportar o documento em Markdown para `editions/AAAA-MM-DD.md`; commit e push.
10. Enviar o PDF por e-mail (ver "E-mail com PDF" em Entrega) e registrar o envio em `editions/index.jsonl`
   (campo `email`).

## Formato de cada bloco (como na edição de 10/10)
São 14 blocos desde 12/11/2026 (entrou o Espanhol, antes da Ideia de Negócio). Se o prompt da tarefa
falar em 13 blocos, vale este arquivo.
1. **Abertura** — 2 parágrafos: a leitura central do dia, ligando os fatos.
2. **Painel** — tabela: Indicador | Atual (data) | vs. dia anterior | vs. ~1 mês | YTD | vs. ~1 ano | Leitura.
   Séries mensais (IPCA, fertilizantes do Banco Mundial) mostram o mês de referência; nelas "vs. dia
   anterior" é vs. mês anterior. Fertilizantes: o índice é preço internacional em dólar; na Leitura, dar o
   contexto Brasil (ureia/KCl/MAP CFR e formulados, quando houver notícia datada). Bezerro TO (Datagro) e
   ágio TO entraram em 12/11/2026; o bezerro MS e a relação CEPEA ficam até o leitor decidir retirá-los.
3. **Fazenda — clima** — tabela por propriedade: recente | próximos 7 dias | distribuição, com a nota
   de rótulos (estimativa de modelo / ERA5 / previsão). **Só os dados, sem análise nem implicação
   operacional** (07/11/2026: os dados são de grade de modelo próxima às fazendas, não medição na
   propriedade, então interpretá-los não agrega valor). Na Weekly, idem: evolução semanal em números,
   sem leitura.
4–8. **Radar** — por notícia: manchete em negrito; O que aconteceu; Por que importa (marcar
   "leitura minha" quando for interpretação); Fonte com link direto da matéria.
9. **Hoje em 3 pontos** — Fazenda Laçada, Investimentos, Tema a monitorar. Interpretação, não manchete.
10. **Aprenda** (formato revisto em 10/11/2026: mais explicado, menos técnico) — caso ou cena de abertura;
    a ideia em uma frase simples; o mecanismo passo a passo com analogia; o que a evidência mostra (até 3
    estudos, cada um com "o que isso quer dizer" em palavras simples); o que ainda se discute e quando não
    vale; "Em resumo" (3 frases); "Onde isso aparece na sua vida" com exemplo trabalhado; ideia para
    guardar; fontes primárias. Todo número com leitura em linguagem comum; termo técnico sempre traduzido.
    Ver "Ajuste de 10/11/2026" em `criterios_conteudo.md`.
11. **Conhecimento Rápido** — O QUE É | COMO USAR/FAZER (exemplo executável com números) | QUANDO É ÚTIL.
    **Desde 17/11/2026, dias alternados são de IA** (metade das edições; ver `memory/conhecimento_rapido.jsonl`,
    campo `categoria`: se a edição anterior não foi de IA, hoje é). Objetivo do leitor: aprofundar o conhecimento e
    tirar mais proveito da IA no dia a dia. Temas em rodízio: técnicas de prompt e de trabalho com IA (dar contexto,
    exemplos, papéis, revisão adversarial, dividir tarefas); funcionalidades do Claude que ele talvez nunca usou
    (Projetos, memória, skills, tarefas agendadas, docs/artifacts, pesquisa, modo Cowork, Claude in Chrome, Excel,
    Claude Code); conectores, integrações e plugins (Gmail, Drive, Calendar, GitHub, MCP, planilhas, WhatsApp/automação);
    usos na realidade dele (fazenda: controle de rebanho, planilhas de custo, laudos e contratos, leilões, CPR;
    estudo do projeto Paraguai; investimentos; e-mail e agenda; espanhol); rotinas para otimizar o dia; limites e
    riscos (alucinação, privacidade, conferir números). O COMO USAR vira um **passo a passo executável**: um prompt
    pronto para copiar, ou o caminho exato de cliques/configuração, com um exemplo do mundo dele e o resultado
    esperado. Funcionalidades e preços mudam: conferir na documentação oficial (docs.claude.com,
    support.claude.com ou a do fornecedor) e citar o link; não prometer recurso que não foi verificado. Pode
    comparar com outras ferramentas quando útil, sem virar propaganda. Registrar `categoria` "IA" e `subtema`.
    **Trilha de IA (desde 23/11/2026):** nos dias de IA, seguir `memory/trilha_ia.md` — diagnóstico do nível do leitor
    e 17 módulos em 5 níveis (mapa do possível → entender a máquina → técnicas → conectar → construir), formato misto
    (conceito + prática de 10–20 min), um módulo por dia de IA, em ordem; registrar `trilha_modulo` (número) em
    `memory/conhecimento_rapido.jsonl`. A trilha prevalece sobre o rodízio livre de temas de IA descrito acima.
12. **Espanhol** (desde 12/11/2026; nível do leitor: iniciante/intermediário, gosta de desafio; título da seção
    "## 12. Español"). **Desde 17/11/2026, imersão gradual:** subtítulos em espanhol e, quando possível, as
    explicações também, em espanhol simples (B1). Português só onde a explicação ficaria confusa, para a
    tradução das frases-exemplo e para apontar o contraste com o português. Aumentar a proporção de espanhol
    aos poucos. **Tamanho (18/11/2026): a seção inteira se lê e se anota em 5 a 10 minutos** — cerca de
    500 a 650 palavras no total, das quais a Noticia de Paraguay fica como está (o tamanho dela agradou).
    Consejo + palavras + respostas: até ~350 palavras. Fontes de conferência numa linha curta no fim, não
    em parágrafo. Três partes, nesta ordem:
    - **Consejo del día** (até ~150 palavras): uma regra só, explicada em 2 a 3 frases, 3 exemplos curtos
      com tradução, no máximo 1 armadilha de brasileiro. Uma regra gramatical ou outro ponto importante (pronúncia, falso cognato, expressão,
      diferença Espanha × América Latina — com atenção ao espanhol do Paraguai/Rio da Prata —, armadilha comum de
      brasileiro), curta, com 3 a 4 exemplos em espanhol e tradução; quando for regra, **Miniejercicio** de 2
      frases com **Respuestas** no fim da seção. **Desde 18/11/2026, mais 2 frases de repaso**: exercícios
      curtos (completar a lacuna ou traduzir) que fazem lembrar palavras já ensinadas, tiradas do campo `palavras`
      de `memory/espanhol.jsonl`, de preferência de 3, 7 e 14+ dias atrás (repetição espaçada), sem repetir a
      mesma palavra de revisão em 7 dias. Total: 4 frases (2 da regra + 2 de repaso), todas com resposta.
    - **Tres palabras nuevas** (até ~50 palavras cada, 3 a 4 linhas). **Mistura (18/11/2026):** no máximo 1 palavra
      de agro, pecuária ou negócios por dia; as outras 2 são vocabulário geral do dia a dia (casa, família,
      viagem, emoções, conversas, cidade, saúde, tempo). Palavra (classe, gênero), pronúncia aproximada quando diferir do português,
      significado (em espanhol simples + tradução), uma frase-exemplo útil (campo, negócios, viagem, terra) e,
      se houver, o falso amigo em português. Subir a dificuldade aos poucos (padrão: B1, uma palavra B2/C1 como
      desafio). Não repetir dica nem palavra de `memory/espanhol.jsonl`; seguir uma progressão
      (ex.: ser/estar → pretéritos → subjuntivo → pronomes oblíquos → por/para → conectores → imperfeito do
      subjuntivo → voseo). Conferir regra e exemplos com fonte confiável (RAE/DLE, Instituto Cervantes); citar
      o link do DLE das 3 palavras.
    - **Noticia de Paraguay** (desde 17/11/2026): todos os dias, uma notícia paraguaia das últimas 24–72 h com
      relação direta ou indireta com o projeto da família de comprar terra no Paraguai (ver `memory/perfil.md`,
      "Projeto Paraguai"): preço e mercado de terras, pecuária e exportação de carne (Senacsa, ARP, frigoríficos,
      mercados abertos), Chaco e Corredor Bioceánico, leis de terra e de estrangeiros (franja de seguridad
      fronteriza, Indert, títulos, invasões/"carperos"), impostos e regime de investimento (IRAGRO, Ley 60/90),
      licenciamento ambiental (MADES, desmatamento no Chaco), clima e água, câmbio, segurança jurídica e
      política econômica. Formato: **manchete original em espanhol** (negrito), **Resumen** em espanhol simples
      (3–4 frases, com números e datas), **Para el proyecto** (1–2 frases, marcar "lectura mía" quando for
      interpretação) e *Fuente* com link direto da matéria aberta (preferir ABC Color, La Nación, Última Hora,
      5días, MarketData, Valor Agro, Agencia IP; fontes oficiais quando houver). Palavras difíceis da notícia
      podem ganhar tradução entre parênteses. Não repetir o evento central dos registros anteriores sem fato
      novo; registrar em `memory/espanhol.jsonl` (campo `paraguay`: manchete, tema, url). Sem notícia boa nas
      72 h (ajuste de 17/11/2026): trocar por **Dato curioso / Aprendizaje sobre Paraguay**: uma curiosidade ou
      aprendizado prático sobre investir em terra ou trabalhar com fazenda no Paraguai (ex.: como funciona a
      escritura e o registro de imóveis, o que é a franja de seguridad fronteriza, IRAGRO na prática, custo de
      abrir área no Chaco, raças e sistemas usados lá, sazonalidade do gado, mão de obra e legislação trabalhista,
      contratos de arrendamento/aparcería, logística até frigoríficos e portos). Mesmo formato: título em espanhol,
      explicação em espanhol simples com um número ou caso concreto, **Para el proyecto** e *Fuente* aberta
      (lei, órgão oficial, estudo ou matéria). Não repetir tema de `memory/espanhol.jsonl` (campo `paraguay`,
      com `tipo`: "noticia" ou "aprendizaje").
    **Repetição pedida em 23/11/2026 (temporária):** o leitor não conseguiu ler as seções Español de 19, 20, 21 e 22/11.
    Nas próximas edições, uma por dia e em ordem, a seção 12 inteira é a repetição de uma delas, no lugar do conteúdo
    novo: a fila é 2026-11-19 → 2026-11-20 → 2026-11-21 → 2026-11-22. Cada edição repete a data mais antiga da fila
    que ainda não aparece no campo `repeticao_de` de `memory/espanhol.jsonl` (assim, um dia pulado não perde nenhuma).
    - Copiar de `editions/AAAA-MM-DD.md` (bloco "## 12. Español") o Consejo del día, o Miniejercicio, as Tres palabras
      nuevas e as Respuestas como foram publicados (pode corrigir erro óbvio), com uma linha no topo: "*Repetição da
      seção de DD/11, a pedido.*"
    - **Noticia de Paraguay:** se a notícia daquela data continua relevante e não houve fato muito novo sobre o tema,
      repeti-la (pode acrescentar uma linha "Actualización" se houver detalhe novo); se perdeu relevância ou houve
      novidade maior, trazer uma notícia nova do dia no formato normal, sem repetir os eventos já registrados.
    - Registrar em `memory/espanhol.jsonl` uma linha com `"repeticao_de": "AAAA-MM-DD"`, as mesmas `palavras` e
      `dica` da data repetida e, no campo `paraguay`, a notícia usada (com `"tipo": "repetida"` ou a nova).
    - Quando as 4 datas estiverem em `repeticao_de`, a seção volta ao normal (progressão anotada em 23/11: seguir +
      gerundio / volver a + infinitivo, ou estar + gerundio), e este parágrafo pode ser apagado.
13. **Ideia de Negócio** — antes de escolher, ler `memory/ideias_feedback.jsonl` e o "Ajuste de 17/11/2026 — Revisão das
    45 ideias" e o "Ajuste de 18/11/2026 — Ideia em formato pitch" em `criterios_conteudo.md` (risco Brasil, o que
    agradou/não agradou). **Desde 18/11/2026, só um pitch de no máximo 1,5 página (≈450–550 palavras)**; a versão
    completa (economia detalhada, rampa de 3 anos, tamanho com cálculo, desafios, MVP dia a dia) só quando o leitor
    pedir para aprofundar. Estrutura do pitch, nesta ordem:
    - **Em uma frase:** quem paga, por quê e quanto (arquétipo entre parênteses).
    - **Por que agora:** 2 bullets, cada um com fonte aberta.
    - **Os números:** 4 a 5 linhas (ticket, margem, capital inicial, prazo de retorno, ordem de grandeza do mercado),
      cada número marcado "fonte" ou "hipótese"; contas conferidas em código.
    - **Por que nós:** 2 a 3 frases, incluindo como se protege do risco Brasil (ou admitir que não se protege).
    - **O que mata a ideia:** 1 frase. **Primeiro passo (7 dias, custo baixo):** 1 a 2 frases.
    - **Nota 1–5:** 1 frase de justificativa.
14. **Ideias & Perspectivas** (formato revisto em 15/10/2026) — por artigo, em prosa, não em ficha técnica:
    título exato com link direto, autor, veículo, data, tempo de leitura (estimativa);
    **A pergunta por trás do texto** (uma frase); 2 parágrafos curtos contando o argumento como história,
    com o caso ou número mais marcante; **Onde o texto incomoda** (a ideia que desafia o leitor);
    **Onde eu discordo** (curto, separado do autor); **Por que ler** (e o que procurar na leitura).
    Uma frase de abertura ligando os dois textos. Veículos diferentes. Só indicar artigo cujo texto foi
    aberto e lido. Sem listas de argumentos nem jargão técnico sem explicação.

### Weekly: Relatórios do agro (desde 16/11/2026)
Seção só da segunda-feira, depois da "Síntese da semana para a Fazenda". Pedido do leitor: monitorar relatórios
setoriais relevantes, sobretudo do Brasil, para saber se vale aprofundar a leitura (gatilho: o Global Beef
Quarterly do Rabobank citado na edição de 16/11).
- **Janela:** relatórios publicados nos últimos 7 dias (segunda a domingo anteriores). Fontes e periodicidade
  em `config/relatorios_agro.yaml`; varrer as prioritárias toda semana e as demais quando houver notícia.
- **Seleção:** de 2 a 5 relatórios, priorizando pecuária de corte, genética/reprodução, mercado de bezerro e
  reposição, crédito e insumos do Centro-Oeste/Tocantins. Brasil primeiro; internacional só se mexer com preço,
  demanda ou tecnologia que chega aqui. Semana sem relatório bom: dizer, não preencher.
- **Por relatório (triagem + veredito):** título exato com link direto (PDF ou página), instituição, data,
  número de páginas quando houver; **Tese central** (1 frase); **2–3 números** que sustentam a tese (com a
  página ou seção); **O que muda para a Laçada** (marcar "leitura minha"); **Relevância 1–5**; **Veredito**:
  *ler inteiro*, *ler só a seção/página X* ou *pular*, com o motivo em uma frase.
- **Regras:** abrir o relatório ou a página oficial; se só houver cobertura de imprensa (relatório fechado ou PDF
  que não abriu), dizer "via imprensa" e limitar a nota a 3. Não repetir relatório de `memory/relatorios.jsonl`
  sem edição nova. Registrar cada um em `memory/relatorios.jsonl` (data, título, instituição, url, relevância,
  veredito). O leitor pode responder com o que leu; usar isso para calibrar as notas.

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
- Clima: locais corretos; histórico, normal e previsão separados e rotulados; nenhuma análise.
- Radar: links abertos; nada repetido sem novidade; diversidade de temas e veículos.
- Manchetes do dia: as 3 maiores notícias da varredura (capas de 2+ veículos) estão no Brief ou têm justificativa no status;
  status lista as capas checadas.
- Aprenda/Conhecimento/Ideia: fontes conferidas; contas refeitas em código; hipóteses marcadas.
- Artigos: título, autor, data e link conferidos na página; contrapontos próprios separados.
- Espanhol: subtítulos em espanhol; regra e exemplos conferidos; 3 palavras novas, sem repetir `memory/espanhol.jsonl`;
  Noticia de Paraguay com link aberto e relação com o projeto explicada.
- Os 14 blocos presentes (Weekly: também Relatórios do agro).
