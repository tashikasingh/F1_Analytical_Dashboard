"""
Analysis Page 2 – Driver Performance Trend
===========================================
Answers : How has a driver's performance changed across seasons?
Purpose : Trend analysis with linear regression modelling
Charts  : Line chart (points per season + regression trend line)
          + Season Performance Overview bar chart (wins + podiums)
"""

from dash import html, dcc, callback, Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import glob
import os
from data_loader import *


# ── CONSTANTS ──────────────────────────────────────────────────────
F1_RED   = "#E10600"
CARD_BG  = "#1A1A2E"
BORDER   = "#2a2a40"
CHART_BG = "#15151E"

DD_STYLE = {
    "backgroundColor": "#1E1E2E",
    "color":           "#000",
    "border":          f"1px solid {BORDER}",
    "borderRadius":    "6px",
}

LABEL_STYLE = {
    "color":         "#888",
    "fontSize":      "11px",
    "textTransform": "uppercase",
    "letterSpacing": "1px",
    "marginBottom":  "6px",
    "display":       "block",
}

CARD_STYLE = {
    "background":   CARD_BG,
    "border":       f"1px solid {BORDER}",
    "borderRadius": "12px",
    "padding":      "20px",
    "marginBottom": "20px",
}

# Different marker shapes — FIX for same-team duplicate legend icons
MARKER_SYMBOLS = [
    "circle", "square", "diamond", "triangle-up",
    "triangle-down", "star", "hexagon", "cross",
    "pentagon", "bowtie", "hourglass", "asterisk"
]

# ── DATA LOADING ───────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "race")


def _load_all_results():
    files = glob.glob(os.path.join(DATA_DIR, "race_results_*.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    df["Points"]   = pd.to_numeric(df["Points"],   errors="coerce").fillna(0)
    df["Position"] = pd.to_numeric(df["Position"],  errors="coerce")
    df["Season"]   = pd.to_numeric(df["Season"],    errors="coerce")
    return df


_ALL_RESULTS = _load_all_results()


def _driver_options():
    if _ALL_RESULTS.empty:
        return []
    ds = _ALL_RESULTS.groupby("Abbreviation")["Season"].nunique()
    multi = ds[ds >= 2].index.tolist()
    name_map = (
        _ALL_RESULTS[_ALL_RESULTS["Abbreviation"].isin(multi)]
        .drop_duplicates("Abbreviation")[["Abbreviation", "FullName"]]
        .set_index("Abbreviation")["FullName"]
        .to_dict()
    )
    return sorted(
        [{"label": f"{name_map.get(a, a)} ({a})", "value": a} for a in multi],
        key=lambda x: x["label"],
    )


def _season_options():
    if _ALL_RESULTS.empty:
        return []
    seasons = sorted(_ALL_RESULTS["Season"].dropna().unique().astype(int))
    return [{"label": str(s), "value": s} for s in seasons]


def _get_team_color(df, abbreviation):
    sub = df[df["Abbreviation"] == abbreviation].sort_values("Season", ascending=False)
    if sub.empty or "TeamColor" not in sub.columns:
        return "#888888"
    raw = str(sub.iloc[0]["TeamColor"]).strip()
    if not raw or raw.lower() in ("nan", "none", ""):
        return "#888888"
    return f"#{raw.lstrip('#')}"


def _get_full_name(df, abbreviation):
    sub = df[df["Abbreviation"] == abbreviation]["FullName"].dropna()
    return sub.iloc[0] if not sub.empty else abbreviation


# ── EMPTY FIGURE ───────────────────────────────────────────────────
def _empty_fig(message="No data available"):
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(color="#888", size=14),
    )
    fig.update_layout(
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        height=420, margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


# ── CHART 1: POINTS LINE CHART + REGRESSION TREND ─────────────────
def _build_points_line_chart(df, drivers, from_year, to_year):
    if df.empty or not drivers:
        return _empty_fig("Select at least one driver to see the trend.")

    filtered = df[
        (df["Abbreviation"].isin(drivers)) &
        (df["Season"] >= from_year) &
        (df["Season"] <= to_year)
    ]
    if filtered.empty:
        return _empty_fig("No data for the selected filters.")

    season_pts = (
        filtered.groupby(["Abbreviation", "Season"])["Points"]
        .sum().reset_index()
        .rename(columns={"Points": "TotalPoints"})
    )

    fig = go.Figure()

    for i, driver in enumerate(drivers):
        d = season_pts[season_pts["Abbreviation"] == driver].sort_values("Season")
        if d.empty:
            continue

        color     = _get_team_color(df, driver)
        full_name = _get_full_name(df, driver)
        symbol    = MARKER_SYMBOLS[i % len(MARKER_SYMBOLS)]  # FIX 1: unique shape

        # Actual data line
        fig.add_trace(go.Scatter(
            x=d["Season"], y=d["TotalPoints"],
            mode="lines+markers",
            name=full_name,
            line=dict(color=color, width=2.5),
            marker=dict(size=9, color=color, symbol=symbol,
                        line=dict(color="#fff", width=1)),
            hovertemplate=(
                f"<b>{full_name}</b><br>"
                "Season: %{x}<br>Points: %{y}<extra></extra>"
            ),
        ))

        # FIX 2: Linear regression trend line
        if len(d) >= 2:
            x_vals = d["Season"].values
            y_vals = d["TotalPoints"].values
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            trend_y = slope * x_vals + intercept
            direction = "improving" if slope > 0 else "declining"

            fig.add_trace(go.Scatter(
                x=x_vals, y=trend_y,
                mode="lines",
                name=f"{full_name} trend ({direction})",
                line=dict(color=color, width=1.5, dash="dash"),
                opacity=0.55,
                hovertemplate=(
                    f"<b>{full_name} — Regression Trend</b><br>"
                    f"Slope: {slope:+.1f} pts/season<br>"
                    f"Performance: {direction}<extra></extra>"
                ),
            ))

    all_seasons = sorted(season_pts["Season"].unique().astype(int))
    fig.update_layout(
        title=dict(
            text="Championship Points per Season  <i>(dashed lines = linear regression trend)</i>",
            font=dict(color="#ffffff", size=16,
                      family="'Titillium Web', Arial, sans-serif"),
            x=0.5,
        ),
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        font=dict(color="#CCCCCC", family="'Titillium Web', Arial, sans-serif"),
        xaxis=dict(title="Season", tickvals=all_seasons,
                   ticktext=[str(s) for s in all_seasons],
                   gridcolor="#222230", griddash="dot",
                   tickfont=dict(color="#888", size=11)),
        yaxis=dict(title="Total Points", gridcolor="#222230",
                   griddash="dot", tickfont=dict(color="#888", size=11)),
        legend=dict(orientation="h", yanchor="top", y=-0.22,
                    xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#fff", size=11)),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1E1E2E", bordercolor="#444",
                        font=dict(color="#fff", size=12)),
        margin=dict(l=60, r=20, t=70, b=120),
        height=460,
    )
    return fig


# ── CHART 2: SEASON PERFORMANCE OVERVIEW (WINS + PODIUMS) ──────────
def _build_performance_overview_chart(df, drivers, from_year, to_year):
   
    if df.empty or not drivers:
        return _empty_fig("Select at least one driver.")

    filtered = df[
        (df["Abbreviation"].isin(drivers)) &
        (df["Season"] >= from_year) &
        (df["Season"] <= to_year)
    ]
    all_seasons = sorted(filtered["Season"].dropna().unique().astype(int))
    if not all_seasons:
        return _empty_fig("No data for the selected filters.")

    fig = go.Figure()

    for i, driver in enumerate(drivers):
        d         = filtered[filtered["Abbreviation"] == driver]
        color     = _get_team_color(df, driver)
        full_name = _get_full_name(df, driver)

        wins_s = (d[d["Position"] == 1].groupby("Season").size()
                  .reindex(all_seasons, fill_value=0).reset_index())
        wins_s.columns = ["Season", "Count"]

        podiums_s = (d[d["Position"] <= 3].groupby("Season").size()
                     .reindex(all_seasons, fill_value=0).reset_index())
        podiums_s.columns = ["Season", "Count"]

        fig.add_trace(go.Bar(
            x=wins_s["Season"], y=wins_s["Count"],
            name=f"{full_name} — Wins",
            marker=dict(color=color,
                        line=dict(color="rgba(255,255,255,0.2)", width=1)),
            hovertemplate=f"<b>{full_name}</b><br>Season: %{{x}}<br>Wins: %{{y}}<extra></extra>",
        ))

        fig.add_trace(go.Bar(
            x=podiums_s["Season"], y=podiums_s["Count"],
            name=f"{full_name} — Podiums",
            marker=dict(color=color, opacity=0.4,
                        pattern_shape="/",
                        line=dict(color="rgba(255,255,255,0.1)", width=1)),
            hovertemplate=f"<b>{full_name}</b><br>Season: %{{x}}<br>Podiums: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        barmode="group",
        title=dict(
            text="Season Performance Overview — Wins (solid) & Podiums (striped) per Season",
            font=dict(color="#ffffff", size=16,
                      family="'Titillium Web', Arial, sans-serif"),
            x=0.5,
        ),
        plot_bgcolor=CHART_BG, paper_bgcolor=CHART_BG,
        font=dict(color="#CCCCCC", family="'Titillium Web', Arial, sans-serif"),
        xaxis=dict(title="Season", tickvals=all_seasons,
                   ticktext=[str(s) for s in all_seasons],
                   gridcolor="#222230", tickfont=dict(color="#888", size=11)),
        yaxis=dict(title="Count", dtick=1, gridcolor="#222230",
                   griddash="dot", tickfont=dict(color="#888", size=11)),
        legend=dict(orientation="h", yanchor="top", y=-0.22,
                    xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#fff", size=11)),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1E1E2E", bordercolor="#444",
                        font=dict(color="#fff", size=12)),
        margin=dict(l=60, r=20, t=70, b=120),
        height=460, bargap=0.15, bargroupgap=0.05,
    )
    return fig


# ── SUMMARY STAT CARDS ─────────────────────────────────────────────
def _build_summary_stats(df, drivers, from_year, to_year):
    if df.empty or not drivers:
        return html.Div()

    filtered = df[
        (df["Abbreviation"].isin(drivers)) &
        (df["Season"] >= from_year) &
        (df["Season"] <= to_year)
    ]
    if filtered.empty:
        return html.Div()

    cards = []
    for driver in drivers:
        d = filtered[filtered["Abbreviation"] == driver]
        if d.empty:
            continue

        total_pts   = int(d["Points"].sum())
        total_wins  = int((d["Position"] == 1).sum())
        podiums     = int((d["Position"] <= 3).sum())
        best_season = d.groupby("Season")["Points"].sum().idxmax()

        # Regression-based trend insight shown in summary card
        season_pts = d.groupby("Season")["Points"].sum().reset_index()
        trend_text = "N/A"
        if len(season_pts) >= 2:
            slope, _ = np.polyfit(season_pts["Season"], season_pts["Points"], 1)
            if slope > 5:
                trend_text = f"📈 +{slope:.1f} pts/yr"
            elif slope < -5:
                trend_text = f"📉 {slope:.1f} pts/yr"
            else:
                trend_text = f"➡️ Stable ({slope:+.1f} pts/yr)"

        color     = _get_team_color(df, driver)
        full_name = _get_full_name(df, driver)

        cards.append(html.Div(
            style={
                "background":   "#15151E",
                "border":       f"1px solid {BORDER}",
                "borderLeft":   f"4px solid {color}",
                "borderRadius": "10px",
                "padding":      "14px 18px",
                "minWidth":     "200px",
                "flex":         "1",
            },
            children=[
                html.Div(full_name, style={
                    "color": color, "fontWeight": "700", "fontSize": "14px",
                    "marginBottom": "10px",
                    "fontFamily": "'Titillium Web', Arial, sans-serif",
                }),
                html.Div([html.Span("Points: ", style={"color": "#888", "fontSize": "12px"}),
                          html.Span(str(total_pts), style={"color": "#fff", "fontWeight": "700"})],
                         style={"marginBottom": "4px"}),
                html.Div([html.Span("Wins: ", style={"color": "#888", "fontSize": "12px"}),
                          html.Span(str(total_wins), style={"color": "#fff", "fontWeight": "700"})],
                         style={"marginBottom": "4px"}),
                html.Div([html.Span("Podiums: ", style={"color": "#888", "fontSize": "12px"}),
                          html.Span(str(podiums), style={"color": "#fff", "fontWeight": "700"})],
                         style={"marginBottom": "4px"}),
                html.Div([html.Span("Best Season: ", style={"color": "#888", "fontSize": "12px"}),
                          html.Span(str(best_season), style={"color": "#fff", "fontWeight": "700"})],
                         style={"marginBottom": "4px"}),
                html.Div([html.Span("Trend: ", style={"color": "#888", "fontSize": "12px"}),
                          html.Span(trend_text, style={"color": "#fff", "fontWeight": "700"})]),
            ]
        ))

    return html.Div(cards, style={"display": "flex", "flexWrap": "wrap", "gap": "12px"})


# ── LAYOUT ─────────────────────────────────────────────────────────
_driver_opts = _driver_options()
_season_opts = _season_options()
_all_seasons = [o["value"] for o in _season_opts]
_min_season  = min(_all_seasons) if _all_seasons else 2018
_max_season  = max(_all_seasons) if _all_seasons else 2025
_default_drivers = [d["value"] for d in _driver_opts if d["value"] in ("HAM", "VER", "NOR")]

layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto"},
    children=[

        html.H1("Driver Performance Trend", style={"color": F1_RED, "fontSize": "22px"}),
        html.P(
            "How has a driver's performance changed across seasons? "
            "Linear regression trend lines show whether a driver is improving or declining over time.",
            style={"color": "#555", "fontSize": "12px", "marginBottom": "28px"},
        ),

        # ── FILTERS ───────────────────────────────────────────────
        html.Div(
            style={"display": "flex", "gap": "20px", "marginBottom": "24px",
                   "flexWrap": "wrap", "alignItems": "flex-end"},
            children=[
                html.Div([
                    html.Label("Driver(s)", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="dpt-driver-dd", options=_driver_opts,
                        value=_default_drivers, multi=True,
                        placeholder="Select driver(s)…",
                        style={**DD_STYLE, "minWidth": "320px"},
                    ),
                ]),
                html.Div([
                    html.Label("From Season", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="dpt-from-year-dd", options=_season_opts,
                        value=_min_season, clearable=False,
                        style={**DD_STYLE, "width": "110px"},
                    ),
                ]),
                html.Div([
                    html.Label("To Season", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id="dpt-to-year-dd", options=_season_opts,
                        value=_max_season, clearable=False,
                        style={**DD_STYLE, "width": "110px"},
                    ),
                ]),
            ],
        ),

        # ── SUMMARY CARDS ─────────────────────────────────────────
        html.Div(style=CARD_STYLE, children=[
            html.H3("Summary", style={"color": "#FFFFFF", "fontSize": "16px",
                                      "marginBottom": "14px", "marginTop": "0"}),
            html.Div(id="dpt-summary-cards"),
        ]),

        # ── LINE CHART + REGRESSION ───────────────────────────────
        html.Div(style=CARD_STYLE, children=[
            dcc.Graph(id="dpt-points-line-chart", config={"displayModeBar": False}),
        ]),

        # ── PERFORMANCE OVERVIEW BAR CHART ────────────────────────
        html.Div(style=CARD_STYLE, children=[
            dcc.Graph(id="dpt-wins-bar-chart", config={"displayModeBar": False}),
        ]),
    ],
)


# ── CALLBACKS ──────────────────────────────────────────────────────
@callback(
    Output("dpt-points-line-chart", "figure"),
    Output("dpt-wins-bar-chart",    "figure"),
    Output("dpt-summary-cards",     "children"),
    Input("dpt-driver-dd",    "value"),
    Input("dpt-from-year-dd", "value"),
    Input("dpt-to-year-dd",   "value"),
)
def update_charts(drivers, from_year, to_year):
    if not from_year or not to_year:
        empty = _empty_fig("Select a season range.")
        return empty, empty, html.Div()
    if from_year > to_year:
        from_year, to_year = to_year, from_year
    drivers = drivers or []
    return (
        _build_points_line_chart(_ALL_RESULTS,          drivers, from_year, to_year),
        _build_performance_overview_chart(_ALL_RESULTS, drivers, from_year, to_year),
        _build_summary_stats(_ALL_RESULTS,              drivers, from_year, to_year),
    )
