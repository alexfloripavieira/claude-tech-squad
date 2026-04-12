# Discovery Blueprint — /cost-estimate skill

## Product Definition (PM)

### Problem
Devs default to /squad for everything, wasting $20+ on trivial tasks. No runtime guardrail exists to recommend the cheapest adequate skill.

### User Stories
1. As a dev, I want a skill recommendation before spending tokens
2. As a team lead, I want visibility into task complexity classification
3. As a cost-conscious operator, I want estimated cost before execution
4. As a new user, I want a single entry point instead of memorizing the decision tree

### Acceptance Criteria
1. Returns recommended_skill + alternatives + complexity_tier
2. Classifies: trivial / small / medium / large
3. Shows estimated agents, tokens, USD range
4. Under 30s, under 50K tokens
5. Zero specialist agents spawned
6. Writes SEP log
7. Passes validate.sh

### Scope
- IN: task analysis, complexity classification, skill recommendation, SEP log
- OUT: auto-invoke, historical analysis, policy changes

## Architecture Decision

### Approach
Zero-agent inline skill (same pattern as /dashboard). Orchestrator executes directly — no TeamCreate, no Agent calls.

### Data Flow
1. Read task description from conversation
2. Read SKILL-SELECTOR.md cost table + Quick Heuristics
3. Extract complexity signals (keywords, scope indicators)
4. Classify tier → map to skill → compute cost estimate
5. Return structured recommendation

### Integration
- Reads: docs/SKILL-SELECTOR.md, runtime-policy.yaml
- Writes: ai-docs/.squad-log/cost-estimate-*.md

### New Files
- plugins/claude-tech-squad/skills/cost-estimate/SKILL.md

### Why Zero-Agent
Alternative (spawn tech-lead for analysis) costs ~50K tokens. Table-lookup by orchestrator costs ~10K. The skill must be cheaper than every skill it recommends.
