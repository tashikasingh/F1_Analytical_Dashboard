import dash_bootstrap_components as dbc
from dash import html

# ── Colour tokens ────────────────────────────────────────────────────
F1_RED = "#E10600"
NAV_BG = "#1A1A2E"

# ── Navigation bar ───────────────────────────────────────────────────
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    # ── Logo / Title ───────────────────────────────
                    dbc.Col(
                        html.Span(
                            "🏎️ F1 Dashboard",
                            style={
                                "color": F1_RED,
                                "fontSize": "18px",
                                "fontWeight": "bold",
                                "marginRight": "40px",
                                "padding": "8px 14px",
                                "whiteSpace": "nowrap",
                            },
                        ),
                        width="auto",
                    ),

                    # ── Navigation Links ───────────────────────────
                    dbc.Col(
                        dbc.Nav(
                            [
                                dbc.NavLink(
                                    "Race Analysis",
                                    href="/race-analysis",
                                    id="nav-race",
                                    active="exact",
                                ),

                                dbc.NavLink(
                                    "Grid Position Analysis",
                                    href="/grid-position-analysis",
                                    id="nav-gridpos",
                                    active="exact",
                                ),

                                dbc.NavLink(
                                    "Driver Trends",
                                    href="/driver-performance-trend",
                                    id="nav-dpt",
                                    active="exact",
                                ),

                                dbc.NavLink(
                                    "Driver Dominance",
                                    href="/driver-dominance",
                                    id="nav-dd",
                                    active="exact",
                                ),

                                dbc.NavLink(
                                    "Pit Strategy",
                                    href="/pit-strategy-analysis",
                                    id="nav-pit",
                                    active="exact",
                                ),

                                dbc.NavLink(
                                    "Position Analysis",
                                    href="/position-analysis",
                                    active="exact",
                                ),
                            ],
                            navbar=True,
                            className="gap-2",
                        ),
                        width=True,
                    ),
                ],
                align="center",
                className="g-0 flex-nowrap",
            ),
        ],
        fluid=True,
    ),

    color=NAV_BG,
    dark=True,
    style={
        "borderBottom": f"2px solid {F1_RED}",
        "padding": "10px 20px",
    },
)