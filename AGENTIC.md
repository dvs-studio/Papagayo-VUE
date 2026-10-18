# Agentic Continuation Protocol

This project follows an agent-friendly multi-turn workflow. Any agent joining this codebase should adhere to the following sequence:

1. **Orientation**:
   - Read `RULES.md` to understand core architectural principles.
   - Read `STATUS.md` to see recent accomplishments and active to-do items.
   - Read `AGENT_API.md` for function signatures and module interactions.
2. **Preservation**:
   - Maintain the landscape timeline layout.
   - Run `python3 -m py_compile` across all Python files to verify compilation after any code edits.
3. **Packaging**:
   - Windows packaging is driven by `build_windows.py` and `papagayo-ng.spec`.
   - CI automation is controlled via `.github/workflows/build-windows.yml`.
