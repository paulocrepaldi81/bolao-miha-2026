# Retrospectiva — Bolão Miha 2026

**Para quem for organizar a próxima edição (2030) ou um bolão parecido.**
Escrito ao vivo pelo painel de 5 agentes do projeto (engenharia, dados, design/copy, jogador real, contraponto) na noite do encerramento, com a Copa e o bolão inteiros ainda frescos na memória. Documento-fonte da decisão: `/memory/bolao-miha-2026.md` (log cronológico completo de todo o projeto).

---

## Resumo executivo — se você só ler isto

1. **O motor nunca confiou em fórmula de planilha, só releu inputs brutos e recalculou tudo.** Foi a decisão mais valiosa do projeto inteiro — repita isso sempre, seja qual for a tecnologia de entrada.
2. **Todo risco sério que o projeto correu nasceu de um humano no caminho crítico sob pressão de tempo** (editar um arquivo na hora do apito final, lembrar de rodar um script, preencher célula certa sob prazo) — nunca de "lógica errada" pura. Da próxima vez, tire o humano do caminho crítico *antes* do primeiro dado real chegar, não depois de quase vazar/errar algo pro grupo inteiro.
3. **A planilha Excel foi o maior ponto de fragilidade E de atrito do sistema** — tanto para quem construiu (mapa de células hardcoded, detecção de cor, nome de arquivo = apelido) quanto para quem apostou (medo de bagunçar fórmula, sem confirmação de envio). O próprio projeto já provou que **Google Form + CSV publicado** resolve isso bem (foi o padrão usado no mata-mata desde o R32). Recomendação do painel: não é "planilha vs. sistema novo do zero" — é **estender esse mesmo padrão de Form também para a aposta inicial**, não reinventar uma plataforma.
4. **"Onde o dado pode vazar" não é só a interface que você constrói** — é toda superfície que aponta pro dado bruto (ex.: URL de um CSV público num JSON versionado num repo público). Ao decidir "isso fica público", liste todos os artefatos que tornam esse dado alcançável, não só o que aparece na tela.
5. **Nomeie o escopo temporal de cada métrica desde a primeira variável** (rodada / 1ª fase / torneio inteiro) — several bugs e retrabalhos de copy vieram de código ou rótulo que não deixava isso explícito.

---

## 1. Arquitetura e engenharia (Agente 1)

### O que funcionou muito bem

**Motor independente que nunca confia na planilha.** Decisão tomada logo no início: "não confiamos na classificação que a planilha calcula — lemos só os INPUTS do apostador e recalculamos tudo aqui" (`engine/config.py`). Eliminou de saída uma classe inteira de bugs (cache de fórmula do openpyxl, fórmula errada em célula específica). Campeão/vice/3º sempre foram deduzidos do chaveamento, nunca digitados por fé.

**ESPN como fonte primária, com 2ª fonte de auditoria.** football-data.org (mais lenta) virou a fonte de conferência via `cross_check.py`; ESPN (near-real-time, sem chave) virou a primária. O padrão "duas fontes, uma decide, a outra audita e só alerta quando ENCERRADO e a divergência PERSISTE" (6 checagens seguidas, ~30min) evitou tanto dado errado quanto flood de e-mail — vale desenhar assim desde o dia 1, não descobrir na marra (foi descoberto na marra: 21 e-mails de flood num só dia em 15/jun).

**Fail-safe em toda a cadeia, sempre na direção certa.** `validate_data.py` bloqueia o publish se o `data.json` vier quebrado — a última versão boa fica no ar. CSV do Form quebrado cai pro fallback sem derrubar o pipeline. Prazo de mata-mata sem cadastro vira "sempre visível" (nunca esconde permanentemente por erro do organizador). Esse padrão — falhar sempre pro lado que preserva o site e nunca publica dado ruim — apareceu em pelo menos 5 lugares diferentes do código.

**Ciclo de commit resiliente em vez de lock.** `concurrency: cancel-in-progress:false` (runs em fila) + push com retry (fetch + reset + re-commit) até 8 tentativas. Atacou a causa raiz (dois runs paralelos) do primeiro incidente sério do projeto, em vez de só tratar o sintoma.

**Dead-man's switch.** healthchecks.io com heartbeat no fim do workflow — se o robô parar de pingar por ~35min, e-mail automático. Barato, simples, detectaria um robô "morto" sem ninguém perceber por horas.

**Fonte única de verdade para constantes.** `EXTRA_CELLS` (nº de categorias extras), `SPECIAL_SLOTS` (movido pra `config.py`, usado por dois módulos), `HALL_DA_FAMA` (uma constante alimenta site e engine). Toda vez que uma informação vivia em dois lugares, virou fonte de bug; toda vez que foi unificada, o bug sumiu.

### Bugs reais e o que eles ensinam

- **Flood de e-mails por comparar `None` como divergência** (15/jun): ao comparar fontes assíncronas, ausência de dado é "pendente", nunca "diferente". Todo alerta de consenso multi-fonte precisa de um estado explícito de "não comparável ainda".
- **Corrida de commits** (15/jun): todo job agendado que commita precisa decidir explicitamente sua política de concorrência desde o design — não "ver depois se dá problema".
- **Movimentação sempre zerada** (15/jun): ao comparar "antes vs. agora", a baseline certa é o último estado *diferente*, não o último estado registrado.
- **Curiosidades de torneio inteiro travadas na 1ª fase** (07/jul): uma métrica "vale o torneio inteiro" implementada lendo só a fonte de dados da fase 1 — chegou a mostrar um time já eliminado como "líder". Nomeie o escopo temporal de cada métrica no schema, com teste que falha se uma fonte estiver faltando.
- **Slot "FIN"/"TER" mapeado errado, silenciosamente** (08/jul): regra geral (numeração sequencial) com uma exceção conhecida (a Final) — regras "quase sempre válidas" são onde bugs silenciosos se escondem, porque só aparecem no pior momento possível.
- **Tela de encerramento podendo mostrar campeão errado** (achado em 12/jul, mitigado em 15/jul): UI dependendo de dois pipelines assíncronos (resultado do jogo + edição manual) sem tratar o estado "meio pronto" como estado de primeira classe.
- **Vazamento por caminho indireto** (09/jul, aceito conscientemente): censurar só a interface óbvia (site) não fecha canais indiretos (URL de CSV num JSON versionado num repo público).

### O que eu faria diferente desde o início

- Desenhar o mata-mata (pontos, escopo "torneio inteiro") **junto** com a fase de grupos, não depois.
- Nunca versionar publicamente URLs de coleta de dados — GitHub Secret desde o primeiro Form.
- Testes desde o primeiro commit de qualquer componente que decide "publicar ou não" (`validate_data.py` só ganhou testes muito depois de estar em produção).
- `datetime.now(SP)` explícito em **toda** linha desde o início, inclusive testes (duas rodadas de bugs vieram de hora da máquina).
- Cache único de chamadas de API externa desde o início (o robô chegou a bater 9+ vezes na ESPN por rodada antes de consolidar).
- Autenticação leve (nem que seja um token por apelido) se a landing tiver qualquer dado sensível por período — decidir isso no design, não conviver com a limitação depois.

---

## 2. Dados, pontuação e regras (Agente 2)

### O que funcionou bem

Outcome (3/5 pts) + bônus de placar exato (nº de gols, mín. 2) foi fácil de explicar, sem contestação em toda a Copa. **Jogo especial detectado pela cor da célula** eliminou erro manual de lista hardcoded. **Classificação final com "melhor encaixe por time"** já protegia contra pontuar em dobro antes de qualquer caso real acontecer — vale escrever regras de borda antes de precisar, não depois de um prêmio errado sair no ar. **Empate tie-aware** em curiosidades e azarão resolveu de forma limpa o desfecho real (mais_goleadora, menos_vazada e azarão todos fecharam com múltiplos vencedores, sem lógica especial de última hora).

### Onde o desenho quase deu problema

O mesmo bug de "torneio inteiro" citado acima, visto pela lente de dados: a causa raiz é uma classe reconhecível — *métrica com escopo torneio inteiro, implementada lendo só a fonte da fase 1*. Segundo ponto: **campos manuais em `facts.json` sem trava** (nomes de seleção como texto livre) — mitigado incrementalmente (ESPN passou a deduzir campeão/vice/3º; `validate_data.py` ganhou checagem contra as 48 seleções conhecidas), mas o padrão certo é: toda categoria com peso em prêmio nasce com uma lista fechada de valores válidos (enum), não texto livre. Terceiro: `KNOCKOUT_POTENTIAL=250` (buffer mágico fixo) antes do cálculo real — "número redondo que parece seguro" vira dívida técnica silenciosa.

### Estatísticas: o que vale manter, o que não

O que sobreviveu a múltiplas rodadas de corte é **sobre a pessoa que olha, não sobre o bolão em abstrato**: "Minha Aposta", "pé-frio do bolão" (cumulativo, comparável), "jogo de agora" (muda a cada partida). O que foi cortado era **estático ou sem gancho emocional**: "mais otimista", "mais perto da eliminação", "Dor da rodada" (duplicava outro card). Pergunta-teste antes de construir uma estatística nova: *isso muda a cada rodada e aponta pra uma pessoa específica?* Se não, é candidato a corte desde o design.

### A ideia da planilha, vista pelos dados

Sem planilha, o ganho seria estrutural: hoje cada aposta é um `.xlsx` solto que o motor *reconstrói* a partir de células soltas — qualquer desalinhamento de linha/coluna é silencioso até alguém notar (o próprio projeto teve um: célula errada em 3 lugares do "Cálculos"). Um formulário estruturado (campo por jogo, tipo forçado, enum fechado) elimina essa classe de bug inteira. Em troca, perde-se a familiaridade da planilha — mas, do ponto de vista de dados, validação na entrada sempre vale mais que validação na saída.

---

## 3. Design, copy e comunicação (Agente 3)

### O que funcionou muito bem

**Coerência de sistema, não peças isoladas.** O "design premium pass" (06/jul) colapsou uma escala tipográfica caótica em 6 variáveis, e o dourado ganhou uma variante única para números de destaque. O detalhe que mais valeu foi a **disciplina de raridade**: o gradiente arco-íris tri-nação ficou reservado para um único lugar da página — "significar algo por ser raro em vez de decoração repetida" (decisão consciente registrada na memória).

**Tom de voz caloroso-mas-nunca-debochado**, grudado no dado, não em banners: "ninguém traindo o próprio campeão agora — fé que não escala, é chão" (quando zero). Ri da situação, nunca do apostador.

**Padrão teaser/revelação**, cristalizado em "O Xerife Deu o Play": esconde o quê, nunca mente sobre a existência do dado, revela na hora certa. A mesma arquitetura foi reaproveitada para a censura de privacidade do mata-mata (placar oculto até o prazo, selo "mudou/manteve" sempre visível).

### Lições de comunicação

A mais cara: **sequenciamento de aviso**. Quando o prazo do mata-mata mudou de regra (23h da véspera → meio-dia do mesmo dia, a partir das Quartas), o RUNBOOK precisou ser explícito — "avise que a REGRA mudou, não só o novo prazo". Apostador lê a última frase e assume que o resto continua igual. Todo aviso de mudança de regra deveria abrir com "MUDOU: [o que era] → [o que passa a ser]".

Segunda: **rótulos que confundiam métrica com número absoluto** ("Melhor taxa de placar exato" quando era contagem; "Pé-frio da rodada" quando era cumulativo) — o texto herda o nome de uma versão anterior do cálculo. Terceira: **número isolado não tem sentido** — "Quem tá torcendo escondido" só ficou claro depois de emparelhar cada número com "de N apostadores no bolão".

### Kit de largada pra próxima vez

Herdar 100% pronto: paleta, escala tipográfica em variáveis, serif reservada para momentos editoriais, "elemento raro usado uma vez só", padrão teaser/revelação, tom "ri da situação, não da pessoa". Repensar do zero: escrever o "roteiro de taglines por marco" (abertura, 1ª fase, mata-mata, final, fechamento) **antes** do torneio começar, e formalizar "MUDOU: X → Y" como template fixo de aviso de regra no RUNBOOK.

---

## 4. Experiência do jogador (Agente 4)

### O que foi ótimo

"Minha Aposta" no topo do site — buscar o apelido, ver a carteirinha com ✓/⭐/0/⏳ assim que o placar saía, sem precisar abrir planilha nenhuma. Atualização do mata-mata via Form (um por fase, só os jogos daquela fase) foi rápida e sem risco de mexer no que não devia. Prazo sempre visível por fase tirou a ansiedade de "será que ainda dá tempo". Regra de prêmio sem ambiguidade nenhuma — ninguém perguntou "como isso é calculado".

### Atritos reais

O mais sério: a busca de apelido em "Minha Aposta" nunca teve login — inofensivo enquanto os palpites eram só leitura, virou brecha real de espionagem quando o mata-mata passou a permitir atualização (percebido só DEPOIS de uma fase inteira já ter rodado sem essa proteção). Se o desenho já prevê "atualizar palpite com prazo" em algum momento futuro, a decisão de esconder placar-antes-do-prazo precisa nascer **junto**, não ser descoberta reativamente. Segundo: mudança de prazo passa despercebida pra quem só olha o WhatsApp de vez em quando — merece aviso gritante e repetido, não uma linha no Form novo.

### Pro próximo bolão

Sem planilha é sonho, não pesadelo, **se bem feito**. A `.xlsx` é o pior ponto de atrito hoje (baixar arquivo, não bagunçar fórmula, nome do arquivo = apelido). Um Form direto resolveria — desde que tenha: uma tela de resumo antes de confirmar (ver a aposta inteira de uma vez, como a planilha permite hoje) e uma confirmação de envio clara. Sem isso, vira pesadelo (gente insegura se o palpite foi salvo). Com isso, fica estritamente melhor que a planilha.

---

## 5. Contraponto e visão de conjunto (Agente 5)

### Os 3 maiores riscos que o projeto correu

1. **A "janela do campeão errado"** — voltou mais de uma vez ao longo da jornada, só fechada de vez quando a dedução de campeão/vice/3º virou automática via ESPN. Por semanas, o sistema ficou desenhado para publicar um resultado errado por padrão, na torcida de um humano editar um arquivo a tempo.
2. **Limites ocultos de infraestrutura de terceiros** — bloqueio de créditos do Netlify e corrida de commits só apareceram sob uso real, em produção, com o bolão rodando ao vivo.
3. **Vazamento estrutural via repo público** — tornar o repo público (decisão de custo) criou uma superfície de exposição (URL do CSV do Form, versionada) que ninguém tinha mapeado antes.

**O que os três têm em comum:** nenhum foi "bug que passou no teste". Todos nasceram de decisões por razões econômicas ou de conveniência, cujo preço só apareceu rodando ao vivo, sob pressão de tempo real — não de lógica errada.

### A ideia da planilha: vale abandonar?

A favor: o Excel custou caro em fragilidade silenciosa (mapa de células hardcoded, detecção de cor como dado estruturado, nome de arquivo = apelido, 88 planilhas fora do git por privacidade = zero histórico auditável do dado bruto). Contra abandonar de forma abrupta: o próprio projeto já provou, sem inventar nada novo, que Google Form + CSV publicado resolve isso — foi exatamente o padrão do mata-mata desde o R32, e funcionou. Construir "outro sistema" do zero é projeto de escopo comparável ao motor inteiro que já existe e funciona (110+ testes, validação, fail-closed) — há risco real de trocar um pipeline maduro por um sistema novo com bugs desconhecidos, bem na hora com menos margem de erro (abertura do bolão).

**Recomendação honesta:** não é "planilha vs. sistema novo do zero" — é **estender o padrão de Form que já se provou também para a aposta inicial**, não só o mata-mata. Guardar essa direção para 2030, não como decisão final.

### O maior aprendizado, em 1 parágrafo

Toda vez que este projeto colocou um humano no caminho crítico sob pressão de tempo, o risco real apareceu — e toda vez que o sistema removeu o humano do caminho crítico, o risco desapareceu de vez. Para 2030: desenhe assumindo que a pessoa responsável vai estar viajando, cansada, ou vai esquecer exatamente no momento decisivo — e construa a automação e os guard-rails **antes** do primeiro dado real chegar, não como correção depois que quase deu errado na frente de todo mundo.

---

*Compilado por Claude a partir do painel de 5 agentes do projeto, na noite do encerramento do Bolão Miha 2026 (22/07/2026). Fonte cronológica completa: memória do projeto (`bolao-miha-2026.md`) e o repositório `bolao-miha-2026` no GitHub.*
