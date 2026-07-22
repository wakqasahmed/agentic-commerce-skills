# Trust and order lifecycle checks

Load this reference after the goal is known. Apply only the controls needed for that goal; for example, payment authorization is `not applicable` to a discovery-only audit.

## Separate the principals and decisions

Record evidence for each applicable row independently. Never infer a later row from an earlier one.

| Check | What it establishes | What it does not establish |
|---|---|---|
| Agent identity | The request came from an identified or trusted agent, using signed-agent verification where the protocol provides it. [SRC-TAP] | User identity, delegated authority, or permission to pay |
| User identity | The buyer or account was authenticated to the required assurance level. | Consent to this action or agent authority |
| Delegated authority | A consent record or mandate scopes the agent to the action, resource, amount, merchant, duration, and relevant constraints. [SRC-AP2] | Payment approval or merchant acceptance |
| Payment authorization | The instrument or payment mandate is authorized for the specific checkout and amount. [SRC-AP2] | Product eligibility, inventory, fulfillment, or refund permission |
| Merchant policy | The merchant allows the action under its eligibility, fraud, cancellation, return, refund, and escalation rules. | Identity or authorization from any principal |

For action-capable endpoints, require authorization evidence scoped to the action, resource, amount, merchant, duration, and relevant constraints. Do not infer that authority from agent identity or payment authorization. [SRC-AP2]

Where OAuth DPoP is used, verify sender-constrained tokens, request binding, short proof lifetimes, and replay detection rather than treating proof possession alone as authorization. [SRC-OAUTH-DPOP]

Reject or downgrade action readiness when any applicable trust link is absent. A profile, endpoint, Agent Card, signing key, valid signature, access token, or payment credential proves only its own layer.

## Checkout integrity

- Recalculate price, discounts, tax, shipping, fees, currency, and inventory from merchant-authoritative state before completion. Escalate mismatched totals for buyer review; do not silently alter or autonomously accept them. [SRC-UCP] [SRC-AP2]
- Bind consent or a mandate to the finalized checkout. AP2 separately binds checkout and payment mandates to the merchant-signed checkout and requires the relevant verifier to validate each role's evidence. [SRC-AP2]
- Honor checkout expiry and terminal states. Provide a buyer handoff for required input or review, and confirm the resulting order through a merchant-issued order identifier or receipt. [SRC-UCP] [SRC-AP2]
- For payment handoff, verify the Credential Provider returns a checkout-scoped payment credential only after validating the Payment Mandate; the Shopping Agent provides that credential and the Checkout Mandate to the Merchant; and the Merchant Payment Processor validates that the credential is scoped to the Checkout. AP2 v0.2 leaves transport and API details to the commerce protocol. [SRC-AP2]
- Make completion, cancellation, payment, refund, and other state-changing retries idempotent. Bind idempotency keys into signed requests where the protocol specifies that behavior, and return the prior result without repeating the side effect. [SRC-UCP]

## Post-checkout lifecycle

- Authenticate order reads and verify signed lifecycle events before applying them. Confirm that the signer is authorized for that order, not merely that its signature is valid. [SRC-UCP]
- Record confirmation, fulfillment, cancellation, return, refund, credit, dispute, and failed adjustment states. Enforce merchant policy and explicit approval boundaries before executing cancellation or money movement. [SRC-UCP]
- Require unique webhook identifiers and retry failed deliveries. Prefer append-only fulfillment and adjustment histories where supported. [SRC-UCP]
- Use the order's `checkout_id` to reconcile it with the originating checkout, and use authenticated Get Order responses to reconcile webhook state or retrieve it on demand. [SRC-UCP]
- When AP2 applies, retain the applicable signed checkout and payment mandates plus the receipt so the authorization and transaction trail can be verified. [SRC-AP2]

## Evidence and scoring

Use the existing protocol scale without changing the goal-based applicability decision:

- `not applicable`: the protocol does not serve the stated goal.
- `missing`: the protocol serves the goal but no usable artifact or implementation evidence exists.
- `partial`: artifacts or endpoints exist, but one or more applicable identity, authority, checkout, payment, policy, or lifecycle gates are absent or untested.
- `ready`: all applicable gates are implemented and documented, including negative paths and safe retry behavior.
- `verified`: `ready` evidence plus observed tests for invalid identity or authority, expiry or replay, duplicate requests, lifecycle authentication, and reconciliation appropriate to the goal.

An advertised protocol endpoint without agent verification or delegated authority must remain `partial` or lower for an action-capable goal; it cannot be `ready` or `verified`.
