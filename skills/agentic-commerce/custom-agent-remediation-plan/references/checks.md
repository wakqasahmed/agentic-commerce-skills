# Custom-agent remediation plan checks

Set `$PLAN` to a local JSON file containing proposed remediation items. Each item must include `id`, `bucket`, `owner`, `acceptance_test`, `evidence_source`, `operation_mode`, and `risk_level`.

## Validate plan completeness

```bash
jq -e 'type == "array" and length > 0' "$PLAN"
jq -e 'all(.[]; (.id | type == "string" and length > 0) and (.bucket | IN("content"; "product_knowledge"; "crawler_access"; "policy"; "integration"; "workflow")) and (.owner | type == "string" and length > 0) and (.acceptance_test | type == "string" and length > 0) and (.evidence_source | type == "string" and length > 0) and (.operation_mode | IN("action_capable"; "read_only")) and (.risk_level | IN("low"; "moderate"; "high")))' "$PLAN"
```

An item without an accountable owner, evidence source, or observable acceptance test is incomplete.

## Separate storefront work from agent work

```bash
jq -r '.[] | [.id, .bucket, .owner, .acceptance_test] | @tsv' "$PLAN"
jq -e 'all(.[]; has("delivery") and (.delivery | IN("storefront"; "agent"; "shared")))' "$PLAN"
```

Add `delivery` before using the second command. Policy, catalog, and crawler-rule changes need storefront delivery; an agent may not compensate for an unknown source of truth.

## Verify readiness lift

```bash
jq -e 'all(.[]; has("baseline_check") and has("post_change_check"))' "$PLAN"
jq -r '.[] | select(.baseline_check == null or .post_change_check == null) | .id' "$PLAN"
```

Each item needs a reproducible before/after check using source audit output as baseline evidence, not an unverified score claim.

## Gate action-capable and high-risk work

```bash
jq -e 'all(.[]; if (.operation_mode == "action_capable" or .risk_level == "high") then ([.operational_controls.trace_or_correlation_ids, .operational_controls.authorization_evidence, .operational_controls.audit_events, .operational_controls.idempotency_or_deduplication, .operational_controls.reconciliation_checks, .operational_controls.retained_failure_evidence, .operational_controls.health_signals, .operational_controls.alert_thresholds, .operational_controls.accountable_operator, .operational_controls.human_escalation_path, .operational_controls.disable_or_kill_switch, .operational_controls.rollback_or_recovery_procedure, .operational_controls.safe_dependency_fallback, .operational_controls.approval_workflow, .operational_controls.policy_grounding] | all(.[]; type == "string" and length > 0)) else true end)' "$PLAN"
```

Then reject placeholders and uncheckable operational promises:

```bash
jq -e '
  def substantive:
    type == "string" and length > 0 and
    ((ascii_downcase | sub("[.!]$"; "")) as $value |
      ["tbd", "todo", "pending", "unknown", "n/a", "na", "none", "later", "not applicable", "to be determined"] |
      index($value) | not) and
    (test("\\b(tbd|todo|not applicable|to be determined)\\b|(^|[^[:alnum:]_])n/a([^[:alnum:]_]|$)|\\b(pending|unknown|none|later)[.!]?[[:space:]]*$"; "i") | not) and
    (test("\\b(add|define|document|establish|implement|specify|set up)\\b.{0,100}\\b(eventually|future|later|pending|tbd|to be determined)\\b"; "i") | not);
  def checkable($pattern): substantive and test($pattern; "i");
  all(.[];
    if (.operation_mode == "action_capable" or .risk_level == "high") then
      (.operational_controls.trace_or_correlation_ids | checkable("\\b(correlation|trace) +(id|identifier|key)s?\\b")) and
      (.operational_controls.authorization_evidence | checkable("\\b(retain|record|store)\\w*\\b.*\\b(actor|decision|evidence|identity|permission)\\w*\\b")) and
      (.operational_controls.audit_events | checkable("\\b(audit|emit|event|log)\\w*\\b.*\\b(action|actor|approved|completed|outcome|requested|submitted|timestamp|write)\\w*\\b")) and
      (.operational_controls.idempotency_or_deduplication | checkable("\\b(deduplicat|duplicate|idempoten|reject|reuse)\\w*\\b.*\\b(duplicate|id|key|reject|reuse)\\w*\\b")) and
      (.operational_controls.reconciliation_checks | checkable("\\b(compare|match|reconcile|verify)\\w*\\b.*\\b(after|before|daily|every|hour|minute|scheduled|weekly)\\b")) and
      (.operational_controls.retained_failure_evidence | checkable("\\b(archive|retain|store)\\w*\\b.*\\b(error|evidence|fail|request|response)\\w*\\b.*\\b[0-9]+ *(days?|hours?|months?|weeks?)\\b")) and
      (.operational_controls.health_signals | checkable("\\b(count|duration|error|failure|lag|latency|rate|success|volume)\\b")) and
      (.operational_controls.alert_thresholds | checkable("\\b(above|at least|below|exceed|fewer than|greater than|less than|more than|over|under)\\b.{0,40}[0-9]+(\\.[0-9]+)? *(%|ms|seconds?|minutes?|hours?|days?|requests?|orders?|events?)")) and
      (.operational_controls.accountable_operator | checkable("\\b(engineer|lead|manager|on-call|operations|operator|owner|support|security)\\b")) and
      (.operational_controls.human_escalation_path | checkable("\\b(escalate|handoff|route)\\w*\\b.*\\b(commander|engineer|incident|lead|manager|on-call|operations|operator|queue|security|support)\\b")) and
      (.operational_controls.disable_or_kill_switch | checkable("\\b(block|disable|pause|stop)\\w*\\b.*\\b(action|connector|order|payment|submission|write)\\w*\\b")) and
      (.operational_controls.rollback_or_recovery_procedure | checkable("\\b(recover|replay|restore|retry|roll back)\\w*\\b.*\\b(connector|event|intent|order|release|request|state|version|write)\\w*\\b")) and
      (.operational_controls.safe_dependency_fallback | checkable("\\b(defer|manual|preserve|queue|read-only|route|stop)\\w*\\b.*\\b(checkout|customer|intent|operator|request|support|write)\\w*\\b")) and
      (.operational_controls.approval_workflow | checkable("\\b(approv|authoriz|require)\\w*\\b.*\\b(before|prior|review|submission|submit)\\w*\\b")) and
      (.operational_controls.policy_grounding | checkable("\\b(approved|canonical|versioned)\\b.*\\b(policy|policies|rule|rules)\\b"))
    else true end
  )' "$PLAN"
```

If either command fails, return `HOLD` and list each missing control. Do not substitute a general monitoring or rollback promise for checkable evidence. Low- and moderate-risk read-only content or discovery items do not need these action controls.
