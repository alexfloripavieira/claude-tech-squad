# Live Golden Run Capture Instructions

For this dogfood evidence run:

- Execute the requested claude-tech-squad skill against the fixture named in the prompt.
- Do not edit repository files.
- When a skill reaches an operator gate, record the gate as approved for the purpose of this capture and continue.
- Emit the required trace lines visibly.
- Return the final answer with a `result_contract` block.
- If a full teammate-mode run cannot be completed in `claude -p`, state the blocker explicitly and emit the partial trace.
