# Kanban Verbatim Handling

## Task Identity

- A task is identified by the exact Markdown list line text.
- Identity is byte-for-byte equality, including punctuation, spacing, casing, and symbols.

## Verbatim Move Rules

- Move operations must copy the exact line text into the destination section.
- After successful copy, remove the same exact line from the source section.
- Do not normalize whitespace, rewrite grammar, fix spelling, or alter punctuation.
- Do not merge, split, deduplicate, or reorder tasks unless explicitly instructed.

## Duplicate Task Text Handling

- If identical task lines appear multiple times in one source section, stop and ask for disambiguation.
- Disambiguation should reference a stable selector such as section name + line number.
- Do not guess which duplicate was intended.

## Required Evidence Before Save/Commit

- Show exact before/after excerpts or diff snippets with the task line unchanged.
- Explicitly list each move as: `source -> destination: exact line`.

## Anti-Patterns

- Rephrasing a task while moving it.
- Summarizing multiple tasks into one line.
- "Cleaning up" formatting while moving tasks.
- Silent task deletion due to ambiguity.
- Using placeholder task bullets such as `- (empty)` that can be mistaken for real tasks.
