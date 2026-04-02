# How To Change And Publish

Este é o fluxo operacional padrão para mudar e publicar o `claude-tech-squad` sem mexer manualmente nos metadados de release.

## Regra Principal

Você altera código, prompts, skills, agentes e docs normalmente.

Você **não** edita manualmente estes arquivos para uma release rotineira:

- `CHANGELOG.md`
- `.claude-plugin/marketplace.json`
- `plugins/claude-tech-squad/.claude-plugin/plugin.json`
- `docs/MANUAL.md`

Esses arquivos são gerados pela pipeline de publish.

## Fluxo Padrão

### 1. Crie uma branch

Exemplos:

```bash
git switch -c feat/nova-skill
git switch -c fix/retry-reviewer
```

### 2. Faça a mudança

Edite o que precisar:

- agentes
- skills
- workflows
- scripts
- fixtures
- documentação visível ao operador

Atualize `README.md` quando a mudança alterar a forma de usar ou operar o plugin.

### 3. Valide localmente

```bash
bash scripts/validate.sh
bash scripts/smoke-test.sh
```

Se a mudança for sensível em workflow, orquestração ou release, rode também:

```bash
bash scripts/dogfood.sh
bash scripts/dogfood-report.sh --schema-only
```

### 4. Faça commit em formato convencional

A release automática depende disso.

Use:

- `feat: ...` para release `minor`
- `fix: ...` para release `patch`
- `docs: ...` para release `patch`
- `refactor: ...` para release `patch`
- `chore: ...` para release `patch`
- `type!: ...` ou `BREAKING CHANGE` para release `major`

Exemplos:

```bash
git add .
git commit -m "feat: automate release metadata generation"
git commit -m "fix: harden publish workflow resume behavior"
git commit -m "docs: clarify teammate mode release flow"
```

### 5. Envie a branch e abra o PR

Se você usa squash merge, o título final do PR também precisa estar em formato convencional, porque ele vira o commit que cai em `main`.

### 6. Espere o CI passar

O workflow `validate` roda automaticamente.

### 7. Faça merge em `main`

Depois disso, o restante é automático.

## O Que Acontece Depois Do Merge

O workflow `publish`:

1. Lê os commits desde a última tag
2. Calcula a próxima versão semver
3. Gera a nova entrada do `CHANGELOG.md`
4. Atualiza `marketplace.json`
5. Atualiza `plugin.json`
6. Atualiza `docs/MANUAL.md`
7. Roda `bash scripts/smoke-test.sh`
8. Faz o commit `chore: prepare release vX.Y.Z`
9. Cria a tag `vX.Y.Z`
10. Cria ou atualiza a GitHub Release

## O Que Verificar

Depois do merge, confira:

- GitHub Actions: workflow `publish`
- GitHub Releases: nova release criada
- tag nova publicada
- `CHANGELOG.md` com a entrada da versão
- `marketplace.json`, `plugin.json` e `MANUAL.md` alinhados

## Fluxo Curto

```bash
git switch -c feat/minha-mudanca
# faz a mudança
bash scripts/validate.sh
bash scripts/smoke-test.sh
git add .
git commit -m "feat: minha mudança"
git push
# abre PR
# merge em main
# publish automático
```

## Fluxo de Emergência

Se a automação externa falhar e você realmente precisar acionar o fallback local:

```bash
./scripts/release.sh
```

Esse script usa o mesmo gerador de metadados da pipeline oficial e dispara o workflow `publish`.
