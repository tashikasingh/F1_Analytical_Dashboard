
from dash import html
from dash.dependencies import Input, Output
from data_loader import *


F1_RED = "#E10600"
CARD_BG = "#1A1A2E"

layout = html.Div(
    [
        html.H1("Compare", style={"color": F1_RED, "fontSize": "22px"}),
        html.P(
            "Head-to-head driver comparison — lap times, deltas, and filtered analysis",
            style={"color": "#555", "fontSize": "12px", "marginBottom": "28px"},
        ),
        html.Div(id="compare-content"),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto"},
)

# Callback to update compare page based on global season filter
@callback(
    Output("compare-content", "children"),
    [
        Input("global-season-dropdown", "value"),
        Input("global-circuit-dropdown", "value"),
        Input("global-session-dropdown", "value"),
        Input("global-selected-drivers", "data"),
    ]
)
def update_compare_content(season, circuit, session_name, selected_drivers):
    selected_drivers = selected_drivers or []

    if not season or not circuit or not session_name:
        return html.Div("Choose a season, race, and session from the global filter.")
    if len(selected_drivers) < 2:
        return html.Div("Select two drivers above to compare fastest laps.")

    comparison_title = f"{selected_drivers[0]} vs {selected_drivers[1]}"
    return html.Div([
        html.Div(
            f"Fastest-lap overlay for {comparison_title} in {session_name} at {circuit} {season} will go here",
            style={
                "background": CARD_BG,
                "border": "1px dashed #2a2a40",
                "borderRadius": "12px",
                "padding": "40px",
                "color": "#444",
                "textAlign": "center",
                "marginBottom": "16px",
            },
        ),
        html.Div(
            f"Time delta chart for {comparison_title} will go here",
            style={
                "background": CARD_BG,
                "border": "1px dashed #2a2a40",
                "borderRadius": "12px",
                "padding": "40px",
                "color": "#444",
                "textAlign": "center",
                "marginBottom": "16px",
            },
        ),
        html.Div(
            f"Filtered fastest laps for {', '.join(selected_drivers)} will go here",
            style={
                "background": CARD_BG,
                "border": "1px dashed #2a2a40",
                "borderRadius": "12px",
                "padding": "40px",
                "color": "#444",
                "textAlign": "center",
                "marginBottom": "16px",
            },
        ),
    ])
