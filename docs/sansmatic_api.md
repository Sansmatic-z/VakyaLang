# Sansmatic API

## Runtime Builtins

- `परिभाषय(name, properties)`:
  Register a concept and seed `HAS` facts for its properties.
- `दावा(entity, relation, property, proof_id=None)`:
  Assert a fact. Known or derivable facts succeed immediately. Unsupported facts
  become proof obligations unless a trusted proof reference supports them.
- `नियम(a, rel_a, prop_a, b, rel_b, prop_b)`:
  Register a forward-chaining implication rule.
- `मूल्यांकन(entity, relation, property)`:
  Return a status string explaining whether the statement is derivable and
  whether contradictions or proof obligations block execution.
- `सिद्ध_है(entity, relation, property)`:
  Boolean derivability query.
- `प्रमाण_लॉग()`:
  Return the current proof log as a list of strings.
- `प्रमाण_सारांश()`:
  Return a structured proof summary, including counts and consistency.
- `प्रमाण_अनुक्रम([limit])`:
  Return structured proof-trace events showing fact registration, rule firing,
  obligations, and contradictions.
- `प्रमाण_वृक्ष(entity, relation, property)`:
  Return a proof tree for the requested goal.
- `प्रमाण_व्याख्या(entity, relation, property)`:
  Return an explanation payload for the goal, including blockers such as proof
  obligations or contradictions.
- `प्रमाण_स्नैपशॉट()`:
  Capture the current proof-engine state.
- `प्रमाण_पुनर्स्थापय([state])`:
  Restore the last or provided proof-engine snapshot.
- `प्रमाण_रीसेट()`:
  Clear proof state for the current engine instance.

## Certificate Payload

Sansmatic certificates preserve the existing payload keys:

- `kind`
- `version`
- `statement`
- `verified`
- `pramana`
- `confidence`
- `certificate_hint`
- `reason`
- `facts`
- `derived`
- `rules`
- `obligations`
- `contradictions`
- `hash`

Additive metadata may also be present:

- `metadata`:
  Verification policy and evidence summary emitted by `NyayaProofVerifier`.
- `signature_alg`
- `signature`

## Environment Variables

- `SANSMATIC_CERTIFICATE_MODE`:
  `auto`, `legacy-hash`, or `hmac-sha256`
- `SANSMATIC_CERTIFICATE_SECRET`:
  HMAC secret used when authenticated certificates are enabled
- `SANSMATIC_ALLOW_LEGACY_CERTIFICATES`:
  `true` or `false`
- `SANSMATIC_STRICT_PROOF_REGISTRATION`:
  `true` or `false`
- `SANSMATIC_LOG_LEVEL`:
  Standard Python logging level

## Audit Events

The verifier emits these audit hooks through Python's audit subsystem:

- `vak.proof.verify.start`
- `vak.proof.verify.complete`

The wider runtime also emits file, import, interpreter, HTTP, and thread events.

## Deployment Guidance

- Keep `SANSMATIC_STRICT_PROOF_REGISTRATION=true` in all non-test environments.
- Prefer `SANSMATIC_CERTIFICATE_MODE=hmac-sha256` with a non-empty
  `SANSMATIC_CERTIFICATE_SECRET` in CI and production.
- Only allow legacy certificates during migration windows.
