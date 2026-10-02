"""Workflow Studio selection, review and control callbacks."""

from __future__ import annotations

from dash import Input, Output, State, ctx, dcc, html, no_update

from qcchem.workbench.workflow_controls import WorkbenchWorkflowController, require_local_control_request

PREFIX = "qcchem-workflow-control"


def workflow_controls_layout() -> html.Section:
    return html.Section([
        html.H2("Workflow controls", className="qcchem-card-title"),
        html.Label("Select a checkpoint", htmlFor=f"{PREFIX}-source"),
        dcc.Dropdown(id=f"{PREFIX}-source", options=[], clearable=False),
        html.Div(id=f"{PREFIX}-selection", role="status"),
        dcc.Store(id=f"{PREFIX}-session"),
        html.Label("Allow retry of these steps (required for unfinished attempts):"),
        dcc.Checklist(id=f"{PREFIX}-retry", options=[], value=[], className="qcchem-workflow-controls__retry"),
        html.Div([
            html.Button("Request cancellation", id=f"{PREFIX}-cancel", n_clicks=0, disabled=True),
            html.Button("Review resume", id=f"{PREFIX}-review", n_clicks=0, disabled=True),
            html.Button("Confirm resume", id=f"{PREFIX}-confirm", n_clicks=0, hidden=True),
        ], className="qcchem-workflow-controls__actions"),
        html.Div(id=f"{PREFIX}-review-plan"),
        dcc.Store(id=f"{PREFIX}-review-data"),
        html.Div(id=f"{PREFIX}-feedback", role="status", **{"aria-live": "polite"}),
        html.Div(id=f"{PREFIX}-job", role="status"),
    ], className="qcchem-card qcchem-workflow-controls")


def _review_content(review):
    return html.Div([
        html.H3("Review recovery"),
        html.P(f"Configuration: {review['source_path']}"),
        html.P(f"Output: {review['artifact_root']}"),
        html.P("Reuse completed steps: " + (", ".join(review["reused_steps"]) or "None")),
        html.P("You allow retrying: " + (", ".join(review["retry_steps"]) or "None; only pending steps will run")),
        html.Ul([html.Li(f"{step['id']} · {step['kind']}") for step in review["pending_steps"]]),
        html.P("Review existing partial outputs before confirming. Previously started steps may have external effects. Runtime budget approvals still apply."),
    ], className="qcchem-workflow-controls__review")


def register_workflow_control_callbacks(app, controller: WorkbenchWorkflowController) -> None:
    @app.callback(
        Output(f"{PREFIX}-source", "options"), Output(f"{PREFIX}-source", "value"),
        Output(f"{PREFIX}-selection", "children"), Output(f"{PREFIX}-session", "data"),
        Output(f"{PREFIX}-retry", "options"), Output(f"{PREFIX}-retry", "value"),
        Output(f"{PREFIX}-cancel", "disabled"), Output(f"{PREFIX}-review", "disabled"),
        Output(f"{PREFIX}-job", "children"),
        Input("qcchem-workflow-studio-status-poll", "n_intervals"),
        Input(f"{PREFIX}-source", "value"), State(f"{PREFIX}-retry", "value"),
    )
    def refresh(_intervals, selection, retries):
        catalog = controller.catalog()
        options = [{"label": row["label"], "value": row["value"]} for row in catalog]
        value = selection or (catalog[0]["value"] if catalog else None)
        row = next((row for row in catalog if row["value"] == value), None)
        selected = value if value != selection else no_update
        if not row or row["error"]:
            message = row["error"] if row else "No available workflow checkpoints under the configured artifact root."
            return options, selected, message, None, [], [], True, True, ""
        status = row["status"]
        current = (status.get("current_step") or {}).get("step_id")
        retry_ids = list(dict.fromkeys([*status["retry_steps"], *([current] if current else [])]))
        retry_options = [{"label": step, "value": step} for step in retry_ids]
        allowed = [] if ctx.triggered_id == f"{PREFIX}-source" else [step for step in (retries or []) if step in retry_ids]
        job = controller.job_status(value)
        busy = status["worker_active"] or bool(job and job["status"] in {"queued", "running"})
        try:
            require_local_control_request()
            local = True
        except ValueError:
            local = False
        details = [html.P(f"{status['workflow_name']} · {status['status']} · {len(status['completed_steps'])} completed steps"),
                   html.P(str(row["path"])), html.P(f"Current step: {current}") if current else None,
                   html.P("Controls are available only from a local browser.") if not local else None]
        job_content = [html.P(f"Recovery job: {job['status']}"), html.P(f"Log: {job['log_path']}"),
                       html.P(job["error"]) if job.get("error") else None] if job else []
        return (options, selected, details, {"session_id": status["session_id"], "value": value},
                retry_options, allowed if allowed != (retries or []) else no_update,
                not (local and status["status"] == "running"),
                not local or busy or status["status"] == "completed", job_content)

    @app.callback(
        Output(f"{PREFIX}-feedback", "children"), Output(f"{PREFIX}-review-plan", "children"),
        Output(f"{PREFIX}-review-data", "data"), Output(f"{PREFIX}-confirm", "hidden"),
        Input(f"{PREFIX}-cancel", "n_clicks"), Input(f"{PREFIX}-review", "n_clicks"),
        Input(f"{PREFIX}-confirm", "n_clicks"), Input(f"{PREFIX}-source", "value"),
        Input(f"{PREFIX}-retry", "value"), State(f"{PREFIX}-session", "data"),
        State(f"{PREFIX}-review-data", "data"), prevent_initial_call=True,
    )
    def act(cancel_clicks, review_clicks, confirm_clicks, value, retries, session, review_data):
        triggered = ctx.triggered_id
        if triggered in {f"{PREFIX}-source", f"{PREFIX}-retry"}:
            return no_update, [], None, True
        clicks = {f"{PREFIX}-cancel": cancel_clicks, f"{PREFIX}-review": review_clicks, f"{PREFIX}-confirm": confirm_clicks}
        if not clicks.get(triggered):
            return (no_update,) * 4
        try:
            require_local_control_request()
            if not session or session.get("value") != value:
                raise ValueError("Refresh the selected workflow before using controls.")
            if triggered == f"{PREFIX}-cancel":
                result = controller.cancel(value, session["session_id"])
                message = "Cancellation requested; waiting for a safe execution boundary. Existing provider jobs continue." if result["action"] == "request_written" else "Workflow has already stopped."
                return message, [], None, True
            if triggered == f"{PREFIX}-review":
                review = controller.review(value, retries or [], session["session_id"])
                data = {key: review[key] for key in ("token", "value", "session_id", "retry_steps")}
                return "Review the steps below, then confirm to start recovery.", _review_content(review), data, False
            if not review_data or (review_data.get("value"), review_data.get("session_id"), review_data.get("retry_steps")) != (value, session["session_id"], retries or []):
                raise ValueError("The selected workflow or retry choices changed; review again.")
            job = controller.start(review_data["token"])
            return f"Recovery queued. Log: {job['log_path']}", [], None, True
        except Exception as exc:
            return f"Action blocked: {type(exc).__name__}: {exc}", [], None, True
