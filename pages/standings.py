from dash import html, dcc, callback, Input, Output
from dash.dependencies import Input, Output, State


from data_loader import load_csv, seasons
import plotly.express as px
from visualisation.driver_standings import driver_standings_card, get_driver_standings_df
from data_loader import *

F1_RED = "#E10600"
CARD_BG = "#1A1A2E"
CHART_BG = "#111119"
ALL_CONSTRUCTORS = "__all__"


def _table_header(columns):
    return html.Thead(
        html.Tr(
            [
                html.Th(
                    label,
                    style={"color": F1_RED, "padding": "12px", "textAlign": align},
                )
                for label, align in columns
            ]
        )
    )


def _season_summary_card(season, total_races, driver_count, team_count):
    return html.Div(
        [
            html.H3(f"{season} Season", style={"color": F1_RED, "marginBottom": "12px"}),
            html.Div(
                [
                    html.Span(f"Races Completed: {total_races}", style={"marginRight": "20px"}),
                    html.Span(f"Drivers: {driver_count}"),
                    html.Span(f" | Teams: {team_count}", style={"marginLeft": "20px"}),
                ],
                style={"color": "#CCCCCC", "fontSize": "14px"},
            ),
        ],
        style={
            "background": CARD_BG,
            "borderRadius": "12px",
            "padding": "20px",
            "marginBottom": "16px",
        },
    )


def _constructor_standings_card(team_standings):
    return html.Div(
        [
            html.H4("Constructor Championship", style={"color": "#FFFFFF", "marginBottom": "16px"}),
            html.Table(
                [
                    _table_header([("Pos", "left"), ("Team", "left"), ("Points", "right")]),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(
                                        row["Position"],
                                        style={"padding": "10px", "color": "#FFFFFF", "fontWeight": "bold"},
                                    ),
                                    html.Td(row["TeamName"], style={"padding": "10px", "color": "#CCCCCC"}),
                                    html.Td(
                                        int(row["Points"]),
                                        style={
                                            "padding": "10px",
                                            "color": "#FFFFFF",
                                            "textAlign": "right",
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ],
                                style={
                                    "borderBottom": "1px solid #2a2a40",
                                    "backgroundColor": "#1A1A2E" if i % 2 == 0 else "#15151E",
                                },
                            )
                            for i, (_, row) in enumerate(team_standings.iterrows())
                        ]
                    ),
                ],
                style={"width": "100%", "borderCollapse": "collapse"},
            ),
        ],
        style={
            "background": CARD_BG,
            "borderRadius": "12px",
            "padding": "20px",
            "marginBottom": "16px",
        },
    )


def _points_progression_placeholder():
    return html.Div(
        [
            html.H4("Points Progression", style={"color": "#FFFFFF", "marginBottom": "16px"}),
            html.Div(
                "Interactive championship progression chart will be displayed here",
                style={"color": "#666", "textAlign": "center", "padding": "60px"},
            ),
        ],
        style={
            "background": CARD_BG,
            "border": "1px dashed #2a2a40",
            "borderRadius": "12px",
            "padding": "20px",
        },
    )


def _wins_chart_card():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Race Wins Analysis", style={"color": "#FFFFFF", "marginBottom": "6px"}),
                           
                        ]
                    ),
                    dcc.Dropdown(
                        id="wins-constructor-dropdown",
                        options=[],
                        value=ALL_CONSTRUCTORS,
                        clearable=False,
                        searchable=False,
                        className="global-filter-dropdown",
                        style={
                            "minWidth": "240px",
                            "backgroundColor": "#2A2A2D",
                            "color": "#070707",
                            "border": "1px solid #54545A",
                            "borderRadius": "14px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "gap": "16px",
                    "alignItems": "center",
                    "flexWrap": "wrap",
                    "marginBottom": "16px",
                },
            ),
            html.Div(
                id="wins-by-driver-summary",
                style={"color": "#D1D5DB", "fontSize": "14px", "marginBottom": "16px"},
            ),
            dcc.Graph(
                id="wins-by-driver-chart",
                config={"displayModeBar": False},
                style={"height": "380px"},
            ),
        ],
        style={
            "background": CARD_BG,
            "borderRadius": "12px",
            "padding": "20px",
            "marginBottom": "16px",
        },
    )


def _get_season_results_df(season):
    if not season:
        return None
    results_df = load_csv("race", f"race_results_{season}.csv")
    if results_df.empty:
        return None
    return results_df.copy()


def _get_driver_standings_df(season):
    results_df = _get_season_results_df(season)
    if results_df is None:
        return None
    return get_driver_standings_df(results_df)


def _get_constructor_standings_df(season):
    results_df = _get_season_results_df(season)
    if results_df is None:
        return None

    team_standings = (
        results_df.groupby("TeamName")
        .agg({"Points": "sum", "TeamColor": "first"})
        .reset_index()
        .sort_values(["Points", "TeamName"], ascending=[False, True])
    )
    team_standings["Position"] = range(1, len(team_standings) + 1)
    team_standings["TeamColor"] = (
        team_standings["TeamColor"].fillna("4F8CFF").apply(lambda c: f"#{str(c).lstrip('#')}")
    )
    return team_standings


def _get_constructor_dropdown_options(season):
    results_df = _get_season_results_df(season)
    if results_df is None:
        return [{"label": "All Constructors", "value": ALL_CONSTRUCTORS}]

    constructors = sorted(results_df["TeamName"].dropna().unique().tolist())
    return [{"label": "All Constructors", "value": ALL_CONSTRUCTORS}] + [
        {"label": constructor, "value": constructor} for constructor in constructors
    ]


def _get_wins_dataframe(season, constructor_filter):
    results_df = _get_season_results_df(season)
    if results_df is None:
        return None

    if constructor_filter and constructor_filter != ALL_CONSTRUCTORS:
        results_df = results_df[results_df["TeamName"] == constructor_filter]

    wins_df = results_df[results_df["Position"] == 1].copy()
    if wins_df.empty:
        return wins_df

    wins_df = (
        wins_df.groupby(["Abbreviation", "BroadcastName", "TeamName"], dropna=False)
        .agg(Wins=("EventName", "size"), TeamColor=("TeamColor", "first"))
        .reset_index()
        .sort_values(["Wins", "Abbreviation"], ascending=[False, True])
    )
    wins_df["DisplayName"] = wins_df["BroadcastName"].fillna(wins_df["Abbreviation"])
    wins_df["TeamColor"] = wins_df["TeamColor"].fillna("4F8CFF").apply(lambda c: f"#{c.lstrip('#')}")
    return wins_df


def _empty_wins_figure(message):
    fig = px.bar()
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CHART_BG,
        font_color="#F4F4F5",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 15, "color": "#9CA3AF"},
            }
        ],
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


def _build_wins_figure(wins_df, season, constructor_filter):
    if wins_df is None:
        return _empty_wins_figure("Select a season to view race wins.")
    if wins_df.empty:
        label = constructor_filter if constructor_filter and constructor_filter != ALL_CONSTRUCTORS else "the selected filters"
        return _empty_wins_figure(f"No race wins found for {label}.")

    fig = px.bar(
        wins_df,
        x="Abbreviation",
        y="Wins",
        color="DisplayName",
        text="Wins",
        custom_data=["DisplayName", "TeamName"],
        color_discrete_sequence=wins_df["TeamColor"].tolist(),
    )
    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Team: %{customdata[1]}<br>Wins: %{y}<extra></extra>",
        textposition="outside",
        marker_line_width=0,
        showlegend=False,
    )
    fig.update_layout(
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CHART_BG,
        font_color="#F4F4F5",
        title={
            "text": f"Race wins by driver in {season}",
            "font": {"size": 18, "color": "#FFFFFF"},
        },
        xaxis_title="Driver",
        yaxis_title="Race Wins",
        yaxis={"dtick": 1, "gridcolor": "#2A2A40"},
        xaxis={"gridcolor": "#2A2A40"},
        margin={"l": 40, "r": 20, "t": 56, "b": 40},
    )
    return fig


def build_standings_cards(season):
    if not season:
        return html.Div(
            "Select a season to view standings.",
            style={"color": "#888", "textAlign": "center", "padding": "40px"},
        )

    driver_standings = _get_driver_standings_df(season)
    team_standings = _get_constructor_standings_df(season)
    if driver_standings is None or team_standings is None:
        return html.Div(
            f"No standings data available for {season}.",
            style={"color": "#888", "textAlign": "center", "padding": "40px"},
        )

    return html.Div(
        [
            driver_standings_card(driver_standings),
            _constructor_standings_card(team_standings),
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(320px, 1fr))",
            "gap": "16px",
            "alignItems": "start",
        },
    )


def build_single_standings_card(season, standings_type):
    if standings_type == "constructors":
        team_standings = _get_constructor_standings_df(season)
        if team_standings is None:
            return html.Div(
                f"No constructor standings data available for {season}.",
                style={"color": "#888", "textAlign": "center", "padding": "40px"},
            )
        return _constructor_standings_card(team_standings)

    driver_standings = _get_driver_standings_df(season)
    if driver_standings is None:
        return html.Div(
            f"No driver standings data available for {season}.",
            style={"color": "#888", "textAlign": "center", "padding": "40px"},
        )
    return driver_standings_card(driver_standings)


def _build_wins_summary(wins_df, constructor_filter):
    if wins_df is None:
        return "Select a season to analyse driver dominance."
    if wins_df.empty:
        if constructor_filter and constructor_filter != ALL_CONSTRUCTORS:
            return f"No wins found for {constructor_filter} in the selected season."
        return "No wins found for the selected season."

    top_wins = wins_df["Wins"].max()
    leaders = wins_df[wins_df["Wins"] == top_wins]
    leader_names = ", ".join(leaders["DisplayName"].tolist())
    constructor_text = (
        f" within {constructor_filter}"
        if constructor_filter and constructor_filter != ALL_CONSTRUCTORS
        else ""
    )
    noun = "driver" if len(leaders) == 1 else "drivers"
    verb = "leads" if len(leaders) == 1 else "lead"
    return f"{leader_names} {verb} this season{constructor_text} with {top_wins} race wins. This helps highlight driver dominance at a glance."


def build_standings_sections(season, include_summary=True, include_progression=True):
    if not season:
        return html.Div(
            "Please select a season from the filter above.",
            style={"color": "#888", "textAlign": "center", "padding": "40px"},
        )

    results_df = load_csv("race", f"race_results_{season}.csv")
    if results_df.empty:
        return html.Div(
            f"No results data available for {season}",
            style={"color": "#888", "textAlign": "center", "padding": "40px"},
        )

    driver_standings = _get_driver_standings_df(season)
    team_standings = _get_constructor_standings_df(season)

    sections = []
    if include_summary:
        sections.append(
            _season_summary_card(
                season,
                results_df["RoundNumber"].nunique(),
                len(driver_standings),
                len(team_standings),
            )
        )

    sections.append(driver_standings_card(driver_standings))
    sections.append(_constructor_standings_card(team_standings))
    sections.append(_wins_chart_card())

    if include_progression:
        sections.append(_points_progression_placeholder())

    return html.Div(sections)


layout = html.Div(
    [
        html.H1("Standings", style={"color": F1_RED, "fontSize": "22px"}),
        html.P(
            "Season standings and driver performance overview",
            style={"color": "#555", "fontSize": "12px", "marginBottom": "28px"},
        ),
        dcc.Dropdown(
            id="standings-season-dropdown",
            options=[{"label": str(season), "value": season} for season in seasons],
            value=seasons[0] if seasons else None,
            clearable=False,
            className="global-filter-dropdown",
            style={
                "maxWidth": "220px",
                "marginBottom": "20px",
                "backgroundColor": "#2A2A2D",
                "color": "#070707",
                "border": "1px solid #54545A",
                "borderRadius": "14px",
            },
        ),
        html.Div(id="standings-content"),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto"},
)


@callback(
    Output("standings-content", "children"),
    Input("standings-season-dropdown", "value"),
)
def update_standings_content(season):
    return build_standings_sections(season)


@callback(
    [Output("wins-constructor-dropdown", "options"), Output("wins-constructor-dropdown", "value")],
    Input("standings-season-dropdown", "value"),
    State("wins-constructor-dropdown", "value"),
)
def update_wins_constructor_options(season, current_constructor):
    options = _get_constructor_dropdown_options(season)
    valid_values = {option["value"] for option in options}
    next_value = current_constructor if current_constructor in valid_values else ALL_CONSTRUCTORS
    return options, next_value


@callback(
    [Output("wins-by-driver-summary", "children"), Output("wins-by-driver-chart", "figure")],
    [Input("standings-season-dropdown", "value"), Input("wins-constructor-dropdown", "value")],
)
def update_wins_chart(season, constructor_filter):
    wins_df = _get_wins_dataframe(season, constructor_filter)
    return _build_wins_summary(wins_df, constructor_filter), _build_wins_figure(
        wins_df, season, constructor_filter
    )
