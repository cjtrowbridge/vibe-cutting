# Playbook: Create and Validate a Machine Profile

*Status: MVP*

## Objective

Capture conservative machine limits without treating manufacturer claims as locally verified facts.

## Procedure

1. Record sourced dimensions, speed, power scale, focus range, modules, and GRBL behavior.
2. Mark every unmeasured value provisional.
3. Compare live GRBL configuration without writing changes.
4. Run non-emitting bounds and framing tests.
5. Create a new profile revision after verified measurements change.

## Verification

- Missing safety-critical limits fail closed.
- Generated jobs fit the conservative work area.
- Fabrication-ready status requires physical acceptance evidence.
