import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

# ── CONSTANTS ─────────────────────────────────────────────────────
TEAM_COLORS = {
    "Red Bull Racing":  "#3671C6",
    "Ferrari":          "#E8002D",
    "Mercedes":         "#27F4D2",
    "McLaren":          "#FF8000",
    "Aston Martin":     "#229971",
    "Alpine":           "#FF87BC",
    "Williams":         "#64C4FF",
    "RB":               "#6692FF",
    "Haas F1 Team":     "#B6BABD",
    "Kick Sauber":      "#52E252",
}

# ── HELPERS ───────────────────────────────────────────────────────
def _parse_to_seconds(val):
    try:
        if pd.isna(val): return None
        val = str(val)
        if "days" in val:
            val = val.split("days")[-1].strip()
        parts = val.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
    except:
        return None

def _fmt(sec):
    if sec is None or pd.isna(sec): return "N/A"
    m = int(sec // 60)
    s = sec % 60
    return f"{m:02d}:{s:06.3f}"

def _btn_style(active, color="#888888"):
    return {
        "backgroundColor": "#1E1E2E"        if active else "rgba(0,0,0,0)",
        "color":           "#FFFFFF"         if active else "#666",
        "border":          "1px solid #555" if active else "1px solid #333",
        "borderRadius":    "20px",
        "padding":         "5px 14px",
        "fontSize":        "12px",
        "fontFamily":      "'Titillium Web', Arial, sans-serif",
        "fontWeight":      "700",
        "cursor":          "pointer",
        "letterSpacing":   "1px",
    }

# ── DRIVER TOGGLE LAYOUT ──────────────────────────────────────────
def lap_times_layout(df, results_df, session_type, color_map=None):
    color_map   = color_map or {}

    # ── sort drivers by finish position ──
    if not results_df.empty and "Abbreviation" in results_df.columns:
        results_df = results_df.copy()
        results_df["Position"] = pd.to_numeric(results_df["Position"], errors="coerce")
        ordered = results_df.sort_values("Position")["Abbreviation"].dropna().tolist()
        # only keep drivers that are in the laps data
        available = set(df["Driver"].dropna().unique())
        all_drivers = [d for d in ordered if d in available]
        # append any drivers not in results (e.g. DNFs missing from results)
        all_drivers += sorted([d for d in available if d not in all_drivers])
    else:
        all_drivers = sorted(df["Driver"].dropna().unique().tolist())

    top3 = all_drivers[:3]

    toggle_buttons = [
        html.Button(
            driver,
            id={"type": "driver-btn", "index": driver},
            n_clicks=1 if driver in top3 else 0,
            style=_btn_style(
                active=driver in top3,
                color=color_map.get(driver, "#888888")
            )
        )
        for driver in all_drivers
    ]

    return html.Div([
        dcc.Graph(id="lap-chart", config={"displayModeBar": False}),
        html.Div(
            toggle_buttons,
            id="driver-toggles",
            style={
                "display":        "flex",
                "flexWrap":       "wrap",
                "gap":            "8px",
                "justifyContent": "center",
                "padding":        "12px 16px 4px 16px",
            }
        )
    ])

# ── MAIN PLOT FUNCTION ────────────────────────────────────────────
def plot_lap_times(df, session_type, selected_drivers=None, color_map=None):
    """
    Returns a Plotly figure of lap times.

    Parameters
    ----------
    df               : filtered laps dataframe (already filtered by season, race, session)
    session_type     : "Race" or "Qualifying"
    selected_drivers : list of driver abbreviations to plot
    """
    if df is None or df.empty:
        return _empty_fig("No data available")

    df = df.copy()
    df["LapTimeSec"] = df["LapTime"].apply(_parse_to_seconds)
    df = df[df["LapTimeSec"].notna()]
    # df = df[df["LapTimeSec"].notna() & df["LapTimeSec"].between(60, 300)]

    # if session_type == "Race":
    #     df = df[df["PitInTime"].isna() & df["PitOutTime"].isna()]

    if df.empty:
        return _empty_fig("No lap data found")

    if selected_drivers:
        df = df[df["Driver"].isin(selected_drivers)]

    if df.empty:
        return _empty_fig("No data for selected drivers")

    y_min     = df["LapTimeSec"].min()
    y_max     = df["LapTimeSec"].max()
    tick_vals = [y_min + i * 5 for i in range(int((y_max - y_min) / 5) + 2)]
    tick_text = [_fmt(v) for v in tick_vals]

    fig = go.Figure()

    seen_colors = {}  # track colours already used

    for driver in selected_drivers or sorted(df["Driver"].dropna().unique()):
        d     = df[df["Driver"] == driver].sort_values("LapNumber")
        if d.empty: continue

        color = color_map.get(driver, "#888888")

        # ── If teammate has same colour, use dashed line ──────────────
        dash  = "dash" if color in seen_colors else "solid"
        seen_colors[color] = driver

        fig.add_trace(go.Scatter(
            x=d["LapNumber"],
            y=d["LapTimeSec"],
            mode="lines+markers",
            name=driver,
            line=dict(color=color, width=2, dash=dash),
            marker=dict(size=6, color=color, symbol="circle"),
            hovertemplate=(
                f"<b>Lap: %{{x}}</b><br>"
                f"<span style='color:{color}'>⬤</span> "
                f"%{{customdata[0]}} · {driver}"
                "<extra></extra>"
            ),
            customdata=list(zip(
                d["LapTime"].apply(lambda x: _fmt(_parse_to_seconds(x)))
            ))
        ))

    fig.update_layout(
        title=dict(
            text="Lap Times",
            font=dict(color="#ffffff", size=20,
                      family="'Titillium Web', Arial, sans-serif"),
            x=0.5,
            pad=dict(t=10)
        ),
        plot_bgcolor="#15151E",
        paper_bgcolor="#15151E",
        font=dict(color="#CCCCCC",
                  family="'Titillium Web', Arial, sans-serif"),
        xaxis=dict(
            title=None,
            gridcolor="#222230",
            gridwidth=1,
            griddash="dot",
            zerolinecolor="#333",
            tickfont=dict(color="#888", size=11),
            showline=False,
        ),
        yaxis=dict(
            title=None,
            gridcolor="#222230",
            gridwidth=1,
            griddash="dot",
            tickvals=tick_vals,
            ticktext=tick_text,
            tickfont=dict(color="#888", size=11),
            showline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#fff", size=11),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1E1E2E",
            bordercolor="#444",
            font=dict(color="#fff", size=12)
        ),
        margin=dict(l=70, r=20, t=60, b=80),
        height=500,
    )

    return fig

# ── EMPTY FIGURE ──────────────────────────────────────────────────
def _empty_fig(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(color="#888", size=14)
    )
    fig.update_layout(
        plot_bgcolor="#15151E",
        paper_bgcolor="#15151E",
        height=500
    )
    return fig