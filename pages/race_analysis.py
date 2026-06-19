from dash import html, dcc, callback, Input, Output, ALL, MATCH

from components.buttons.driver_toggle_button import get_driver_toggle_button_style
from data_loader import (
    seasons,
    filter_laps,
    filter_results,
    get_races,
    get_color_map,
)
from pages.standings import build_single_standings_card
from visualisation.lap_times import plot_lap_times, lap_times_layout, _empty_fig
from visualisation.position_changes import plot_position_changes


# ── STYLES ────────────────────────────────────────────────────────
F1_RED = "#E10600"
CARD_BG = "#1A1A2E"
BORDER = "#2a2a40"

DD_STYLE = {
    "backgroundColor": "#1E1E2E",
    "color": "#000",
    "border": f"1px solid {BORDER}",
    "borderRadius": "6px",
}

LABEL_STYLE = {
    "color": "#888",
    "fontSize": "11px",
    "textTransform": "uppercase",
    "letterSpacing": "1px",
    "marginBottom": "6px",
    "display": "block",
}

CARD_STYLE = {
    "background": CARD_BG,
    "border": f"1px solid {BORDER}",
    "borderRadius": "12px",
    "padding": "16px",
    "marginBottom": "16px",
}

BTN_BASE = {
    "borderRadius": "20px",
    "padding": "6px 18px",
    "fontSize": "12px",
    "fontWeight": "700",
    "cursor": "pointer",
    "border": "1px solid #555",
    "fontFamily": "'Titillium Web', Arial, sans-serif",
    "letterSpacing": "1px",
    "marginRight": "8px",
}

BTN_ACTIVE = {
    **BTN_BASE,
    "backgroundColor": F1_RED,
    "color": "#FFFFFF",
    "border": f"1px solid {F1_RED}",
}

BTN_INACTIVE = {
    **BTN_BASE,
    "backgroundColor": "rgba(0,0,0,0)",
    "color": "#666",
}


# ── LAYOUT ────────────────────────────────────────────────────────
layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto"},
    children=[
        html.H1("Race Analysis", style={"color": F1_RED, "fontSize": "22px"}),

        html.P(
            "Lap times, positions, tyres, and pit stops — all in one place",
            style={"color": "#555", "fontSize": "12px", "marginBottom": "28px"},
        ),

        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "24px",
                "flexWrap": "wrap",
                "alignItems": "flex-end",
            },
            children=[
                html.Div([
                    html.Label("Season", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="ra-season-dd",
                        options=[{"label": str(s), "value": s} for s in seasons],
                        value=seasons[0] if seasons else None,
                        clearable=False,
                        style={**DD_STYLE, "width": "110px"},
                    ),
                ]),

                html.Div([
                    html.Label("Session", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="ra-session-dd",
                        options=[
                            {"label": "Race", "value": "Race"},
                            {"label": "Qualifying", "value": "Qualifying"},
                        ],
                        value="Race",
                        clearable=False,
                        style={**DD_STYLE, "width": "140px"},
                    ),
                ]),

                html.Div([
                    html.Label("Grand Prix", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="ra-gp-dd",
                        clearable=False,
                        style={**DD_STYLE, "width": "260px"},
                    ),
                ]),
            ],
        ),

        dcc.Store(id="ra-color-map-store"),

        # Season standings
        html.Div(
            style=CARD_STYLE,
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "gap": "16px",
                        "flexWrap": "wrap",
                        "marginBottom": "16px",
                    },
                    children=[
                        html.H3(
                            "Season Standings",
                            style={
                                "color": "#FFFFFF",
                                "fontSize": "18px",
                                "margin": "0",
                            },
                        ),

                        dcc.Dropdown(
                            id="ra-standings-type-dd",
                            options=[
                                {"label": "Driver Standings", "value": "drivers"},
                                {"label": "Constructor Standings", "value": "constructors"},
                            ],
                            value="drivers",
                            clearable=False,
                            style={**DD_STYLE, "width": "220px"},
                        ),
                    ],
                ),

                html.Div(id="ra-standings-container"),
            ],
        ),

        # Lap times
        html.Div(
            style=CARD_STYLE,
            children=[
                html.Div(id="lap-times-container"),
            ],
        ),

        # Position changes
        html.Div(
            style=CARD_STYLE,
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "16px",
                        "flexWrap": "wrap",
                        "gap": "12px",
                    },
                    children=[
                        html.Div([
                            html.H3(
                                "Race Position Changes",
                                style={
                                    "color": "#FFFFFF",
                                    "fontSize": "18px",
                                    "margin": "0 0 4px 0",
                                },
                            ),

                            html.P(
                                "Bump chart showing lap-by-lap position changes. Coloured dots mark pit stops.",
                                style={
                                    "color": "#555",
                                    "fontSize": "12px",
                                    "margin": "0",
                                },
                            ),
                        ]),

                        html.Div([
                            html.Button(
                                "Top 10",
                                id="ra-top10-btn",
                                n_clicks=1,
                                style=BTN_ACTIVE,
                            ),
                            html.Button(
                                "Bottom 10",
                                id="ra-bottom10-btn",
                                n_clicks=0,
                                style=BTN_INACTIVE,
                            ),
                        ]),
                    ],
                ),

                html.Div(
                    style={"marginBottom": "16px"},
                    children=[
                        html.Label("Highlight Drivers", style=LABEL_STYLE),
                        dcc.Dropdown(
                            id="ra-highlight-dd",
                            options=[],
                            value=None,
                            multi=True,
                            placeholder="Select drivers to highlight...",
                            style={**DD_STYLE, "maxWidth": "500px"},
                        ),
                    ],
                ),

                html.Div(id="ra-position-changes-container"),
            ],
        ),
    ],
)


# ── CALLBACKS ─────────────────────────────────────────────────────
@callback(
    Output("ra-gp-dd", "options"),
    Output("ra-gp-dd", "value"),
    Input("ra-season-dd", "value"),
    Input("ra-session-dd", "value"),
)
def update_gp(season, session):
    races = get_races(season, session)
    options = [{"label": r, "value": r} for r in races]
    return options, races[0] if races else None


@callback(
    Output("ra-color-map-store", "data"),
    Input("ra-season-dd", "value"),
    Input("ra-gp-dd", "value"),
    Input("ra-session-dd", "value"),
)
def update_color_map(season, gp, session):
    if not gp:
        return {}
    return get_color_map(season, gp, session)


@callback(
    Output("ra-standings-container", "children"),
    Input("ra-season-dd", "value"),
    Input("ra-standings-type-dd", "value"),
)
def render_standings_tables(season, standings_type):
    return build_single_standings_card(season, standings_type)


@callback(
    Output("lap-times-container", "children"),
    Input("ra-season-dd", "value"),
    Input("ra-gp-dd", "value"),
    Input("ra-session-dd", "value"),
    Input("ra-color-map-store", "data"),
)
def render_lap_times(season, gp, session, color_map):
    if not gp:
        return html.Div(
            "Select a Grand Prix",
            style={"color": "#666", "padding": "40px", "textAlign": "center"},
        )

    laps_df = filter_laps(season, gp, session)
    res_df = filter_results(season, gp)

    return lap_times_layout(laps_df, res_df, session, color_map or {})


@callback(
    Output("lap-chart", "figure"),
    Input("ra-season-dd", "value"),
    Input("ra-gp-dd", "value"),
    Input("ra-session-dd", "value"),
    Input({"type": "driver-btn", "index": ALL}, "n_clicks"),
    Input({"type": "driver-btn", "index": ALL}, "id"),
    Input("ra-color-map-store", "data"),
)
def update_chart(season, gp, session, n_clicks_list, ids, color_map):
    if not gp:
        return _empty_fig("Select a Grand Prix")

    selected = [
        btn["index"]
        for btn, n in zip(ids, n_clicks_list)
        if n and n % 2 == 1
    ]

    laps_df = filter_laps(season, gp, session)

    return plot_lap_times(
        df=laps_df,
        session_type=session,
        selected_drivers=selected or None,
        color_map=color_map or {},
    )


@callback(
    Output({"type": "driver-btn", "index": MATCH}, "style"),
    Input({"type": "driver-btn", "index": MATCH}, "n_clicks"),
)
def toggle_button_style(n_clicks):
    return get_driver_toggle_button_style(n_clicks)


# ── POSITION CHANGES CALLBACKS ────────────────────────────────────
@callback(
    Output("ra-highlight-dd", "options"),
    Input("ra-season-dd", "value"),
    Input("ra-gp-dd", "value"),
    Input("ra-session-dd", "value"),
)
def update_highlight_options(season, gp, session):
    if not gp or session != "Race":
        return []

    laps_df = filter_laps(season, gp, "Race")

    if laps_df.empty or "Driver" not in laps_df.columns:
        return []

    drivers = sorted(laps_df["Driver"].dropna().unique().tolist())
    return [{"label": d, "value": d} for d in drivers]


@callback(
    Output("ra-top10-btn", "style"),
    Output("ra-bottom10-btn", "style"),
    Input("ra-top10-btn", "n_clicks"),
    Input("ra-bottom10-btn", "n_clicks"),
)
def toggle_group_buttons(top_clicks, bot_clicks):
    top_clicks = top_clicks or 0
    bot_clicks = bot_clicks or 0

    if bot_clicks > top_clicks:
        return BTN_INACTIVE, BTN_ACTIVE

    return BTN_ACTIVE, BTN_INACTIVE


@callback(
    Output("ra-position-changes-container", "children"),
    Input("ra-season-dd", "value"),
    Input("ra-gp-dd", "value"),
    Input("ra-session-dd", "value"),
    Input("ra-color-map-store", "data"),
    Input("ra-top10-btn", "n_clicks"),
    Input("ra-bottom10-btn", "n_clicks"),
    Input("ra-highlight-dd", "value"),
)
def render_position_changes(
    season,
    gp,
    session,
    color_map,
    top_clicks,
    bot_clicks,
    highlight,
):
    if session != "Race":
        return html.Div(
            "Position changes are only available for Race sessions.",
            style={"color": "#666", "padding": "30px", "textAlign": "center"},
        )

    if not gp:
        return html.Div(
            "Select a Grand Prix to see position changes.",
            style={"color": "#666", "padding": "30px", "textAlign": "center"},
        )

    show_group = "bottom10" if (bot_clicks or 0) > (top_clicks or 0) else "top10"

    laps_df = filter_laps(season, gp, "Race")

    fig = plot_position_changes(
        df=laps_df,
        color_map=color_map or {},
        selected_drivers=highlight if highlight else None,
        show_group=show_group,
    )

    return dcc.Graph(figure=fig, config={"displayModeBar": False})