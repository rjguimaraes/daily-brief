# Trilha de IA — Conhecimento Rápido nos dias de IA (desenhada em 23/11/2026)

## Diagnóstico do leitor (respostas de 23/11/2026)
- Usa toda semana Claude e ChatGPT.
- Já faz: perguntas e textos; análise de arquivos (PDF, planilha, foto); projetos e instruções; conectores e automação.
- Automação e código: iniciante entre "criei rotinas" e "mexo com código" — fez um site com Claude + GitHub e montou
  este Daily Brief, mas "ainda tenho muito o que aprender e entender o universo do que dá pra ser feito".
- Prompts: costuma dar contexto (situação, objetivo, formato); ainda não usa exemplos, critérios, revisão adversarial
  ou fluxos em etapas de forma sistemática.
- Conceitos: conhecimento básico de contexto/memória e alucinação, mas não conseguiria explicar com segurança; modelos e
  modos, agentes e MCP não marcados.
- Maior frustração: **não sabe o que é possível** (sente que usa uma fração da ferramenta).
- Prioridades (todas): gestão da fazenda, projeto Paraguai, rotina e produtividade, investimentos e estudo.
- Formato preferido: **misto em trilha** — alternar conceito e prática, numa sequência que sobe de nível.

## Como aplicar
- Cada dia de IA do Conhecimento Rápido é o **próximo módulo da trilha**, em ordem. O módulo da vez é o primeiro desta
  lista que ainda não aparece no campo `trilha_modulo` de `memory/conhecimento_rapido.jsonl`.
- Título: "## 11. Conhecimento Rápido — Trilha de IA, módulo N/17: <tema>".
- Estrutura (mantém O QUE É | COMO USAR | QUANDO É ÚTIL, adaptada): **O QUE É** (o conceito explicado em linguagem
  simples, com uma analogia; é a parte "entender"); **COMO USAR** (prática de 10–20 minutos, passo a passo executável:
  prompt pronto para copiar ou caminho exato de cliques, aplicado à fazenda, ao Paraguai, à rotina ou aos investimentos,
  com o resultado esperado); **QUANDO É ÚTIL** (e quando não vale, limites e riscos); fechar com uma linha **"Depois
  deste módulo você consegue:"** e outra **"Próximo módulo:"**.
- Funcionalidades e preços mudam: conferir na documentação oficial (docs.claude.com, support.claude.com ou a do
  fornecedor) antes de ensinar; citar o link; não prometer recurso não verificado. Pode comparar com o ChatGPT quando
  útil (ele usa os dois), sem virar propaganda.
- Se o leitor disser que já domina um módulo, marcar como pulado (`trilha_modulo` + `"pulado": true`) e seguir.
  Se pedir para aprofundar, repetir o nível com um módulo extra antes de avançar.
- Já ensinados antes da trilha (não repetir; podem ser citados como base): Projetos como sala de dados do Paraguai
  (18/11), tarefas agendadas (20/11), extração estruturada de laudos para planilha (22/11).

## Módulos
### Nível 0 — O mapa
1. **O mapa do possível:** o que a IA já faz bem hoje, o que faz mal e onde está o ganho para ele — 12 usos concretos
   em 4 frentes (fazenda, Paraguai, rotina, investimentos), cada um com o recurso que usa (conversa, projeto, conector,
   tarefa agendada, código, agente). Prática: escolher 3 usos e testar o mais simples hoje. (responde à frustração
   principal)

### Nível 1 — Entender a máquina (conceito forte, prática curta)
2. **Contexto:** o que a IA "vê" numa conversa, janela de contexto, por que conversas longas pioram e arquivos grandes
   são lidos em parte. Prática: o "resumo de passagem" para abrir conversa nova sem perder o fio.
3. **Memória × Projetos × instruções × skills:** o que persiste onde, entre conversas e entre ferramentas. Prática:
   revisar a memória e as instruções do Claude e corrigir o que estiver errado.
4. **Alucinação:** por que a IA inventa (previsão de texto, não consulta a banco de dados) e como se proteger: pedir
   trecho literal, permitir "não encontrado", contas em código, fonte aberta. Prática: protocolo de checagem num
   contrato de arrendamento ou laudo.
5. **Modelos e modos:** modelos maiores e menores, raciocínio estendido, pesquisa na web, deep research; custo, tempo
   e quando usar cada um. Prática: a mesma pergunta do Paraguai em três modos, comparando as respostas.

### Nível 2 — Técnicas de trabalho
6. **Exemplos e critérios:** dar 2–3 exemplos do que é bom e uma régua de avaliação. Prática: modelo de e-mail para
   cliente de touro no seu estilo.
7. **Revisão adversarial:** pedir para a IA atacar o próprio trabalho ou o seu (advogado do diabo, pré-mortem). Prática:
   pré-mortem do projeto Paraguai.
8. **Tarefas grandes em etapas:** dividir, criar pontos de checagem e encadear conversas. Prática: roteiro de due
   diligence de uma fazenda em 5 etapas.
9. **Números confiáveis:** fazer a IA calcular com código/fórmula em vez de "de cabeça"; criar e ler planilhas
   (.xlsx, Claude in Excel). Prática: planilha de custo por arroba produzida.

### Nível 3 — Conectar o seu mundo
10. **Conectores (Gmail, Drive, Agenda):** o que cada um permite, permissões e cuidados. Prática: triagem semanal da
    caixa de entrada com lista de pendências.
11. **MCP e o catálogo de integrações:** o que é MCP em linguagem simples, como achar e avaliar um conector, riscos.
    Prática: mapear 3 integrações úteis para a fazenda (planilhas, WhatsApp/automação, sistemas de rebanho).
12. **Skills:** o que são e como criar uma. Prática: skill "laudo andrológico → planilha" ou "e-mail no meu estilo".
13. **IA no navegador (Claude in Chrome):** tarefas em sites (agendas de leilão, cotações, formulários) e limites de
    segurança. Prática: levantar os leilões da semana em GO e TO.

### Nível 4 — Construir
14. **Agentes e subagentes:** o que são, quando dividir trabalho entre vários (este Brief usa 10 em paralelo). Prática:
    pesquisa paralela comparando 3 regiões do Paraguai.
15. **Claude Code + GitHub por dentro:** repositório, commit, branch, como a Daily funciona e como pedir mudanças com
    segurança. Prática: uma melhoria pequena no site ou no painel.
16. **Artifacts, painéis e apps:** construir uma página compartilhável (painel de leilões, controle de touros) com
    dados que se atualizam. Prática: um painel simples para a família.
17. **Automação ponta a ponta + segurança:** tarefa agendada + conector + planilha + aviso no celular; privacidade,
    dados sensíveis, revendedores de IA. Prática: relatório semanal automático para a família (chuva, preços, agenda).

Depois do módulo 17: voltar ao rodízio livre de temas de IA (sem repetir subtema de 30 dias), ou abrir uma trilha 2 se
o leitor pedir.
