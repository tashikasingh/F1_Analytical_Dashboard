from dash import html, dcc, callback, Input, Output
import pandas as pd
import glob
import plotly.express as px

# ─────────────────────────────
# LOAD DATA (SAFE)
# ─────────────────────────────
files = glob.glob("data/race/race_*.csv")

if len(files) == 0:
    raise Exception("No race files found in data/race")

df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

df.columns = df.columns.str.strip()
df["position_change"] = df["GridPosition"] - df["Position"]

# ─────────────────────────────
# LAYOUT (IMPORTANT: MUST EXIST)
# ─────────────────────────────
layout = html.Div([

    html.H2("Position Analysis"),

    dcc.Dropdown(
        id="position-year",
        options=[{"label": y, "value": y} for y in sorted(df["Season"].unique())],
        value=max(df["Season"].unique())
    ),

    dcc.Graph(id="position-team"),
    dcc.Graph(id="position-driver")

])

# ─────────────────────────────
# CALLBACK
# ─────────────────────────────
@callback(
    Output("position-team", "figure"),
    Output("position-driver", "figure"),
    Input("position-year", "value")
)
def update(year):

    data = df[df["Season"] == year]

    team_df = data.groupby("TeamName")["position_change"].mean().reset_index()

    fig1 = px.bar(team_df, x="TeamName", y="position_change", template="plotly_dark")

    driver_df = data.groupby("FullName")["position_change"].mean().reset_index()

    fig2 = px.bar(driver_df, x="FullName", y="position_change", template="plotly_dark")

    return fig1, fig2