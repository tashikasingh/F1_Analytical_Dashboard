# app.py

from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc

# =====================================================
# CREATE DASH APP
# =====================================================
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.SLATE]
)

server = app.server
app.title = "F1 Dashboard"

# =====================================================
# IMPORT AFTER APP CREATION
# =====================================================
from components.navbar import navbar

from pages import (
    race_analysis,
    grid_position_regression,
    driver_performance_trend,
    driver_dominance,
    pit_strategy_analysis,
    position_analysis
)

# =====================================================
# MAIN LAYOUT
# =====================================================
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),

        navbar,

        html.Div(
            id="page-content",
            style={
                "padding": "28px 30px 60px",
                "minHeight": "100vh",
                "backgroundColor": "#111119"
            }
        ),
    ]
)

# =====================================================
# SINGLE ROUTER CALLBACK
# ONLY ONE CALLBACK CONTROLS page-content.children
# =====================================================
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def router(pathname):

    routes = {
        "/race-analysis": race_analysis.layout,
        "/grid-position-analysis": grid_position_regression.layout,
        "/driver-performance-trend": driver_performance_trend.layout,
        "/driver-dominance": driver_dominance.layout,
        "/pit-strategy-analysis": pit_strategy_analysis.layout,
        "/position-analysis": position_analysis.layout,
    }

    return routes.get(pathname, race_analysis.layout)

# =====================================================
# RUN APP
# =====================================================
if __name__ == "__main__":
    app.run(debug=True, port=8051) 