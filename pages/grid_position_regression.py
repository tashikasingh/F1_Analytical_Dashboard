from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.graph_objects as go
from data_loader import *


from data_loader import seasons, filter_results, get_races
from visualisation.grid_logistic_regression import plot_grid_logistic_regression, _empty_fig


# ── STYLES ────────────────────────────────────────────────────────
F1_RED  = "#E10600"
CARD_BG = "#1A1A2E"
BORDER  = "#2a2a40"

DD_STYLE = {
    "backgroundColor": "#1E1E2E",
    "color":           "#000",
    "border":          f"1px solid {BORDER}",
    "borderRadius":    "6px"
}

LABEL_STYLE = {
    "color":         "#888",
    "fontSize":      "11px",
    "textTransform": "uppercase",
    "letterSpacing": "1px",
    "marginBottom":  "6px",
    "display":       "block"
}

CARD_STYLE = {
    "background":   CARD_BG,
    "border":       f"1px solid {BORDER}",
    "borderRadius": "12px",
    "padding":      "16px",
    "marginBottom": "16px",
}

# ── LAYOUT ────────────────────────────────────────────────────────
layout = html.Div(
    style={"maxWidth": "1400px", "margin": "0 auto"},
    children=[

        html.H1("Grid Position Impact", style={"color": F1_RED, "fontSize": "22px"}),
        html.P(
            "Logistic regression analysis: probability of top finishes based on grid position",
            style={"color": "#555", "fontSize": "12px", "marginBottom": "28px"},
        ),

        # ── GLOBAL FILTERS ────────────────────────────────────────
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "24px",
                   "flexWrap": "wrap", "alignItems": "flex-end"},
            children=[
                html.Div([
                    html.Label("From Year", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="gp-from-year-dd",
                        options=[{"label": str(s), "value": s} for s in seasons],
                        value=min(seasons) if seasons else None,
                        clearable=False,
                        style={**DD_STYLE, "width": "110px"}
                    )
                ]),
                html.Div([
                    html.Label("To Year", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="gp-to-year-dd",
                        options=[{"label": str(s), "value": s} for s in seasons],
                        value=max(seasons) if seasons else None,
                        clearable=False,
                        style={**DD_STYLE, "width": "110px"}
                    )
                ]),
                html.Div([
                    html.Label("Target Finish", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="gp-target-finish-dd",
                        options=[
                            {"label": "Top 3 (Podium)", "value": 3},
                            {"label": "Top 5", "value": 5},
                            {"label": "Top 10", "value": 10},
                        ],
                        value=3,
                        clearable=False,
                        style={**DD_STYLE, "width": "160px"}
                    )
                ]),
                html.Div([
                    html.Label("Grand Prix", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="gp-race-dd",
                        clearable=True,
                        style={**DD_STYLE, "width": "260px"}
                    )
                ]),
            ]
        ),

        # ── LOGISTIC REGRESSION CHART ────────────────────────────
        html.Div(style=CARD_STYLE, children=[
            html.Div(id="logistic-regression-container")
        ]),

    ]
)

# ── CALLBACKS ─────────────────────────────────────────────────────

@callback(
    Output("gp-race-dd", "options"),
    Input("gp-from-year-dd", "value"),
    Input("gp-to-year-dd", "value")
)
def update_races(from_year, to_year):
    if not from_year or not to_year:
        return []
    
    races_set = set()
    for year in range(min(from_year, to_year), max(from_year, to_year) + 1):
        races = get_races(year, "Race")
        races_set.update(races)
    
    races_list = sorted(list(races_set))
    options = [{"label": r, "value": r} for r in races_list]
    return options


@callback(
    Output("logistic-regression-container", "children"),
    Input("gp-from-year-dd", "value"),
    Input("gp-to-year-dd", "value"),
    Input("gp-target-finish-dd", "value"),
    Input("gp-race-dd", "value")
)
def render_logistic_regression(from_year, to_year, target_finish, race):
    if not from_year or not to_year or not target_finish:
        return html.Div("Select year range and target finish",
                        style={"color": "#666", "padding": "40px",
                               "textAlign": "center"})
    
    dfs = []
    
    try:
        if race:
            # Analyze specific Grand Prix across years
            for year in range(min(from_year, to_year), max(from_year, to_year) + 1):
                res_df = filter_results(year, race)
                if res_df is not None and not res_df.empty:
                    dfs.append(res_df)
        else:
            # Analyze all races in the year range if no specific race selected
            for year in range(min(from_year, to_year), max(from_year, to_year) + 1):
                races = get_races(year, "Race")
                for race_name in races:
                    res_df = filter_results(year, race_name)
                    if res_df is not None and not res_df.empty:
                        dfs.append(res_df)
        
        if not dfs:
            message = f"No data available for {race if race else 'selected range'}"
            fig = _empty_fig(message)
            return dcc.Graph(figure=fig)
        
        combined_df = pd.concat(dfs, ignore_index=True)
        fig = plot_grid_logistic_regression(combined_df, top_n=target_finish)
        return dcc.Graph(figure=fig)
        
    except Exception as e:
        return html.Div(f"Error: {str(e)}",
                        style={"color": "#999", "padding": "40px",
                               "textAlign": "center"})
