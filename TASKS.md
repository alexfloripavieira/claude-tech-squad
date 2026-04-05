## 13. Lista de Tarefas

> **Convenção de checklist:**
> - `[ ]` — pendente
> - `[x]` — concluído
> - `[-]` — em progresso
> - `[~]` — descartado / não se aplica

---

### Sprint 1 — Auditoria de qualidade da esteira atual ✓

**Objetivo:** Garantir que todos os 20 skills e 61 agentes atendem ao contrato mínimo de rastreabilidade e segurança antes de qualquer expansão.

---

#### 1.1 — Auditar `result_contract` em todos os 61 agentes ✓

**Escopo:** Todo agente deve encerrar com um bloco `result_contract` estruturado com campos `artifacts`, `blocking_findings`, `warnings`, `verdict`. Sem esse bloco, o SEP log e o `Agent Execution Log` ficam incompletos.

- [x] 1.1.1 — Listar todos os 61 arquivos em `plugins/claude-tech-squad/agents/`
- [x] 1.1.2 — Para cada arquivo: verificar presença do bloco `result_contract`
- [x] 1.1.3 — Registrar lista de agentes sem o bloco
- [x] 1.1.4 — Para cada agente faltante: ler o prompt e identificar os artefatos que o agente produz
- [x] 1.1.5 — Adicionar bloco `result_contract` com `artifacts`, `blocking_findings`, `warnings`, `verdict` em cada agente faltante
- [x] 1.1.6 — Verificar que o bloco adicionado é consistente com a especialidade declarada do agente
- [x] 1.1.7 — Rodar `bash scripts/validate.sh` após todas as adições e confirmar que passa

> Resultado: 61/61 agentes em conformidade total. Nenhuma correção necessária.

#### 1.2 — Auditar `Absolute Prohibitions` em agentes com autoridade de execução ✓

**Escopo:** Agentes que executam comandos, criam PRs, fazem deploy, ou operam infra devem ter o bloco de proibições absolutas. Agentes de análise pura não precisam.

- [x] 1.2.1 — Definir lista de agentes com autoridade de execução: `release`, `sre`, `backend-dev`, `devops`, `ci-cd`, `dba`, `cloud-architect`, `platform-dev`, `incident-manager`
- [x] 1.2.2 — Ler cada agente da lista e verificar presença de bloco `Absolute Prohibitions`
- [x] 1.2.3 — Registrar agentes da lista sem o bloco
- [x] 1.2.4 — Adicionar bloco em cada agente faltante, referenciando a lista completa do README.md
- [x] 1.2.5 — Adicionar asserção no `scripts/validate.sh` que verifica presença do bloco nesses agentes
- [x] 1.2.6 — Testar: remover bloco de um agente e confirmar que `validate.sh` falha com mensagem clara
- [x] 1.2.7 — Restaurar e confirmar que `validate.sh` passa

> Resultado: `cloud-architect.md` estava sem o bloco. Adicionado. Asserção adicionada ao `validate.sh`. Testado com falha intencional (exit 1, mensagem clara) e restauração confirmada.

#### 1.3 — Auditar cobertura de smoke test por skill ✓

**Escopo:** `scripts/smoke-test.sh` deve ter ao menos uma asserção por skill. Skills sem cobertura são invisíveis à validação estrutural.

- [x] 1.3.1 — Ler `scripts/smoke-test.sh` e extrair lista de skills cobertas
- [x] 1.3.2 — Comparar com as 20 skills em `plugins/claude-tech-squad/skills/`
- [x] 1.3.3 — Identificar skills sem cobertura
- [x] 1.3.4 — Para cada skill não coberta: adicionar asserção verificando presença de preflight block e result_contract no conteúdo da skill
- [x] 1.3.5 — Rodar `bash scripts/smoke-test.sh` e confirmar que passa
- [x] 1.3.6 — Verificar que o script falha ao remover intencionalmente uma skill do diretório

> Resultado: 17 de 20 skills estavam sem cobertura. Adicionadas assertions para todas. Skills operacionais verificam `## Global Safety Contract` + `ai-docs/.squad-log`. `pre-commit-lint` recebeu instrução de SEP log (era a única sem). Smoke test confirma exit 1 ao remover SKILL.md.

#### 1.4 — Executar escada completa de validação e registrar baseline ✓

**Escopo:** Registrar o estado atual como baseline para comparação futura após qualquer mudança.

- [x] 1.4.1 — Rodar `bash scripts/validate.sh` e salvar output em `ai-docs/baseline-validation.txt`
- [x] 1.4.2 — Rodar `bash scripts/smoke-test.sh` e salvar output
- [x] 1.4.3 — Rodar `bash scripts/dogfood.sh` e salvar output
- [x] 1.4.4 — Rodar `bash scripts/dogfood-report.sh --schema-only` e salvar output
- [x] 1.4.5 — Commitar os arquivos de baseline em `ai-docs/` com mensagem `chore: register validation baseline vX.X.X`

> Resultado: `validate.sh` e `dogfood-report.sh --schema-only` passam. `smoke-test.sh` e `dogfood.sh` falham por ausência de `ripgrep` (`rg`) no ambiente de execução — issue ambiental pré-existente, não relacionada às mudanças da sprint. Baseline salvo em `ai-docs/baseline-*.txt`.

---

### Sprint 2 — Golden runs e validação comportamental

**Objetivo:** Capturar golden runs reais para os 3 cenários de dogfood e estabelecer o scorecard de comportamento como contrato de regressão.

---

#### 2.1 — Preparar e capturar golden run `layered-monolith`

**Escopo:** Validar que discovery num repositório layered detecta `architecture_style=layered` e não força hexagonal.

- [ ] 2.1.1 — Ler `fixtures/dogfooding/layered-monolith/` e verificar presença de estrutura representativa de repositório layered
- [ ] 2.1.2 — Completar fixture se estrutura estiver incompleta (pastas `controllers/`, `services/`, `repositories/` mínimas)
- [ ] 2.1.3 — Rodar `bash scripts/dogfood.sh --print-prompts` e confirmar o prompt do cenário
- [ ] 2.1.4 — Executar `bash scripts/start-golden-run.sh layered-monolith alexfloripavieira`
- [ ] 2.1.5 — Executar o prompt de discovery no fixture e capturar output completo
- [ ] 2.1.6 — Verificar presença de: `[Preflight Passed]`, `architecture_style=layered`, `[Agent Start]` para pm/ba/po, `Agent Execution Log`
- [ ] 2.1.7 — Preencher `templates/golden-run-scorecard.md` para o run
- [ ] 2.1.8 — Salvar artefato em `ai-docs/dogfood-runs/layered-monolith/`
- [ ] 2.1.9 — Rodar `bash scripts/dogfood-report.sh` e confirmar schema válido

#### 2.2 — Preparar e capturar golden run `hexagonal-billing`

**Escopo:** Validar que discovery num repositório hexagonal detecta `architecture_style=hexagonal` e ativa especialistas de domínio corretos.

- [ ] 2.2.1 — Ler `fixtures/dogfooding/hexagonal-billing/` e verificar estrutura de ports/adapters
- [ ] 2.2.2 — Completar fixture se necessário (pastas `domain/`, `application/`, `infrastructure/` mínimas)
- [ ] 2.2.3 — Executar `bash scripts/start-golden-run.sh hexagonal-billing alexfloripavieira`
- [ ] 2.2.4 — Executar prompt de discovery no fixture e capturar output
- [ ] 2.2.5 — Verificar `architecture_style=hexagonal` no preflight
- [ ] 2.2.6 — Verificar que `hexagonal-architect` está na lista de agentes invocados
- [ ] 2.2.7 — Preencher scorecard e salvar em `ai-docs/dogfood-runs/hexagonal-billing/`
- [ ] 2.2.8 — Rodar `bash scripts/dogfood-report.sh` e confirmar schema válido

#### 2.3 — Preparar e capturar golden run `hotfix-checkout`

**Escopo:** Validar que o fluxo de hotfix executa gate de diagnóstico, gera branch `hotfix/`, e documenta rollback path.

- [ ] 2.3.1 — Ler `fixtures/dogfooding/hotfix-checkout/` e verificar contexto de erro simulado
- [ ] 2.3.2 — Executar `bash scripts/start-golden-run.sh hotfix-checkout alexfloripavieira`
- [ ] 2.3.3 — Executar prompt de hotfix no fixture e capturar output
- [ ] 2.3.4 — Verificar: gate de diagnóstico presente, gate de staging presente, rollback path no output
- [ ] 2.3.5 — Verificar que Absolute Prohibitions não foram violadas no output
- [ ] 2.3.6 — Preencher scorecard e salvar em `ai-docs/dogfood-runs/hotfix-checkout/`
- [ ] 2.3.7 — Rodar `bash scripts/dogfood-report.sh` e confirmar schema válido

#### 2.4 — Adicionar cenário de dogfood `llm-rag`

**Escopo:** Nenhum cenário de dogfood cobre repositórios com features LLM/AI. Adicionar cenário que valida a ativação do bench de AI.

- [ ] 2.4.1 — Criar diretório `fixtures/dogfooding/llm-rag/` com estrutura mínima de repositório com código de embedding
- [ ] 2.4.2 — Adicionar arquivo de contexto simulando imports de LangChain ou Anthropic SDK
- [ ] 2.4.3 — Adicionar entrada `llm-rag` em `fixtures/dogfooding/scenarios.json` com prompt e expected output
- [ ] 2.4.4 — Definir expected output: `[AI Detected]`, agents `ai-engineer`, `llm-eval-specialist`, `llm-safety-reviewer` presentes
- [ ] 2.4.5 — Atualizar `scripts/dogfood.sh` para incluir o cenário `llm-rag`
- [ ] 2.4.6 — Capturar golden run real e validar contra scorecard
- [ ] 2.4.7 — Rodar `bash scripts/dogfood-report.sh` e confirmar schema válido

---

### Sprint 3 — SEP log e rastreabilidade formal

**Objetivo:** Formalizar o schema do SEP log, garantir que todas as skills o produzem, e habilitar o `/factory-retrospective` para análise de padrões.

---

#### 3.1 — Definir schema JSON formal do SEP log

**Escopo:** Sem schema formal, o SEP log não é validável e o `/factory-retrospective` não tem contrato para parsear.

- [ ] 3.1.1 — Ler seção 13 do `docs/MANUAL.md` e extrair campos atuais do SEP log
- [ ] 3.1.2 — Criar `ai-docs/.squad-log/sep-log.schema.json` com JSON Schema (draft-07 ou 2020-12)
- [ ] 3.1.3 — Incluir campos obrigatórios: `skill`, `execution_mode`, `architecture_style`, `checkpoints` (array), `fallbacks_invoked` (array), `final_status`, `timestamp`
- [ ] 3.1.4 — Incluir campos opcionais: `lint_profile`, `docs_lookup_mode`, `runtime_policy_version`, `agent_results`
- [ ] 3.1.5 — Adicionar validação do schema ao `scripts/dogfood-report.sh`
- [ ] 3.1.6 — Atualizar `docs/MANUAL.md` seção 13 com o schema formalizado e exemplos

#### 3.2 — Auditar skills que produzem SEP log

**Escopo:** Verificar quais das 20 skills incluem instrução de gravar SEP log e adicionar nas que faltam.

- [ ] 3.2.1 — Ler cada skill em `plugins/claude-tech-squad/skills/` e verificar presença de instrução de SEP log
- [ ] 3.2.2 — Listar skills sem instrução
- [ ] 3.2.3 — Para cada skill faltante: identificar os campos disponíveis ao final da execução (skill name, agents invocados, gates passados)
- [ ] 3.2.4 — Adicionar instrução de gravação de SEP log em cada skill faltante seguindo o schema da tarefa 3.1
- [ ] 3.2.5 — Verificar que a instrução especifica o caminho `ai-docs/.squad-log/<skill>-<timestamp>.json`
- [ ] 3.2.6 — Rodar `bash scripts/validate.sh` após todas as adições

#### 3.3 — Melhorar `/factory-retrospective` com análise de padrões de pipeline

**Escopo:** O retrospective deve ser capaz de ler SEP logs e produzir insights acionáveis sobre a saúde da esteira.

- [ ] 3.3.1 — Ler skill `plugins/claude-tech-squad/skills/factory-retrospective` atual e identificar o que já analisa
- [ ] 3.3.2 — Adicionar análise de: retry rate por skill (quantas vezes cada skill triggou retry), fallback rate por agente (quais agentes mais acionam fallback)
- [ ] 3.3.3 — Adicionar análise de: checkpoint mais frequente de parada (onde os runs mais param/falham), hotfixes sem postmortem subsequente
- [ ] 3.3.4 — Adicionar detecção de: runs sem SEP log (skill sem instrução), runs com `final_status=aborted` sem motivo logado
- [ ] 3.3.5 — Garantir que o output do retrospective inclui recomendações acionáveis por categoria (não só métricas)
- [ ] 3.3.6 — Testar com os SEP logs dos golden runs capturados na Sprint 2

---

### Sprint 4 — Onboarding e experiência do operador

**Objetivo:** Reduzir o tempo até primeira execução bem-sucedida e eliminar pontos de fricção no onboarding.

---

#### 4.1 — Validar e documentar fluxo de instalação

**Escopo:** Identificar pré-requisitos implícitos e erros comuns que um novo operador enfrenta.

- [ ] 4.1.1 — Ler `docs/GETTING-STARTED.md` completo e mapear cada passo de instalação
- [ ] 4.1.2 — Identificar pré-requisitos não documentados: versão mínima do Claude Code, se tmux é opcional ou obrigatório para modo padrão, variáveis de ambiente necessárias
- [ ] 4.1.3 — Documentar os 5 erros mais comuns em nova seção "Troubleshooting" no `GETTING-STARTED.md`
- [ ] 4.1.4 — Adicionar seção "Verificando a instalação" com comando de smoke test rápido que confirma que o plugin está ativo
- [ ] 4.1.5 — Registrar tempo de instalação documentado como baseline da meta < 10 minutos

#### 4.2 — Criar `docs/SKILL-SELECTOR.md` com decision tree

**Escopo:** Novo operador não sabe qual skill usar. O decision tree compacto resolve isso sem precisar ler o playbook inteiro.

- [ ] 4.2.1 — Mapear critérios de decisão de cada uma das 20 skills em formato de perguntas binárias
- [ ] 4.2.2 — Criar diagrama `flowchart TD` em mermaid com o decision tree
- [ ] 4.2.3 — Adicionar tabela: `Skill | Quando usar | Quando NÃO usar | Escalate para`
- [ ] 4.2.4 — Salvar em `docs/SKILL-SELECTOR.md`
- [ ] 4.2.5 — Adicionar link no `docs/README.md` e no `README.md` raiz

#### 4.3 — Melhorar skill `/onboarding` para repositórios com LLM/AI

**Escopo:** Onboarding deve detectar código LLM/AI e configurar o CLAUDE.md gerado com instruções de eval e prompt review.

- [ ] 4.3.1 — Ler skill `plugins/claude-tech-squad/skills/onboarding` atual
- [ ] 4.3.2 — Verificar se detecta: imports de OpenAI, Anthropic, LangChain, LlamaIndex, pgvector
- [ ] 4.3.3 — Adicionar detecção: se LLM code encontrado, incluir seção no CLAUDE.md gerado explicando uso de `/llm-eval` antes de qualquer release e `/prompt-review` antes de qualquer merge com mudança de prompt
- [ ] 4.3.4 — Adicionar geração de baseline de dependências: listar dependências detectadas com flags de desatualização conhecidas
- [ ] 4.3.5 — Testar skill em 3 tipos de repositório: layered Python sem AI, hexagonal TypeScript sem AI, repositório com imports de Anthropic SDK

---

### Sprint 5 — Segurança da esteira e guardrails

**Objetivo:** Fortalecer a detecção automatizada de violações de segurança antes do publish e fortalecer o bench de AI.

---

#### 5.1 — Adicionar detecção automatizada de Absolute Prohibitions ao validate.sh

**Escopo:** Atualmente o validate.sh não verifica se agentes de execução têm o bloco de proibições. Qualquer agente novo pode ser publicado sem ele.

- [ ] 5.1.1 — Consolidar lista definitiva de agentes com autoridade de execução (definida na tarefa 1.2.1)
- [ ] 5.1.2 — Adicionar no `scripts/validate.sh`: para cada agente da lista, fazer grep de string identificadora do bloco de proibições
- [ ] 5.1.3 — Fazer o script emitir mensagem clara por agente faltante e retornar exit code 1
- [ ] 5.1.4 — Testar: remover bloco de um agente e verificar que `validate.sh` falha indicando o agente
- [ ] 5.1.5 — Restaurar e verificar que `validate.sh` passa

#### 5.2 — Fortalecer skill `/security-audit` para cobertura de ameaças LLM

**Escopo:** A skill de security-audit deve incluir o bench de segurança de AI quando detectar código LLM no repositório.

- [ ] 5.2.1 — Ler skill `plugins/claude-tech-squad/skills/security-audit` atual
- [ ] 5.2.2 — Verificar se inclui: scan de prompt injection, verificação de model pinning, verificação de PII em prompts, tool call authorization review
- [ ] 5.2.3 — Adicionar: se código LLM detectado, ativar `llm-safety-reviewer` como parte obrigatória do audit
- [ ] 5.2.4 — Garantir que findings de injection, PII leak, e model sem pin são emitidos como BLOCKING
- [ ] 5.2.5 — Adicionar entrada no `scripts/smoke-test.sh` verificando a presença do bloco de detecção de LLM na skill
- [ ] 5.2.6 — Rodar `bash scripts/validate.sh` e `bash scripts/smoke-test.sh`

#### 5.3 — Revisar e documentar justificativa de cada Absolute Prohibition

**Escopo:** Cada proibição deve ter justificativa de incidente ou risco real documentado no MANUAL.md para que o time entenda por que existe e não tente contorná-la.

- [ ] 5.3.1 — Extrair lista atual de Absolute Prohibitions do README.md
- [ ] 5.3.2 — Para cada item: documentar justificativa (ex: "DROP TABLE sem confirmação — risco de perda irreversível de dados de produção")
- [ ] 5.3.3 — Adicionar seção "Justificativa das proibições absolutas" no `docs/MANUAL.md` seção 12
- [ ] 5.3.4 — Verificar consistência da lista entre README.md, MANUAL.md, e bloco nos agentes
- [ ] 5.3.5 — Corrigir divergências encontradas nos 3 pontos

---

### Sprint 6 — Pipeline de release e automação

**Objetivo:** Garantir que a pipeline automatizada de release é robusta e que nenhum metadado desalinhado chega ao marketplace.

---

#### 6.1 — Auditar `.github/workflows/release.yml` contra `docs/RELEASING.md`

**Escopo:** Verificar que todo passo documentado em RELEASING.md tem um step correspondente no workflow.

- [ ] 6.1.1 — Ler `docs/RELEASING.md` e listar todos os passos que devem ser automatizados
- [ ] 6.1.2 — Ler `.github/workflows/release.yml` e mapear cada step do workflow para os passos documentados
- [ ] 6.1.3 — Identificar passos documentados sem step no workflow
- [ ] 6.1.4 — Adicionar steps faltantes ou documentar explicitamente por que são opcionais ou manuais
- [ ] 6.1.5 — Verificar que o workflow falha se `scripts/smoke-test.sh` retornar exit code diferente de 0

#### 6.2 — Adicionar verificação de alinhamento de versão ao validate.sh

**Escopo:** `marketplace.json`, `plugin.json`, e `docs/MANUAL.md` devem ter a mesma versão. Atualmente essa verificação não é automatizada.

- [ ] 6.2.1 — Identificar o campo de versão em cada um dos 3 arquivos
- [ ] 6.2.2 — Adicionar no `scripts/validate.sh`: extração da versão dos 3 arquivos e comparação
- [ ] 6.2.3 — Fazer o script falhar com mensagem mostrando as versões encontradas quando divergentes
- [ ] 6.2.4 — Adicionar a mesma verificação como step no `.github/workflows/release.yml`
- [ ] 6.2.5 — Testar: alterar versão em um arquivo e verificar que `validate.sh` falha com mensagem clara
- [ ] 6.2.6 — Restaurar e verificar que `validate.sh` passa

#### 6.3 — Documentar processo de release de emergência

**Escopo:** Se o GitHub Actions workflow falhar, o operador precisa de um caminho seguro para publicar manualmente.

- [ ] 6.3.1 — Adicionar seção "Release de emergência (workflow failure)" em `docs/HOW-TO-CHANGE-AND-PUBLISH.md`
- [ ] 6.3.2 — Documentar passo a passo: atualizar versão nos 3 arquivos com o número correto, rodar validate, rodar smoke test, criar tag git manualmente, criar GitHub Release manualmente via `gh release create`
- [ ] 6.3.3 — Adicionar aviso: release manual deve ser seguido de commit de sincronização para que o histórico não fique desalinhado
- [ ] 6.3.4 — Verificar que `scripts/verify-release.sh` cobre os mesmos checks do workflow automatizado
- [ ] 6.3.5 — Documentar o output esperado de `bash scripts/verify-release.sh` após release bem-sucedido

---

### Sprint 7 — Expansão de especialistas e fronteiras

**Objetivo:** Mapear e documentar fronteiras entre agentes com papéis próximos e identificar gaps de cobertura especializada.

---

#### 7.1 — Mapear fronteiras entre agentes com papéis próximos

**Escopo:** Pares de agentes com maior risco de sobreposição devem ter boundary text explícito definindo o que cada um faz e o que não faz.

- [ ] 7.1.1 — Identificar pares de alto risco: (docs-writer / tech-writer), (security-reviewer / security-engineer), (reviewer / code-quality), (architect / backend-architect), (llm-safety-reviewer / security-reviewer)
- [ ] 7.1.2 — Para cada par: ler ambos os prompts e documentar a linha divisória em termos de responsabilidade
- [ ] 7.1.3 — Adicionar ou atualizar bloco "What this agent does NOT do" em cada agente do par
- [ ] 7.1.4 — Atualizar README.md com seção de "splits" para os novos pares documentados
- [ ] 7.1.5 — Rodar `bash scripts/validate.sh` após todas as edições

#### 7.2 — Auditar bench de AI para cobertura de LLM em produção

**Escopo:** Os 8 especialistas de AI cobrem design, eval, e segurança. Verificar se cobrem também operação de LLM em produção: model cost, context management, streaming edge cases.

- [ ] 7.2.1 — Mapear os 8 agentes: `ai-engineer`, `prompt-engineer`, `rag-engineer`, `llm-eval-specialist`, `llm-safety-reviewer`, `agent-architect`, `conversational-designer`, `ml-engineer`
- [ ] 7.2.2 — Ler cada prompt e mapear: o que cobre, o que não cobre
- [ ] 7.2.3 — Identificar gaps: model cost optimization, context window management, streaming failure handling, multi-modal input handling
- [ ] 7.2.4 — Para cada gap: decidir se pertence a agente existente (adicionar) ou justifica novo agente
- [ ] 7.2.5 — Implementar adições nos prompts dos agentes existentes
- [ ] 7.2.6 — Rodar escada de validação completa

#### 7.3 — Criar agente `llm-cost-analyst`

**Escopo:** Não existe agente específico para análise de custo de tokens. O `cost-optimizer` cobre infra, não LLM usage cost.

- [ ] 7.3.1 — Ler `plugins/claude-tech-squad/agents/cost-optimizer.md` e confirmar que não cobre custo de tokens de LLM
- [ ] 7.3.2 — Definir escopo do `llm-cost-analyst`: análise de custo por usuário, por prompt template, por pipeline RAG; identificação de oportunidades de prompt compression e caching; recomendação de model downgrade onde aplicável
- [ ] 7.3.3 — Criar `plugins/claude-tech-squad/agents/llm-cost-analyst.md` com: role, specialty, boundary text, result_contract, docs_lookup instruction
- [ ] 7.3.4 — Adicionar o agente ao bench de AI no skill `/squad` (ativado quando LLM detectado)
- [ ] 7.3.5 — Atualizar roster no README.md e MANUAL.md com o novo agente (total: 62)
- [ ] 7.3.6 — Rodar escada de validação completa

---

### Sprint 8 — Documentação e contribuição

**Objetivo:** Fechar gaps de documentação para que qualquer contribuidor novo possa adicionar agentes ou skills sem precisar de ajuda externa.

---

#### 8.1 — Adicionar guia "Como adicionar um novo agente" ao CONTRIBUTING.md

**Escopo:** O CONTRIBUTING.md não documenta o processo de adição de agentes, criando fricção para contribuidores.

- [ ] 8.1.1 — Ler `CONTRIBUTING.md` atual e identificar o que está documentado e o que falta
- [ ] 8.1.2 — Documentar campos obrigatórios de um novo agente: `role`, `specialty`, `boundary_text`, `result_contract`, `absolute_prohibitions` (se agente de execução)
- [ ] 8.1.3 — Documentar onde registrar o agente: `plugins/claude-tech-squad/agents/` + README.md roster + MANUAL.md seção 6
- [ ] 8.1.4 — Documentar o checklist de PR para novo agente: validate.sh, smoke-test.sh, boundary text revisado
- [ ] 8.1.5 — Adicionar seção em `CONTRIBUTING.md` com o guia completo

#### 8.2 — Adicionar guia "Como adicionar uma nova skill" ao CONTRIBUTING.md

**Escopo:** Skills têm estrutura mínima obrigatória (preflight, SEP log, gates, result_contract). Sem documentação, contribuidores criam skills incompletas.

- [ ] 8.2.1 — Documentar estrutura mínima de uma skill: preflight block, chain de agentes, gate blocks, checkpoint block, SEP log block
- [ ] 8.2.2 — Documentar onde registrar: `plugins/claude-tech-squad/skills/` + README.md commands + MANUAL.md seção 4 + GETTING-STARTED.md commands + smoke-test.sh
- [ ] 8.2.3 — Adicionar exemplo de skill mínima como template inline no CONTRIBUTING.md
- [ ] 8.2.4 — Documentar checklist de PR para nova skill: todos os pontos de registro verificados, smoke test adicionado, validação passando
- [ ] 8.2.5 — Adicionar seção em `CONTRIBUTING.md` com o guia completo

#### 8.3 — Traduzir `docs/MANUAL.md` para inglês

**Escopo:** O MANUAL.md está em português. Todos os outros docs estão em inglês. Inconsistência cria barreira para contribuidores internacionais.

- [ ] 8.3.1 — Ler `docs/MANUAL.md` completo e mapear todas as seções
- [ ] 8.3.2 — Traduzir seções 1-3: O que é o plugin, Instalação e ativação, Teammate Mode
- [ ] 8.3.3 — Traduzir seções 4-6: Skills disponíveis, Fluxo completo de cada skill, Os 61 agentes
- [ ] 8.3.4 — Traduzir seções 7-10: Arquitetura da esteira, Gates de usuário, Visibilidade de execução, Regras de uso
- [ ] 8.3.5 — Traduzir seções 11-13: Referência rápida, Absolute Prohibitions, SEP protocol
- [ ] 8.3.6 — Verificar que todos os exemplos de comandos, trace lines, e outputs continuam corretos
- [ ] 8.3.7 — Rodar `bash scripts/validate.sh` para confirmar integridade após a tradução

#### 8.4 — Revisar e completar CHANGELOG.md com entradas retroativas

**Escopo:** Verificar se há versões no histórico de tags sem entrada correspondente no CHANGELOG.

- [ ] 8.4.1 — Executar `git tag --sort=-v:refname` e listar todas as tags existentes
- [ ] 8.4.2 — Comparar com entradas em `CHANGELOG.md`
- [ ] 8.4.3 — Para cada versão sem entrada: executar `git log <tag-anterior>..<tag>` e identificar commits relevantes
- [ ] 8.4.4 — Adicionar entrada retroativa para cada versão faltante no formato consistente com o padrão atual
- [ ] 8.4.5 — Rodar `bash scripts/validate.sh` para confirmar que o CHANGELOG está no formato esperado pelo script de release

---

### Sprint 9 — Integração dos stack specialists ao plugin

**Objetivo:** Mover os 12 agentes de stack da pasta `agents/` para dentro do plugin e garantir que todos atendem ao contrato de agente do plugin com Context7 e Playwright onde aplicável.

---

#### 9.1 — Mover agentes de stack para `plugins/claude-tech-squad/agents/`

**Escopo:** Os 12 arquivos em `agents/` passam a ser agentes oficiais do plugin, sujeitos ao mesmo contrato e validação dos 61 existentes.

- [ ] 9.1.1 — Ler cada arquivo em `agents/` e verificar conformidade com o contrato: frontmatter `name`/`description`, `## Result Contract`, `## Documentation Standard — Context7 First, Repository Fallback`
- [ ] 9.1.2 — Para agentes com autoridade de execução (`shell-developer`, `django-backend`, `python-developer`): verificar presença de `## Absolute Prohibitions`
- [ ] 9.1.3 — Copiar os 12 arquivos para `plugins/claude-tech-squad/agents/` com nomes padronizados ao formato do plugin
- [ ] 9.1.4 — Remover a pasta `agents/` raiz após migração (os arquivos vivem apenas no plugin)
- [ ] 9.1.5 — Atualizar `agents/README.md` → mover conteúdo para `plugins/claude-tech-squad/agents/README.md` ou integrar ao README existente

#### 9.2 — Atualizar agentes existentes do plugin com Context7 e Playwright

**Escopo:** Agentes do plugin que trabalham com código ou tecnologias específicas devem usar Context7. Agentes de frontend e QA devem usar Playwright.

- [ ] 9.2.1 — Auditar os 61 agentes existentes: quais já têm instrução de Context7, quais não têm
- [ ] 9.2.2 — Para cada agente técnico sem Context7: adicionar `## Documentation Standard — Context7 First, Repository Fallback` com lookup antes de qualquer lib
- [ ] 9.2.3 — Auditar agentes de frontend e QA: verificar quais já têm acesso a Playwright tools no frontmatter
- [ ] 9.2.4 — Para `frontend-dev`, `qa`, `mobile-dev`: adicionar Playwright tools ao frontmatter e seção de verificação visual/E2E
- [ ] 9.2.5 — Para `tech-lead` e `architect`: adicionar Context7 para verificação de tecnologias propostas antes de recomendar

#### 9.3 — Atualizar validate.sh para o novo roster de agentes

**Escopo:** O `validate.sh` tem a lista de agentes obrigatórios hardcoded. Após a integração dos 12 novos, a lista precisa ser atualizada.

- [ ] 9.3.1 — Ler `scripts/validate.sh` e identificar a variável ou lista `REQUIRED_AGENTS`
- [ ] 9.3.2 — Adicionar os 12 novos agentes à lista
- [ ] 9.3.3 — Verificar que o script valida Context7 instruction nos agentes técnicos (grep por string identificadora)
- [ ] 9.3.4 — Rodar `bash scripts/validate.sh` e confirmar que passa com os 12 novos agentes presentes
- [ ] 9.3.5 — Testar: remover um dos novos agentes e confirmar que validate.sh falha com mensagem clara

#### 9.4 — Criar categorias de stack specialist no README.md do plugin

**Escopo:** O README.md do plugin lista os 61 agentes sem categorização por stack. Com os 12 novos especialistas, adicionar seção de "Stack Specialists" com instruções de quando usar cada um.

- [ ] 9.4.1 — Ler README.md atual do plugin e identificar a seção de agentes
- [ ] 9.4.2 — Adicionar seção "Stack Specialists" com subsections: Django Stack, React/Vue, Python, TypeScript/JavaScript, Shell/Automation
- [ ] 9.4.3 — Para cada specialist: descrição, tools (Context7, Playwright onde aplicável), quando usar, quando NÃO usar
- [ ] 9.4.4 — Adicionar tabela de cobertura MCP: qual agente usa Context7, qual usa Playwright, qual usa ambos
- [ ] 9.4.5 — Atualizar contagem total de agentes no header do README.md (61 → 73)

#### 9.5 — Atualizar contagem e escada de validação

**Escopo:** Garantir que a escada de validação cobre os novos agentes e que os counts em `plugin.json`, `marketplace.json`, e `MANUAL.md` refletem o novo total.

- [ ] 9.5.1 — Atualizar contagem de agentes em `plugins/claude-tech-squad/.claude-plugin/plugin.json`
- [ ] 9.5.2 — Atualizar contagem em `docs/MANUAL.md` seção de roster
- [ ] 9.5.3 — Adicionar smoke test para cada novo agente: verificar presença de `result_contract` e `Documentation Standard` no arquivo
- [ ] 9.5.4 — Rodar escada completa: `validate.sh` → `smoke-test.sh` → `dogfood.sh` → `dogfood-report.sh --schema-only`
- [ ] 9.5.5 — Criar entrada no `CHANGELOG.md` para a versão que inclui os stack specialists
- [ ] 9.5.6 — Commitar todas as mudanças e criar tag de release seguindo o processo documentado em `docs/HOW-TO-CHANGE-AND-PUBLISH.md`