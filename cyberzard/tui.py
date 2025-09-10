from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static, DataTable
from textual.reactive import reactive
from textual import events

from .agent_engine.tools import scan_server, propose_remediation


class ScanApp(App):
    CSS = """
    Screen { background: $surface; }
    #title { content-align: center middle; height: 3; color: $accent; text-style: bold; }
    .metrics { layout: grid; grid-size: 2; grid-gutter: 1; }
    .metric { padding: 1; border: tall $accent; height: 5; content-align: center middle; }
    """

    running = reactive(False)
    summary = reactive(dict)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TabbedContent(
            TabPane("Summary", Static(id="title", renderable="Cyberzard Scan"), Static("Loading...", id="summary"), id="tab_summary"),
            TabPane("Findings", DataTable(id="findings"), id="tab_findings"),
            TabPane("Plan", Static("No plan yet", id="plan"), id="tab_plan"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.call_later(self._run_scan)

    async def _run_scan(self) -> None:
        if self.running:
            return
        self.running = True
        await self.run_worker(self._do_scan(), exclusive=True)

    async def _do_scan(self):
        results = scan_server(include_encrypted=False)
        plan = propose_remediation(results)
        self._render_summary(results)
        self._render_findings(results)
        self._render_plan(plan)

    def _render_summary(self, results):
        s = results.get("summary", {})
        items = [f"{k}: {v}" for k, v in s.items()]
        self.query_one('#summary', Static).update("\n".join(items))

    def _render_findings(self, results):
        table = self.query_one('#findings', DataTable)
        table.clear(columns=True)
        table.add_columns("Category", "Count")
        s = results.get("summary", {})
        for k, v in s.items():
            table.add_row(k, str(v))

    def _render_plan(self, plan):
        self.query_one('#plan', Static).update("Previews: " + str(plan.get('plan', {}).get('total_actions', 0)))


def run_tui():
    ScanApp().run()
