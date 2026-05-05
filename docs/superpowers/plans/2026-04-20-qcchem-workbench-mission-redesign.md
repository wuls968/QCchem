# QCchem Workbench Mission-Redesign Plan

> For Hermes: use Codex or subagent-driven-development for implementation, but keep scope limited to the visual workbench layer first.

Goal: Reframe the QCchem workbench as a serious scientific decision surface rather than a decorative dashboard.

Architecture: Keep the current Dash routing and artifact-backed page model, but redesign the shell, theme tokens, and page composition around three principles: evidence hierarchy, research-operating-system clarity, and publication-grade restraint. Use an IBM/Carbon-like design discipline adapted for chemistry evidence rather than the current soft “atelier” motif.

Tech stack: Dash, Plotly, CSS in `qcchem/workbench/assets/theme.css`, page composition in `qcchem/workbench/components/*.py` and `qcchem/workbench/pages/*.py`.

---

### Task 1: Replace the shell’s visual identity with a research-instrument language

Objective: Make the app feel like scientific software with clear authority, not a lifestyle dashboard.

Files:
- Modify: `qcchem/workbench/theme.py`
- Modify: `qcchem/workbench/assets/theme.css`
- Modify: `qcchem/workbench/components/layout.py`

Steps:
1. Replace parchment/copper palette with a restrained lab palette:
   - neutral background
   - dark graphite text
   - electric blue primary accent
   - semantic status colors with higher contrast
2. Replace serif-heavy “Scientific Atelier” framing with a more mission-aligned title and subtitle.
3. Tighten spacing, reduce ornamental gradients, and make panels/cards flatter and more systematic.
4. Rework shell navigation and interpretation rail to read like an operating console.
5. Verify `/overview` still renders and navigation still works.

Verification:
- `ruff check qcchem tests`
- Launch workbench and inspect `/overview` visually.

### Task 2: Rebuild overview page hierarchy around the core scientific question

Objective: Make the opening screen answer “what result can we defend right now?” in the first viewport.

Files:
- Modify: `qcchem/workbench/pages/overview.py`
- Modify: `qcchem/workbench/components/cards.py`
- Modify: `qcchem/workbench/components/charts.py`

Steps:
1. Replace decorative hero block with an evidence summary block.
2. Add a compact “defensibility” band showing:
   - claimed result
   - benchmark gap
   - chemical-accuracy status
   - runtime evidence status
3. Restyle metric cards into denser, more readable evidence tiles.
4. Tighten Plotly chart theming so charts look like instrument readouts, not marketing charts.
5. Keep molecule/context section, but subordinate it beneath the evidence story.

Verification:
- `ruff check qcchem tests`
- `pytest -q tests/integration/test_workbench_app_v14.py tests/integration/test_report_visuals_v14.py`
- Browser inspection of `/overview`

### Task 3: Improve the floating copilot so it stops visually hijacking the science surface

Objective: Keep the copilot useful while preventing it from dominating the screen.

Files:
- Modify: `qcchem/workbench/components/assistant.py`
- Modify: `qcchem/workbench/assets/theme.css`
- Modify: `qcchem/workbench/assets/assistant-window.js` (if needed)

Steps:
1. Reduce visual noise in the floating window.
2. Tighten header and controls.
3. Improve form density and field grouping.
4. Make status chips and actions look operational rather than ornamental.
5. Ensure draggable/resizable behavior still works.

Verification:
- `ruff check qcchem tests`
- `pytest -q tests/integration/test_workbench_ai_workspace_v15.py tests/integration/test_ai_workspace_cli_v15.py`
- Manual browser interaction.

### Task 4: Add reusable mission-aligned UI patterns for the rest of the pages

Objective: Build a stronger visual system that later pages can inherit without ad hoc styling.

Files:
- Modify: `qcchem/workbench/components/cards.py`
- Modify: `qcchem/workbench/assets/theme.css`
- Optional: `qcchem/workbench/components/layout.py`

Steps:
1. Introduce reusable card variants:
   - evidence card
   - status card
   - section header block
   - compact metric strip
2. Add utility classes for page section spacing and two-column evidence layouts.
3. Ensure cards and charts read consistently across pages.

Verification:
- `ruff check qcchem tests`
- spot-check `/structure-orbitals`, `/runtime-monitoring`, `/hardware-campaign`

### Task 5: Verify visual integrity and preserve behavior

Objective: Make sure the redesign improves the interface without breaking existing workbench logic.

Files:
- No required edits
- Test files may be updated only if UI text changes require it

Steps:
1. Run focused workbench tests.
2. Run full `pytest -q` if the visual refactor touched shared components.
3. Inspect the app in browser across at least:
   - `/overview`
   - `/structure-orbitals`
   - `/hardware-campaign`
4. Record remaining issues for a second-phase redesign.

Verification:
- `ruff check qcchem tests`
- `pytest -q`

---

Implementation notes:
- Default design direction: IBM/Carbon discipline adapted to chemistry evidence.
- Prioritize information hierarchy over decoration.
- Do not change chemistry logic in this pass.
- Prefer CSS/system-level improvements over page-specific hacks.
