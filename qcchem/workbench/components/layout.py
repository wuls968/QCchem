from __future__ import annotations

from collections.abc import Sequence

from dash import dcc, html, page_container, page_registry

from qcchem.workbench.components.assistant import build_floating_assistant
from qcchem.workbench.components.cards import callout_card, metric_card


def ordered_pages() -> list[dict[str, object]]:
    return sorted(
        [page for page in page_registry.values() if page.get("path")],
        key=lambda page: (int(page.get("order") or 0), str(page.get("path") or ""), str(page.get("name") or "")),
    )


def page_focus(pathname: str | None) -> dict[str, object]:
    active_path = pathname or "/overview"
    focus_map: dict[str, dict[str, object]] = {
        "/": {
            "route_label": "Overview",
            "summary": "Start with the best available chemistry evidence, then branch into orbital, compression, runtime, and confidence detail.",
            "rail_title": "Start from the defended story",
            "rail_note": "Use the overview to orient yourself before drilling into reduction, runtime, or benchmark nuance.",
            "callout_title": "Read this page like a lab notebook cover",
            "callout_body": "Treat the opening page as a compact scientific brief: total energy, error framing, runtime backing, and the path to deeper evidence.",
            "checklist": [
                ("Lead with", "Total energy + error envelope"),
                ("Then inspect", "Active space and compression rationale"),
                ("Carry forward", "Runtime and confidence posture"),
            ],
        },
        "/overview": {
            "route_label": "Overview",
            "summary": "Start with the best available chemistry evidence, then branch into orbital, compression, runtime, and confidence detail.",
            "rail_title": "Start from the defended story",
            "rail_note": "Use the overview to orient yourself before drilling into reduction, runtime, or benchmark nuance.",
            "callout_title": "Read this page like a lab notebook cover",
            "callout_body": "Treat the opening page as a compact scientific brief: total energy, error framing, runtime backing, and the path to deeper evidence.",
            "checklist": [
                ("Lead with", "Total energy + error envelope"),
                ("Then inspect", "Active space and compression rationale"),
                ("Carry forward", "Runtime and confidence posture"),
            ],
        },
        "/structure-orbitals": {
            "route_label": "Structure / Orbitals",
            "summary": "Keep the chemistry story visible: geometry context, orbital ordering, and why the active window still makes sense.",
            "rail_title": "Protect the chemistry narrative",
            "rail_note": "A reduced problem only feels trustworthy if the retained orbitals still read like a chemically coherent choice.",
            "callout_title": "Window choice before operator choice",
            "callout_body": "Read the orbital ladder first, then interpret compression and mapping as downstream consequences rather than arbitrary resource cuts.",
            "checklist": [
                ("Ask", "Which orbitals are active vs frozen?"),
                ("Check", "Does the window still look chemically sensible?"),
                ("Bridge to", "Compression and mapping pages"),
            ],
        },
        "/active-space-compression": {
            "route_label": "Active Space / Compression",
            "summary": "This is QCchem's core differentiator: reduction audit, retained chemistry, and operator compression shown together.",
            "rail_title": "Where QCchem should feel distinctive",
            "rail_note": "This page needs to answer both chemistry and cost: what was retained, what shrank, and why the approximation still reads as intentional.",
            "callout_title": "Compression is not just smaller math",
            "callout_body": "Use this view to connect chosen orbitals, post-factorization scale, and execution posture in one defended story.",
            "checklist": [
                ("Inspect", "Selection mode and retained orbitals"),
                ("Compare", "Pre vs post term scale"),
                ("Decide", "Whether compression reads as informed or blunt"),
            ],
        },
        "/mapping-resources": {
            "route_label": "Mapping / Resources",
            "summary": "Explain the practical burden directly: how many qubits, how much tapering, and what the circuit actually costs.",
            "rail_title": "Translate elegance into burden",
            "rail_note": "Mapping is only persuasive when it survives transpilation and two-qubit gate pressure.",
            "callout_title": "Resource realism matters",
            "callout_body": "Use this page to answer the uncomfortable question early: what the backend will actually need, not just what the model looks like on paper.",
            "checklist": [
                ("Count", "Qubits and Pauli terms"),
                ("Watch", "Depth and 2Q gates"),
                ("Relate", "Tapering savings to compiled burden"),
            ],
        },
        "/runtime-monitoring": {
            "route_label": "Runtime Monitoring",
            "summary": "Keep telemetry and chemistry connected: execution posture, submission evidence, and how hardware drifts from simulator expectations.",
            "rail_title": "Operational truth without losing chemistry",
            "rail_note": "The runtime page should make backend reality legible before anyone overclaims a hardware result.",
            "callout_title": "Evidence before excitement",
            "callout_body": "Use this page to pair queue / usage / compile evidence with the simulator-versus-hardware gap so runtime results stay honest.",
            "checklist": [
                ("Verify", "Attempt / submit / succeed"),
                ("Compare", "Simulator vs hardware error"),
                ("Interpret", "Telemetry as evidence, not decoration"),
            ],
        },
        "/result-confidence": {
            "route_label": "Result Confidence",
            "summary": "Close the loop with a report-grade answer: what evidence exists, what threshold matters, and whether the claim is defended.",
            "rail_title": "End with a defendable statement",
            "rail_note": "This page should read like the final paragraph of a careful research note, not a generic pass/fail badge.",
            "callout_title": "A confidence page should decide something",
            "callout_body": "Use the threshold framing and evidence checklist to answer whether the result is merely interesting, operationally retrieved, or scientifically defended.",
            "checklist": [
                ("State", "Absolute error and threshold"),
                ("Separate", "Runtime evidence from accuracy"),
                ("Conclude", "Validated / exploratory / unstable"),
            ],
        },
        "/lr-ace-method": {
            "route_label": "LR-ACE Method",
            "summary": "Flagship method view for generator selection, adaptive provenance, and trust-first validation gates.",
            "rail_title": "Make the main method inspectable",
            "rail_note": "LR-ACE should be easy to promote only when its exact-reference and compression evidence stay visible.",
            "callout_title": "A flagship method still needs gates",
            "callout_body": "Use this page to inspect generator count, profile, local exact status, and adaptive expansion evidence before treating LR-ACE as defended.",
            "checklist": [
                ("Inspect", "Generator plan and profile"),
                ("Check", "Local exact and compression gates"),
                ("Decide", "Validated, exploratory, or limited"),
            ],
        },
        "/studies": {
            "route_label": "Studies",
            "summary": "A research project view: compare run records, preserve axes, and keep the campaign readable as a coherent experiment.",
            "rail_title": "Read the study as a campaign",
            "rail_note": "Studies work best when the comparison axes stay explicit and the best record is easy to spot without flattening the rest.",
            "callout_title": "A study is more than a list of runs",
            "callout_body": "Use the study page to understand what changed between runs and which axes are carrying the scientific claim.",
            "checklist": [
                ("Track", "Backend / mapping / policy axes"),
                ("Spot", "Best energy and best error"),
                ("Preserve", "Exploratory separation if present"),
            ],
        },
        "/benchmarks": {
            "route_label": "Benchmarks",
            "summary": "This is the credibility dashboard: validated scope, unstable edges, and how much evidence supports each claim.",
            "rail_title": "Benchmark pages define trust",
            "rail_note": "Use this page to show what QCchem can defend today, not just what it can technically execute.",
            "callout_title": "Keep status bands visually honest",
            "callout_body": "Validated, exploratory, and unstable must feel meaningfully different here or the suite loses value.",
            "checklist": [
                ("Separate", "Validated vs unstable"),
                ("Compare", "Counts and mean error"),
                ("Read", "Best case as a trust anchor"),
            ],
        },
        "/scans": {
            "route_label": "Scans",
            "summary": "Read a scan like a chemistry path, not a CSV preview: the curve, the minimum, and the defended points should stand out.",
            "rail_title": "Scans should feel directional",
            "rail_note": "Good scan pages make a path legible: where the sweep moves, where the minimum lies, and how trustworthy the curve is.",
            "callout_title": "A scan is a shape, not just rows",
            "callout_body": "Use this page to see the sweep as an energy landscape first, then consult the point table for precise labels.",
            "checklist": [
                ("See", "Path shape and minimum"),
                ("Check", "Validated point count"),
                ("Use", "Point table for exact labels"),
            ],
        },
        "/hardware-campaign": {
            "route_label": "Hardware Campaign",
            "summary": "Hardware evidence stays comparative here: best retrieved case, runtime status ladder, and distance from chemical accuracy.",
            "rail_title": "Hardware claims need visible restraint",
            "rail_note": "This page should make clear what was truly retrieved, what failed, and how far the best case still is from the target.",
            "callout_title": "Best retrieved is not automatically best science",
            "callout_body": "Use the campaign page to rank hardware evidence honestly, with status and distance to chemical accuracy kept in view.",
            "checklist": [
                ("Rank", "Cases by achieved error"),
                ("Filter", "Retrieved vs submitted vs failed"),
                ("Anchor", "Distance to chemical accuracy"),
            ],
        },
        "/ai-workspace": {
            "route_label": "AI Workspace",
            "summary": "Evidence-first copilot surface for drafting tickets, reviewing work lanes, and carrying delivery history without breaking artifact authority.",
            "rail_title": "Keep agent work bounded",
            "rail_note": "This workspace should read persisted evidence before it drafts conclusions, and it should keep inbox, running, returned, and delivery states visibly separate.",
            "callout_title": "Interpret first, dispatch second",
            "callout_body": "Use the floating copilot to pull claim, trust tier, and recommended action into the ticket review flow before you let execution or delivery advance.",
            "checklist": [
                ("Draft", "A bounded task request"),
                ("Review", "Inbox, running, and returned lanes"),
                ("Inspect", "Delivery history and review state"),
            ],
        },
    }
    return focus_map.get(active_path, focus_map["/overview"])


def build_context_bar() -> html.Header:
    route_count = len([page for page in page_registry.values() if page.get("path")])
    default_focus = page_focus("/overview")
    return html.Header(
        className="qcchem-context-bar",
        children=[
            html.Div(
                className="qcchem-context-bar__identity",
                children=[
                    html.Div(
                        className="qcchem-context-bar__brand",
                        children=[
                            html.Img(
                                src="/assets/qcchem-logo.png",
                                alt="QCchem logo",
                                className="qcchem-context-bar__logo",
                            )
                        ],
                    ),
                    html.P("QCchem Evidence Console", className="qcchem-context-bar__eyebrow"),
                    html.H1("Evidence Workbench", className="qcchem-context-bar__title"),
                    html.P(
                        "Defended chemistry evidence, runtime provenance, and reduction decisions stay legible as you move from single-run review to campaign-scale comparison.",
                        className="qcchem-context-bar__subtitle",
                    ),
                    html.Div(
                        className="qcchem-context-bar__route",
                        children=[
                            html.P("Active route", className="qcchem-context-bar__route-eyebrow"),
                            html.H3(default_focus["route_label"], id="qcchem-context-current-route", className="qcchem-context-bar__route-title"),
                            html.P(default_focus["summary"], id="qcchem-context-current-summary", className="qcchem-context-bar__route-summary"),
                        ],
                    ),
                    html.Div(
                        className="qcchem-context-bar__chips",
                        children=[
                            html.Span("Thresholds stay explicit", className="qcchem-context-bar__chip"),
                            html.Span("Provenance precedes claims", className="qcchem-context-bar__chip"),
                            html.Span("Campaign pages inherit report-grade language", className="qcchem-context-bar__chip"),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="qcchem-context-bar__metrics",
                children=[
                    metric_card("Mode", "Scientific software", "Workbench shell for chemistry review", tone="compact"),
                    metric_card("Routes", str(route_count), "Single-run and aggregate evidence pages", tone="compact"),
                    metric_card("Focus", "Defended evidence", "Chemistry, runtime, and confidence stay linked", tone="compact"),
                    metric_card("Style", "Mission control", "Carbon discipline adapted to chemistry", tone="compact"),
                ],
            ),
        ],
    )


def build_research_navigator() -> html.Aside:
    sorted_pages = ordered_pages()
    nav_links = [
        dcc.Link(
            html.Div(
                className="qcchem-research-navigator__link-body",
                children=[
                    html.Span(page["name"], className="qcchem-research-navigator__link-title"),
                    html.Span(str(page.get("path") or ""), className="qcchem-research-navigator__link-meta"),
                ],
            ),
            href=page["path"],
            id=f"qcchem-nav-link--{index}",
            className="qcchem-research-navigator__link qcchem-research-navigator__link--inactive",
        )
        for index, page in enumerate(sorted_pages)
    ]
    return html.Aside(
        className="qcchem-research-navigator",
        children=[
            html.Div(
                className="qcchem-panel",
                children=[
                    html.P("Navigation", className="qcchem-panel__eyebrow"),
                    html.H2("Mission index", className="qcchem-panel__title"),
                    html.P(
                        "Move between single-run interpretation, aggregate campaign views, and confidence surfaces without losing the chemistry story.",
                        className="qcchem-panel__note",
                    ),
                    html.Nav(children=nav_links, className="qcchem-research-navigator__links"),
                ],
            ),
        ],
    )


def build_interpretation_rail() -> html.Aside:
    default_focus = page_focus("/overview")
    return html.Aside(
        className="qcchem-interpretation-rail",
        children=[
            html.Div(
                className="qcchem-panel",
                children=[
                    html.P("Review protocol", className="qcchem-panel__eyebrow"),
                    html.H2("Reading guide", id="qcchem-rail-page-title", className="qcchem-panel__title"),
                    html.P(
                        default_focus["rail_note"],
                        id="qcchem-rail-page-note",
                        className="qcchem-panel__note",
                    ),
                    html.Section(
                        id="qcchem-rail-callout",
                        children=[
                            callout_card(
                                str(default_focus["callout_title"]),
                                str(default_focus["callout_body"]),
                            )
                        ],
                    ),
                    html.Div(
                        id="qcchem-rail-checklist",
                        className="qcchem-rail-checklist",
                        children=[
                            html.Div(className="qcchem-rail-checklist__item", children=[html.Span(label), html.Strong(value)])
                            for label, value in default_focus["checklist"]
                        ],
                    ),
                ],
            ),
        ],
    )


def build_page_frame(children: Sequence[html.Component] | html.Component) -> html.Main:
    return html.Main(className="qcchem-page-frame", children=children)


def build_shell() -> html.Div:
    content = build_page_frame(page_container)
    return html.Div(
        className="qcchem-shell",
        children=[
            dcc.Location(id="qcchem-shell-location", refresh=False),
            build_context_bar(),
            html.Div(
                className="qcchem-main-grid",
                children=[
                    build_research_navigator(),
                    content,
                    build_interpretation_rail(),
                ],
            ),
            build_floating_assistant(),
        ],
    )
