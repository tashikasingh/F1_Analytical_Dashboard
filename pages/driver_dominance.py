import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


from data_loader import results_df, seasons

# Style tokens
F1_RED = "#E10600"
CARD_BG = "#1A1A2E"
BORDER = "#2A2A40"
CHART_BG = "#15151E"
DOMINANT_COLOR = "#F4D35E"
OBSERVED_COLOR = "#4C78A8"
EXPECTED_COLOR = "#FFFFFF"

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

NO_DATA_STYLE = {
    "background": CARD_BG,
    "border": f"1px dashed {BORDER}",
    "borderRadius": "12px",
    "padding": "42px 20px",
    "textAlign": "center",
    "color": "#9DA5B4",
    "fontSize": "14px",
}


def _empty_fig(message):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color="#9DA5B4", size=14),
    )
    fig.update_layout(
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color="#CCCCCC"),
        margin=dict(l=20, r=20, t=55, b=20),
        height=430,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def _poibin_pmf(probabilities):
    pmf = np.array([1.0], dtype=float)
    for p in probabilities:
        prob = float(np.clip(p, 1e-9, 1 - 1e-9))
        pmf = np.convolve(pmf, np.array([1.0 - prob, prob], dtype=float))

    pmf = np.maximum(pmf, 0.0)
    total = pmf.sum()
    if total <= 0:
        return np.array([1.0], dtype=float)
    return pmf / total


def _poibin_equal_tailed_ci(pmf, alpha=0.05):
    cdf = np.cumsum(pmf)
    lower = int(np.searchsorted(cdf, alpha / 2.0, side="left"))
    upper = int(np.searchsorted(cdf, 1.0 - alpha / 2.0, side="left"))
    upper = min(upper, len(pmf) - 1)
    return lower, upper


def _poibin_upper_tail_p_value(pmf, observed_wins):
    observed = int(observed_wins)
    if observed <= 0:
        return 1.0
    if observed >= len(pmf):
        return 0.0
    return float(np.clip(pmf[observed:].sum(), 0.0, 1.0))


def _coerce_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _filter_results_for_page(season, constructor):
    if results_df.empty or season is None:
        return pd.DataFrame()

    df = results_df.copy()
    df = _coerce_numeric(df, ["Season", "Position", "GridPosition"])

    filtered = df[df["Season"] == int(season)].copy()
    if constructor and constructor != "ALL":
        filtered = filtered[filtered["TeamName"] == constructor].copy()

    required = {"Abbreviation", "EventName", "Position", "GridPosition"}
    if filtered.empty or not required.issubset(filtered.columns):
        return pd.DataFrame()

    filtered = filtered.dropna(subset=["Abbreviation", "EventName"]).copy()
    filtered["DisplayName"] = filtered["FullName"].fillna(filtered["Abbreviation"])
    filtered["is_win"] = (filtered["Position"] == 1).astype(int)
    return filtered


def _normalize_probs_by_race(model_df, prob_col):
    normalized = model_df.copy()
    race_entries = normalized.groupby("EventName")["Abbreviation"].transform("count").clip(lower=1)
    fallback_p = 1.0 / race_entries

    raw_prob = pd.to_numeric(normalized[prob_col], errors="coerce")
    raw_prob = raw_prob.fillna(fallback_p).clip(lower=1e-9)
    race_prob_sum = raw_prob.groupby(normalized["EventName"]).transform("sum")

    normalized[prob_col] = np.where(race_prob_sum > 0, raw_prob / race_prob_sum, fallback_p)
    normalized[prob_col] = normalized[prob_col].clip(lower=1e-6, upper=1 - 1e-6)
    return normalized


def _build_logistic_pipeline():
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), ["GridPosition"]),
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["TeamName", "Abbreviation"]),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=3000,
                    class_weight=None,
                    solver="liblinear",
                    C=20.0,
                ),
            ),
        ]
    )


def _estimate_probs_logistic(model_df, training_df=None):
    if training_df is None:
        training_df = model_df

    scored_df = model_df.copy()
    scored_df["p_win"] = np.nan

    train_source = training_df.copy()
    valid_train_mask = (train_source["GridPosition"] > 0) & train_source["GridPosition"].notna()
    train_df = train_source.loc[valid_train_mask].copy()

    valid_eval_mask = (scored_df["GridPosition"] > 0) & scored_df["GridPosition"].notna()
    eval_df = scored_df.loc[valid_eval_mask].copy()
    if train_df.empty or eval_df.empty:
        return pd.Series(index=model_df.index, dtype=float)

    train_df["GridPosition"] = pd.to_numeric(train_df["GridPosition"], errors="coerce")
    eval_df["GridPosition"] = pd.to_numeric(eval_df["GridPosition"], errors="coerce")
    train_df = train_df.dropna(subset=["GridPosition"]).copy()
    eval_df = eval_df.dropna(subset=["GridPosition"]).copy()
    if train_df.empty or eval_df.empty or train_df["is_win"].nunique() < 2:
        return pd.Series(index=model_df.index, dtype=float)

    for col, fill_value in [("TeamName", "Unknown"), ("Abbreviation", "UNK"), ("EventName", "Unknown Event")]:
        train_df[col] = train_df[col].fillna(fill_value)
        eval_df[col] = eval_df[col].fillna(fill_value)

    features = ["GridPosition", "TeamName", "Abbreviation"]
    X_train = train_df[features]
    y_train = train_df["is_win"].astype(int).to_numpy()
    groups = train_df["EventName"].astype(str)

    pred_series = pd.Series(index=model_df.index, dtype=float)
    eval_index = eval_df.index
    same_sample_eval = eval_index.equals(train_df.index)

    can_use_oof = groups.nunique() >= 3 and same_sample_eval
    if can_use_oof:
        n_splits = min(5, groups.nunique())
        cv = GroupKFold(n_splits=n_splits)
        oof_probs = np.full(len(train_df), np.nan, dtype=float)

        for train_idx, val_idx in cv.split(X_train, y_train, groups):
            if np.unique(y_train[train_idx]).size < 2:
                continue
            fold_model = _build_logistic_pipeline()
            fold_model.fit(X_train.iloc[train_idx], y_train[train_idx])
            oof_probs[val_idx] = fold_model.predict_proba(X_train.iloc[val_idx])[:, 1]

        if np.isnan(oof_probs).any():
            full_model = _build_logistic_pipeline()
            full_model.fit(X_train, y_train)
            full_probs = full_model.predict_proba(X_train)[:, 1]
            oof_probs = np.where(np.isnan(oof_probs), full_probs, oof_probs)

        if not np.isnan(oof_probs).all():
            pred_series.loc[eval_index] = oof_probs

    if pred_series.loc[eval_index].isna().any():
        full_model = _build_logistic_pipeline()
        full_model.fit(X_train, y_train)
        pred_series.loc[eval_index] = full_model.predict_proba(eval_df[features])[:, 1]

    scored_df["p_win"] = pred_series
    scored_df = _normalize_probs_by_race(scored_df, "p_win")
    return scored_df["p_win"]


def _build_driver_summary(filtered_df, training_df=None):
    model_df = filtered_df.copy()

    if model_df.empty:
        return pd.DataFrame()

    if "p_win" not in model_df.columns:
        p_win = _estimate_probs_logistic(model_df, training_df=training_df)
        if p_win.empty or p_win.isna().all():
            return pd.DataFrame()
        model_df["p_win"] = pd.to_numeric(p_win, errors="coerce")
    else:
        model_df["p_win"] = pd.to_numeric(model_df["p_win"], errors="coerce")

    model_df["p_win"] = model_df["p_win"].clip(lower=1e-6, upper=1 - 1e-6)

    model_df = model_df.dropna(subset=["p_win"]).copy()
    if model_df.empty:
        return pd.DataFrame()

    summary_rows = []
    for (abbr, display_name), driver_rows in model_df.groupby(["Abbreviation", "DisplayName"]):
        probs = driver_rows["p_win"].to_numpy(dtype=float)
        if probs.size == 0:
            continue

        observed_wins = int(driver_rows["is_win"].sum())
        expected_wins = float(probs.sum())
        variance = float(np.sum(probs * (1.0 - probs)))

        pmf = _poibin_pmf(probs)
        ci_low, ci_high = _poibin_equal_tailed_ci(pmf, alpha=0.05)
        p_value = _poibin_upper_tail_p_value(pmf, observed_wins)

        summary_rows.append(
            {
                "Abbreviation": abbr,
                "DisplayName": display_name,
                "observed_wins": observed_wins,
                "expected_wins": expected_wins,
                "variance": variance,
                "races": int(driver_rows["EventName"].nunique()),
                "ci_low": float(ci_low),
                "ci_high": float(ci_high),
                "p_value": p_value,
            }
        )

    if not summary_rows:
        return pd.DataFrame()

    summary = pd.DataFrame(summary_rows)
    summary["std_dev"] = np.sqrt(summary["variance"].clip(lower=0))
    summary["dominant"] = (
        (summary["observed_wins"] > summary["expected_wins"])
        & (summary["p_value"] < 0.05)
    )

    summary = summary.sort_values(
        ["observed_wins", "expected_wins", "DisplayName"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return summary

def _chart_theme(fig, title):
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(color="#FFFFFF", size=16)),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color="#CCCCCC"),
        margin=dict(l=55, r=20, t=65, b=95),
        height=460,
        hoverlabel=dict(bgcolor="#1E1E2E", bordercolor="#444", font=dict(color="#FFF")),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FFF", size=11),
        ),
    )
    fig.update_xaxes(tickangle=-35, tickfont=dict(color="#AAB2C5", size=11), gridcolor="#222230")
    fig.update_yaxes(gridcolor="#222230", griddash="dot", zeroline=False)
    return fig




def _build_observed_vs_expected_chart(summary):
    if summary.empty:
        return _empty_fig("No observed vs expected values available for the selected filters.")

    drivers = summary["DisplayName"].tolist()
    color_map = np.where(summary["dominant"], DOMINANT_COLOR, OBSERVED_COLOR).tolist()

    custom_data = np.column_stack(
        [
            summary["observed_wins"],
            summary["expected_wins"],
            summary["ci_low"],
            summary["ci_high"],
            summary["p_value"],
        ]
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=drivers,
            y=summary["observed_wins"],
            name="Observed Wins",
            marker=dict(color=color_map, line=dict(color="#202433", width=1)),
            customdata=custom_data,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Observed Wins: %{customdata[0]:.0f}<br>"
                "Expected Wins: %{customdata[1]:.2f}<br>"
                "95% CI: [%{customdata[2]:.0f}, %{customdata[3]:.0f}]<br>"
                "p-value: %{customdata[4]:.4f}<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=drivers,
            y=summary["expected_wins"],
            mode="lines+markers",
            name="Expected Wins",
            line=dict(color=EXPECTED_COLOR, width=2),
            marker=dict(color=EXPECTED_COLOR, size=8),
            error_y=dict(
                type="data",
                symmetric=False,
                array=np.maximum(summary["ci_high"] - summary["expected_wins"], 0).tolist(),
                arrayminus=np.maximum(summary["expected_wins"] - summary["ci_low"], 0).tolist(),
                color=EXPECTED_COLOR,
                thickness=1.2,
                width=4,
            ),
            customdata=custom_data,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Observed Wins: %{customdata[0]:.0f}<br>"
                "Expected Wins: %{y:.2f}<br>"
                "Exact 95% CI: [%{customdata[2]:.0f}, %{customdata[3]:.0f}]<br>"
                "p-value: %{customdata[4]:.4f}<extra></extra>"
            ),
        )
    )

    dominant_rows = summary[summary["dominant"]]
    if not dominant_rows.empty:
        fig.add_trace(
            go.Scatter(
                x=dominant_rows["DisplayName"],
                y=dominant_rows["observed_wins"] + 0.2,
                mode="text",
                text=["SIG"] * len(dominant_rows),
                textposition="top center",
                textfont=dict(color=DOMINANT_COLOR, size=10),
                name="p < 0.05",
                hoverinfo="skip",
            )
        )

    fig = _chart_theme(fig, "Observed vs Expected Wins (Logistic Regression ML)")
    fig.update_xaxes(categoryorder="array", categoryarray=drivers)
    fig.update_yaxes(title="Wins", dtick=1)

    return fig


#  LAYOUT 
layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto"},
    children=[
        html.H1("Driver Dominance", style={"color": F1_RED, "fontSize": "22px"}),
        html.P(
            "This chart compares each driver's actual wins to expected wins estimated by a Logistic Regression model.",
            style={"color": "#555", "fontSize": "18px", "marginBottom": "28px"},
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
                html.Div(
                    [
                        html.Label("Season", style=LABEL_STYLE),
                        dcc.Dropdown(
                            id="dd-season-dd",
                            options=[{"label": str(s), "value": s} for s in seasons],
                            value=seasons[0] if seasons else None,
                            clearable=False,
                            style={**DD_STYLE, "width": "120px"},
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label("Constructor", style=LABEL_STYLE),
                        dcc.Dropdown(
                            id="dd-constructor-dd",
                            options=[{"label": "All Constructors", "value": "ALL"}],
                            value="ALL",
                            clearable=False,
                            style={**DD_STYLE, "minWidth": "260px"},
                        ),
                    ]
                ),
             
            ],
        ),
        html.Div(id="dd-charts-container"),
    ],
)


# CALLBACKS
@callback(
    Output("dd-constructor-dd", "options"),
    Output("dd-constructor-dd", "value"),
    Input("dd-season-dd", "value"),
)
def update_constructors(season):
    if season is None or results_df.empty:
        return [{"label": "All Constructors", "value": "ALL"}], "ALL"

    df = results_df.copy()
    df = _coerce_numeric(df, ["Season"])
    season_df = df[df["Season"] == int(season)]

    constructors = []
    if "TeamName" in season_df.columns:
        constructors = sorted([c for c in season_df["TeamName"].dropna().unique().tolist() if c])

    options = [{"label": "All Constructors", "value": "ALL"}] + [
        {"label": c, "value": c} for c in constructors
    ]
    return options, "ALL"


@callback(
    Output("dd-charts-container", "children"),
    Input("dd-season-dd", "value"),
    Input("dd-constructor-dd", "value"),
)
def render_charts(season, constructor):
    filtered_df = _filter_results_for_page(season, constructor)
    season_df = _filter_results_for_page(season, "ALL")

    if filtered_df.empty:
        return html.Div(
            "No data available for the selected season/constructor. "
            "Try a different filter combination.",
            style=NO_DATA_STYLE,
        )

    if season_df.empty:
        return html.Div(
            "No season-level data available to train the Logistic Regression model.",
            style=NO_DATA_STYLE,
        )

    season_probs = _estimate_probs_logistic(season_df, training_df=season_df)
    if season_probs.empty or season_probs.isna().all():
        return html.Div(
            "Could not compute Logistic Regression probabilities for this season.",
            style=NO_DATA_STYLE,
        )

    scored_filtered_df = filtered_df.copy()
    scored_filtered_df["p_win"] = season_probs.reindex(scored_filtered_df.index)

    summary = _build_driver_summary(scored_filtered_df)
    if summary.empty:
        return html.Div(
            "No valid modelling data available for this filter. "
            "Try another constructor or season.",
            style=NO_DATA_STYLE,
        )

    combo_fig = _build_observed_vs_expected_chart(summary)

    return [
        html.Div(
            style=CARD_STYLE,
            children=[
                dcc.Graph(
                    id="dd-observed-expected-chart",
                    figure=combo_fig,
                    config={"displayModeBar": False},
                )
            ],
        ),
    ]
