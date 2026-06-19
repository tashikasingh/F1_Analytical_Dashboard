import pandas as pd
import plotly.graph_objects as go


TYRE_COLORS = {
    "SOFT": "#ff0050",
    "MEDIUM": "#fff200",
    "HARD": "#ffffff",
    "INTER": "#22c55e",
    "INTERMEDIATE": "#22c55e",
    "WET": "#00aaff",
}


def plot_position_changes(
    df,
    color_map=None,
    selected_drivers=None,
    show_group="top10",
):
    color_map = color_map or {}

    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            title="No position data available",
            paper_bgcolor="#12121c",
            plot_bgcolor="#12121c",
        )
        return fig

    data = df.copy()

    required_cols = {"Driver", "LapNumber", "Position"}
    missing = required_cols - set(data.columns)
    if missing:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            title=f"Missing columns: {', '.join(missing)}",
            paper_bgcolor="#12121c",
            plot_bgcolor="#12121c",
        )
        return fig

    data = data.dropna(subset=["Driver", "LapNumber", "Position"])
    data["LapNumber"] = pd.to_numeric(data["LapNumber"], errors="coerce")
    data["Position"] = pd.to_numeric(data["Position"], errors="coerce")
    data = data.dropna(subset=["LapNumber", "Position"])

    final_pos = (
        data.sort_values("LapNumber")
        .groupby("Driver")["Position"]
        .last()
        .sort_values()
    )

    if selected_drivers:
        drivers = selected_drivers
        title_suffix = "Highlighted Drivers"
    elif show_group == "bottom10":
        drivers = final_pos.tail(10).index.tolist()
        title_suffix = "Bottom 10"
    else:
        drivers = final_pos.head(10).index.tolist()
        title_suffix = "Top 10"

    plot_df = data[data["Driver"].isin(drivers)].copy()

    fig = go.Figure()
    max_lap = plot_df["LapNumber"].max()

    for i, driver in enumerate(drivers):
        driver_df = plot_df[plot_df["Driver"] == driver].sort_values("LapNumber")

        if driver_df.empty:
            continue

        color = color_map.get(driver, None)

        dash_style = "dot" if selected_drivers else "solid"

        fig.add_trace(
            go.Scatter(
                x=driver_df["LapNumber"],
                y=driver_df["Position"],
                mode="lines",
                name=driver,
                line=dict(
                    width=3,
                    color=color,
                    shape="spline",
                    dash=dash_style,
                ),
                hovertemplate=(
                    f"<b>{driver}</b><br>"
                    "Lap: %{x}<br>"
                    "Position: P%{y}<extra></extra>"
                ),
            )
        )

        first = driver_df.iloc[0]

        # Left-side starting position label only
        fig.add_annotation(
            x=first["LapNumber"],
            y=first["Position"],
            text=f"P{int(first['Position'])}  <b>{driver}</b>",
            showarrow=False,
            xanchor="right",
            xshift=-8,
            font=dict(size=11, color=color or "white"),
        )

        # Pit stop detection
        if "PitInTime" in driver_df.columns:
            pit_df = driver_df[driver_df["PitInTime"].notna()]
        elif "pit_event" in driver_df.columns:
            pit_df = driver_df[driver_df["pit_event"] == True]
        else:
            pit_df = pd.DataFrame()

        if not pit_df.empty:
            marker_color = color

            tyre_col = None
            for col in ["Compound", "Tyre", "tyre", "compound"]:
                if col in pit_df.columns:
                    tyre_col = col
                    break

            if tyre_col:
                marker_color = [
                    TYRE_COLORS.get(str(t).upper(), color)
                    for t in pit_df[tyre_col]
                ]

            fig.add_trace(
                go.Scatter(
                    x=pit_df["LapNumber"],
                    y=pit_df["Position"],
                    mode="markers",
                    name=f"{driver} pit",
                    showlegend=False,
                    marker=dict(
                        size=10,
                        color=marker_color,
                        line=dict(width=2, color="#00ff99"),
                    ),
                    hovertemplate=(
                        f"<b>{driver} Pit Stop</b><br>"
                        "Lap: %{x}<br>"
                        "Position: P%{y}<extra></extra>"
                    ),
                )
            )

    # Tyre key inside graph
    tyre_x = max_lap - 2
    tyre_start_y = 17.7

    fig.add_trace(
        go.Scatter(
            x=[tyre_x],
            y=[tyre_start_y],
            mode="markers+text",
            marker=dict(size=9, color="#777"),
            text=["Pit Stop Tyres:"],
            textposition="middle right",
            name="Pit Stop Tyres:",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    tyre_labels = [
        ("SOFT", "#ff0050"),
        ("MEDIUM", "#fff200"),
        ("HARD", "#ffffff"),
        ("INTER", "#22c55e"),
    ]

    for idx, (label, col) in enumerate(tyre_labels):
        fig.add_trace(
            go.Scatter(
                x=[tyre_x],
                y=[tyre_start_y + 1 + idx],
                mode="markers+text",
                marker=dict(size=9, color=col),
                text=[label],
                textposition="middle right",
                textfont=dict(color=col, size=11),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.update_yaxes(
        autorange="reversed",
        title="Position",
        tickmode="array",
        tickvals=list(range(1, 21)),
        ticktext=[f"P{i}" for i in range(1, 21)],
        range=[20.5, 0.5],
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
    )

    fig.update_xaxes(
        title="Lap Number",
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
    )

    fig.update_layout(
        title=dict(
            text=(
                f"Race Position Changes — {title_suffix} "
                "<sup><i>(coloured dots = pit stops)</i></sup>"
            ),
            x=0.5,
            font=dict(size=20),
        ),
        template="plotly_dark",
        height=700,
        paper_bgcolor="#12121c",
        plot_bgcolor="#12121c",
        font=dict(color="#FFFFFF"),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.17,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
            itemwidth=40,
        ),
        margin=dict(l=110, r=60, t=80, b=120),
    )

    return fig