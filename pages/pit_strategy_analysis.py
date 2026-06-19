from dash import html, dcc, callback, Input, Output
import plotly.express as px
import pandas as pd
import os
import glob
from data_loader import *


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── THEME COLORS ─────────────────────────────
BG_COLOR = "#0B0D17"
CARD_COLOR = "#121629"
GRID_COLOR = "#2A2D3E"
TEXT_COLOR = "#EAEAEA"
F1_RED = "#E10600"
ACCENT_BLUE = "#3A86FF"
ACCENT_ORANGE = "#FF9F1C"


def style_figure(fig):
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=CARD_COLOR,
        font=dict(color=TEXT_COLOR),
        title_font=dict(size=18, color=TEXT_COLOR),
        xaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "laps", "laps_*.csv")

files = glob.glob(DATA_PATH)

print("FILES FOUND:", files)

if not files:
    raise ValueError(f"No files found at {DATA_PATH}")

df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

# ─────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────

df["Year"] = df["Season"]
df["tyre_age"] = df["TyreLife"]

df["LapTime"] = pd.to_timedelta(df["LapTime"]).dt.total_seconds()

df["pit_event"] = df["PitInTime"].notna()
df["position_change"] = df.groupby("Driver")["Position"].diff()

df["strategy_type"] = "no_pit"
median_lap = df["LapNumber"].median()

df.loc[(df["pit_event"]) & (df["LapNumber"] <= median_lap), "strategy_type"] = "undercut"
df.loc[(df["pit_event"]) & (df["LapNumber"] > median_lap), "strategy_type"] = "overcut"


# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────
layout = html.Div([

    html.H2("Pit Strategy Analysis", style={
        "color": F1_RED,
        "marginBottom": "10px"
    }),

    html.P(
        "Undercut vs Overcut analysis with tyre degradation and race pace.",
        style={"color": TEXT_COLOR}
    ),

    # ── FILTERS ─────────────────────────────
    html.Div([
        dcc.Dropdown(
            id="year-filter",
            options=[{"label": y, "value": y} for y in sorted(df["Year"].unique())],
            value=sorted(df["Year"].unique())[0],
            clearable=False
        ),

        dcc.Dropdown(
            id="driver-filter",
            options=[{"label": d, "value": d} for d in df["Driver"].unique()],
            value=df["Driver"].unique()[0],
            clearable=False
        ),
    ], style={"marginBottom": "20px"}),

    # ── GRAPHS ─────────────────────────────
    html.Div([
        dcc.Graph(id="fig1"),
        dcc.Graph(id="fig2"),
        dcc.Graph(id="fig3"),
        dcc.Graph(id="fig4"),
        dcc.Graph(id="fig5"),
        dcc.Graph(id="fig6"),
    ], style={
        "backgroundColor": CARD_COLOR,
        "padding": "20px",
        "borderRadius": "12px"
    })

], style={
    "backgroundColor": BG_COLOR,
    "padding": "20px",
    "minHeight": "100vh"
})


# ─────────────────────────────────────────────
# CALLBACK
# ─────────────────────────────────────────────
@callback(
    [
        Output("fig1", "figure"),
        Output("fig2", "figure"),
        Output("fig3", "figure"),
        Output("fig4", "figure"),
        Output("fig5", "figure"),
        Output("fig6", "figure"),
    ],
    [
        Input("year-filter", "value"),
        Input("driver-filter", "value"),
    ]
)
def update_graphs(selected_year, selected_driver):

    # ── FILTER DATA ─────────────────────────
    filtered_df = df[
        (df["Year"] == selected_year) &
        (df["Driver"] == selected_driver)
    ]

    # ── GRAPH 1: TYRE DEGRADATION ───────────
    fig1 = px.line(
        filtered_df,
        x="TyreLife",
        y="LapTime",
        color="Compound",
        title="Tyre Degradation"
    )
    fig1 = style_figure(fig1)

    # ── GRAPH 2: STRATEGY PERFORMANCE ───────
    strategy_perf = filtered_df.groupby("strategy_type")["position_change"].mean().reset_index()

    fig2 = px.bar(
        strategy_perf,
        x="strategy_type",
        y="position_change",
        color="strategy_type",
        color_discrete_map={
            "undercut": F1_RED,
            "overcut": ACCENT_BLUE,
            "no_pit": "#888888"
        },
        title="Strategy Performance"
    )
    fig2 = style_figure(fig2)

    # ── GRAPH 3: POSITION CHANGE ────────────
    fig3 = px.scatter(
        filtered_df,
        x="LapNumber",
        y="position_change",
        color="strategy_type",
        title="Position Change After Pit"
    )
    fig3 = style_figure(fig3)

    # ── GRAPH 4: RACE PACE ──────────────────
    fig4 = px.box(
        filtered_df,
        x="Compound",
        y="LapTime",
        color="Compound",
        title="Race Pace Distribution"
    )
    fig4 = style_figure(fig4)

    # ── GRAPH 5: TYRE AGE VS PERFORMANCE ───
    fig5 = px.scatter(
        filtered_df,
        x="tyre_age",
        y="LapTime",
        color="Compound",
        trendline="ols",
        title="Tyre Age vs Performance"
    )
    fig5 = style_figure(fig5)

    # ── GRAPH 6: CORRELATION HEATMAP ───────
    corr_df = filtered_df[[
        "LapTime", "tyre_age", "LapNumber", "position_change"
    ]].corr()

    fig6 = px.imshow(
        corr_df,
        text_auto=True,
        title="Correlation Heatmap"
    )
    fig6 = style_figure(fig6)

    return fig1, fig2, fig3, fig4, fig5, fig6
