---
name: iac-review
description: This skill should be used when Infrastructure as Code changes need review before apply, including static analysis, blast radius, security posture, cost impact, and safe sequencing with rollback. Trigger with "revisar infraestrutura", "iac review", "checar terraform", "revisar cloudformation", "antes do terraform apply", "infra review", "revisar helm chart". NOT for application-runtime incident debugging (use /cloud-debug).
user-invocable: true
---

# /iac-review — Infrastructure as Code Change Review

Reviews IaC changes before `terraform apply`, `helm upgrade`, or equivalent. Prevents the most dangerous class of production accidents: infrastructure changes that are hard to reverse, affect shared resources, or silently alter security posture.

**Core principle:** Infrastructure changes are not reversible like code changes. A dropped database or misconfigured security group can cost hours of recovery. Review before apply — always.

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Recommend running `terraform apply`, `pulumi up`, `helm upgrade`, or equivalent against production without staging verification first
- Recommend `terraform destroy` or any resource deletion command in production without explicit user confirmation and verified backup
- Suggest removing security groups, firewall rules, or IAM policies without confirming equivalent replacements are in place
- Recommend force-replacing stateful resources (databases, volumes, caches) that would cause data loss
- Generate or store cloud credentials, API keys, or secrets in IaC outputs or state files
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

## When to Use

- Before any `terraform apply`, `pulumi up`, `cdk deploy`, `helm upgrade`, or `ansible-playbook`
- When reviewing a PR that touches IaC files
- Before a production infrastructure change
- When the user says: "revisar infraestrutura", "iac review", "checar terraform", "revisar cloudformation", "antes do terraform apply", "infra review", "revisar helm chart"

## Operator Visibility Contract

Emit these trace lines so the operator can follow the IaC review and the SEP log can capture state transitions:

- `[Preflight Start] iac-review`
- `[IaC Stack Detected] tools=<list> | files=<count>`
- `[Static Analysis] tool=<name> | findings=<count>` (per scanner)
- `[Team Created] iac-review-team`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Gate] Teammate Failure | <name> failed twice` (when applicable)
- `[Blast Radius] scope=<production|staging|dev> | resources=<count>`
- `[Apply Approval Gate] verdict=<approve|block|conditional>` (mandatory before apply)
- `[Team Deleted] iac-review-team | cleanup complete` (or `[Team Cleanup Warning]` on failure)
- `[SEP Log Written] ai-docs/.squad-log/<filename>`

## Checkpoint / Resume Rules

Long apply-plan reviews on large repos benefit from checkpoint tracking. Checkpoints recorded in the SEP log:

- `iac-stack-detected` — Terraform/CFN/CDK/Pulumi/Helm/Ansible toolset locked
- `static-analysis-complete` — tflint/checkov/cfn-lint/kubescape findings collected
- `blast-radius-assessed` — production vs staging vs dev scope determined
- `specialists-reviewed` — devops + cloud-architect + cost-optimizer outputs collected
- `apply-approval-recorded` — final operator verdict captured (approve/block/conditional)

**Resume rule:** if restarted, read the highest completed checkpoint from the SEP log. If `static-analysis-complete` is set, skip rerunning scanners unless the IaC files have changed since the checkpoint timestamp. Always re-validate the apply-approval gate even on resume — operator approval is not cacheable.

## Execution

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role.

**For every teammate spawned — without exception:**

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - Emit: `[Teammate Retry] <name> | Reason: silent failure — re-spawning`
   - Re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails:
   - Emit: `[Gate] Teammate Failure | <name> failed twice`
   - Surface to the user:

```
Teammate <name> failed to return a valid output (attempt 1 and 2).

Options:
- [R] Retry once more with the same prompt
- [S] Skip and continue — downstream quality WILL be degraded (log the risk)
- [X] Abort the run
```

4. **Sequential teammates** (output feeds the next agent): [S] degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: [S] on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. **Do NOT advance to the next step** until every teammate in the current step has returned valid output, been explicitly skipped, or the run has been aborted.

### Step 1 — Detect IaC stack and scope

```bash
# Terraform
find . -name "*.tf" -o -name "*.tfvars" 2>/dev/null | grep -v ".terraform/" | head -20

# Pulumi
ls Pulumi.yaml Pulumi.*.yaml 2>/dev/null || echo "NO_PULUMI"

# CloudFormation
find . -name "*.template" -o -name "template.yaml" -o -name "template.json" 2>/dev/null | head -10

# AWS CDK
ls cdk.json cdk.context.json 2>/dev/null || echo "NO_CDK"

# Helm
find . -name "Chart.yaml" 2>/dev/null | head -5

# Ansible
find . -name "playbook*.yml" -o -name "site.yml" -o -name "*.playbook.yml" 2>/dev/null | head -5

# Kubernetes raw manifests
find . -name "*.yaml" -path "*/k8s/*" -o -name "*.yaml" -path "*/kubernetes/*" 2>/dev/null | head -10
```

Record detected stack. If multiple tools: process each independently.

### Step 2 — Get the changeset

**For Terraform:**
```bash
# Show planned changes (dry run)
terraform plan -out=tfplan 2>/dev/null && terraform show -json tfplan 2>/dev/null || \
terraform plan 2>/dev/null || echo "TERRAFORM_PLAN_NOT_AVAILABLE"
```

**For Helm:**
```bash
helm diff upgrade {{release}} {{chart}} --values {{values_file}} 2>/dev/null || \
helm upgrade --dry-run {{release}} {{chart}} 2>/dev/null || echo "HELM_DIFF_NOT_AVAILABLE"
```

**For CloudFormation:**
```bash
aws cloudformation create-change-set --stack-name {{stack}} --template-body file://template.yaml \
  --change-set-name review-$(date +%s) --no-execute 2>/dev/null || echo "CFN_CHANGESET_NOT_AVAILABLE"
```

**Fallback — git diff of IaC files:**
```bash
git diff HEAD -- "*.tf" "*.yaml" "*.json" "*.template" 2>/dev/null | head -300
git diff --cached -- "*.tf" "*.yaml" "*.json" "*.template" 2>/dev/null | head -300
```

If no changeset is available, ask the user to paste the plan or diff output. This is a soft gate.

### Step 3 — Run static analysis

**Terraform — tfsec / checkov:**
```bash
tfsec . --format json 2>/dev/null || \
checkov -d . --framework terraform --output json 2>/dev/null || \
echo "STATIC_ANALYSIS_NOT_AVAILABLE"
```

**Kubernetes / Helm — kubesec / kube-score:**
```bash
kubesec scan *.yaml 2>/dev/null || \
kube-score score *.yaml 2>/dev/null || \
echo "K8S_ANALYSIS_NOT_AVAILABLE"
```

**General — checkov (multi-framework):**
```bash
checkov -d . --output json 2>/dev/null || echo "CHECKOV_NOT_AVAILABLE"
```

Parse all tool output. Categorize findings: CRITICAL / HIGH / MEDIUM / LOW.

### Step 4 — Spawn devops for blast radius assessment

Use TeamCreate to create a team named "iac-review-team". Then spawn each agent using the Agent tool with `team_name="iac-review-team"` and a descriptive `name` for each agent.

```
Agent(
  subagent_type = "claude-tech-squad:devops",
  team_name = "iac-review-team",
  name = "devops",
  prompt = """
## IaC Change Blast Radius Assessment

### IaC Stack
{{detected_stack}}

### Changeset / Plan
{{changeset_or_diff}}

### Environment
{{target_environment}}

---
You are the DevOps specialist. Assess the blast radius of these infrastructure changes.

1. **Resource inventory** — categorize each changed resource:
   - Type: compute / network / storage / database / IAM / DNS / CDN / messaging
   - Change type: create / modify / replace / destroy
   - Stateful: yes/no (stateful = data loss risk on replace/destroy)
   - Shared: yes/no (shared = multiple services depend on this resource)

2. **Blast radius** — if this apply fails or produces unexpected results:
   - Which services are affected?
   - Is the impact isolated or cascading?
   - Estimated user impact (none / degraded / down)

3. **Force-replace risk** — any resources marked for replacement (taint/replace)?
   - Will replacement cause downtime?
   - Will replacement cause data loss?
   - Is there a safer alternative (modify in-place, blue-green)?

4. **Dependency order** — in what order should resources be created/modified/destroyed?
   - Which resources must exist before others can be created?
   - Which must be destroyed last?

5. **Environment-specific risks** — is this change targeting production directly?
   - Has it been applied to a lower environment (dev/staging) first?
   - Are there environment-specific variables that could behave differently?

Safety: Never recommend `terraform destroy` on production stateful resources without a backup verification step.
Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] devops | pane: devops`

### Step 5 — Spawn cloud-architect for security and IAM review

```
Agent(
  subagent_type = "claude-tech-squad:cloud-architect",
  team_name = "iac-review-team",
  name = "cloud-architect",
  prompt = """
## IaC Security and Architecture Review

### Changeset
{{changeset_or_diff}}

### Static Analysis Findings
{{static_analysis_output}}

### Cloud Provider
{{aws_gcp_azure_or_multi}}

---
You are the Cloud Architect. Review the security posture and architecture quality of these IaC changes.

1. **IAM / permissions** — for any role, policy, or binding changes:
   - Does the new permission follow least-privilege?
   - Are wildcard permissions (`*`) introduced? Flag these as HIGH risk.
   - Are cross-account or cross-project permissions introduced?
   - Are any admin or owner roles being assigned?

2. **Network security** — for any security group, firewall, VPC, or subnet changes:
   - Are any ports opened to 0.0.0.0/0 (internet)?
   - Is any private resource becoming publicly accessible?
   - Are existing security group rules being removed without replacement?

3. **Encryption and data protection**:
   - Are storage resources (S3, GCS, RDS, EBS) encrypted at rest?
   - Are KMS keys or encryption configs being removed?
   - Are any secrets or credentials hardcoded in the IaC?

4. **Architecture compliance**:
   - Does the change follow the project's established patterns (VPC layout, naming, tagging)?
   - Are required tags (environment, owner, cost-center) present on new resources?
   - Is logging and monitoring enabled on new resources?

5. **Well-Architected violations**: flag any that apply:
   - Single point of failure introduced
   - No multi-AZ / multi-region for critical resources
   - Missing backup policy on stateful resources
   - Public endpoint without authentication

Return: APPROVED / ISSUES FOUND / BLOCKED (critical security issue).
Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] cloud-architect | pane: cloud-architect`

### Step 6 — Spawn cost-optimizer for cost impact

```
Agent(
  subagent_type = "claude-tech-squad:cost-optimizer",
  team_name = "iac-review-team",
  name = "cost-optimizer",
  prompt = """
## IaC Cost Impact Analysis

### Changeset
{{changeset_or_diff}}

### Cloud Provider
{{cloud_provider}}

### Current Environment Size (if known)
{{environment_context}}

---
You are the Cost Optimizer. Estimate the cost impact of these infrastructure changes.

1. **New resources being added**: estimate monthly cost for each:
   - Compute (instance type, hours, reserved vs. on-demand)
   - Storage (GB, IOPS, transfer)
   - Managed services (RDS, ElastiCache, MSK — instance class + storage)
   - Network (NAT gateway, load balancer, data transfer)

2. **Resources being modified**: will the change increase or decrease cost?
   - Instance type upgrades/downgrades
   - Storage size increases (usually irreversible)
   - Scaling policy changes

3. **Resources being destroyed**: what cost is being eliminated?

4. **Total monthly delta**: estimated increase / decrease / neutral

5. **Cost risks**: any resource that could generate unexpected cost at scale?
   - Auto-scaling without upper bound
   - Data transfer across regions/AZs
   - On-demand pricing for resources that should be reserved

Return: CLEAR (no significant cost change) or RISK with specific items and estimates.
Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] cost-optimizer | pane: cost-optimizer`

### Step 7 — Consolidate findings and apply sequence

Consolidate all agent outputs. Produce the review report:

```markdown
# IaC Review — {{date}}

## Summary
- IaC stack: {{terraform/helm/cloudformation/cdk/ansible}}
- Environment: {{target}}
- Resources changed: {{N}} (create: N, modify: N, replace: N, destroy: N)
- Static analysis: {{N critical, N high, N medium, N low}}
- Security review: {{APPROVED / ISSUES FOUND / BLOCKED}}
- Cost impact: {{CLEAR / RISK — estimated delta}}
- Overall: GO / NO-GO

## Resource Change Inventory

| Resource | Type | Change | Stateful | Shared | Risk |
|----------|------|--------|----------|--------|------|
| {{resource}} | {{type}} | create/modify/replace/destroy | yes/no | yes/no | low/medium/high |

## Static Analysis Findings

### Critical (blocking)
{{findings}}

### High
{{findings}}

## Security Findings
{{cloud_architect_output}}

## Blast Radius
{{devops_blast_radius}}

## Cost Impact
{{cost_optimizer_output}}

## Safe Apply Sequence

### Step 1 — Pre-apply checklist
- [ ] All changes applied to staging first and verified
- [ ] Backup verified for stateful resources: {{resource_list}}
- [ ] On-call engineer notified (if production)
- [ ] Rollback plan reviewed and understood

### Step 2 — Apply sequence
1. {{first_resource_or_group}} — reason: {{dependency}}
2. {{next_resource_or_group}}
3. ...

### Step 3 — Verification
- [ ] {{verification_step_1}}
- [ ] {{verification_step_2}}

### Step 4 — Rollback plan
1. {{rollback_step_1}} — command: `{{command}}`
2. {{rollback_step_2}}
```

### Step 8 — Gate: Apply approval

Present to user:

```
IaC Review Complete

Stack: {{stack}}
Environment: {{environment}}
Resources: {{N changes}}
Security: {{APPROVED / ISSUES FOUND / BLOCKED}}
Cost delta: {{estimate}}
Overall: GO / NO-GO

Blocking issues:
{{list_or_none}}

Recommended apply sequence:
{{sequence}}

Proceed with apply? [Y/N]
```

**This is a blocking gate.** If there are CRITICAL security findings or blast radius HIGH: halt and require explicit acknowledgment with written reason.

### Step 9 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-iac-review-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: iac-review
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [preflight-passed, scan-complete, findings-reviewed]
fallbacks_invoked: []
iac_stack: terraform | helm | cloudformation | cdk | ansible | k8s
environment: staging | production
resources_changed: N
critical_findings: N
security_result: APPROVED | ISSUES_FOUND | BLOCKED
cost_result: CLEAR | RISK
overall: GO | NO-GO
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Key Findings
{{summary}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 10 — Save report and report to user

Write full report to `ai-docs/iac-review-{{date}}.md`.

Tell the user:
- Overall GO / NO-GO
- Critical security findings (if any) — must fix before apply
- Blast radius summary — highest-risk resources
- Cost impact estimate
- Safe apply sequence
- Path to saved review report
- If NO-GO: specific blockers and what to fix
