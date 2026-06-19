from dash import html, dcc, Input, Output

from app import app
from components.navbar import navbar
# from components.global_filter import global_filter
from pages import race_analysis, grid_position_regression, driver_performance_trend, driver_dominance
from pages import pit_strategy_analysis

# ── Colour tokens ────────────────────────────────────────────────────
BODY_BG = "#111119"

# ── App layout ───────────────────────────────────────────────────────
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        html.Div(id="page-content", style={"padding": "28px 30px 60px"}),
    ],
    style={"backgroundColor": BODY_BG, "minHeight": "100vh"},
)


# ── URL routing ──────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/race-analysis":
        return race_analysis.layout
    if pathname == "/grid-position-analysis":
        return grid_position_regression.layout
    if pathname == "/driver-performance-trend":
        return driver_performance_trend.layout
    if pathname == "/driver-dominance":
        return driver_dominance.layout

    # ✅ ADD THIS NEW PAGE
    if pathname == "/pit-strategy-analysis":
        return pit_strategy_analysis.layout

    return race_analysis.layout


# ── Run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8051)
