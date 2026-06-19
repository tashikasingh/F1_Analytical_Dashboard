import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats

# ── MAIN PLOT FUNCTION ────────────────────────────────────────────
def plot_grid_logistic_regression(results_df, top_n=3):
    """
    Create logistic regression plot showing probability of finishing 
    in top N positions based on grid position.

    Parameters
    ----------
    results_df : filtered or full results dataframe
    top_n : int - target finish position (default 3 for podium)
            common values: 3 (podium), 5, 10
    """
    if results_df is None or results_df.empty:
        return _empty_fig("No data available")

    df = results_df.copy()
    df["GridPosition"] = pd.to_numeric(df["GridPosition"], errors="coerce")
    df["Position"]     = pd.to_numeric(df["Position"],     errors="coerce")
    df = df[df["GridPosition"].notna() & df["Position"].notna()]
    df = df[(df["GridPosition"] > 0) & (df["Position"] > 0)]
    
    # Round grid positions to nearest integer
    df["GridPosition"] = df["GridPosition"].round().astype(int)

    if df.empty:
        return _empty_fig("No data available")

    # ── CREATE BINARY TARGET ──────────────────────────────────────
    df["TopFinish"] = (df["Position"] <= top_n).astype(int)

    # ── FIT LOGISTIC REGRESSION ───────────────────────────────────
    X = df["GridPosition"].values.reshape(-1, 1)
    y = df["TopFinish"].values

    # Check if we have enough variance in the data
    if len(np.unique(X)) < 2 or len(np.unique(y)) < 2:
        return _empty_fig("Insufficient data variation for analysis")

    try:
        model = LogisticRegression()
        model.fit(X, y)
    except Exception as e:
        return _empty_fig(f"Cannot fit model: {str(e)}")

    # ── GENERATE PREDICTION CURVE ─────────────────────────────────
    x_range = np.linspace(df["GridPosition"].min(), 
                          df["GridPosition"].max(), 300)
    X_range = x_range.reshape(-1, 1)
    y_pred = model.predict_proba(X_range)[:, 1]
    
    # Compute standard errors
    y_pred_train = model.predict_proba(X)[:, 1]
    residuals = y - y_pred_train
    n_samples = len(X)
    
    # Simplified CI calculation
    std_error = np.sqrt(np.var(residuals) / n_samples)
    ci_range = 1.96 * std_error
    
    y_upper = np.clip(y_pred + ci_range, 0, 1)
    y_lower = np.clip(y_pred - ci_range, 0, 1)

    # ── CALCULATE ACTUAL PROBABILITIES BY GRID POSITION ───────────
    grid_probs = df.groupby("GridPosition").agg(
        TopFinishes=("TopFinish", "sum"),
        TotalRaces=("TopFinish", "count"),
    ).reset_index()
    grid_probs["Probability"] = (grid_probs["TopFinishes"] / 
                                  grid_probs["TotalRaces"])

    # ── CREATE FIGURE ─────────────────────────────────────────────
    fig = go.Figure()

    # Add confidence interval band
    fig.add_trace(go.Scatter(
        x=x_range,
        y=y_upper,
        fill=None,
        mode='lines',
        name='95% CI Upper',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=x_range,
        y=y_lower,
        fill='tonexty',
        mode='lines',
        name='95% Confidence Interval',
        line=dict(width=0),
        fillcolor='rgba(0, 100, 200, 0.2)',
        hoverinfo='skip',
        showlegend=False,
    ))

    # Add logistic regression curve
    fig.add_trace(go.Scatter(
        x=x_range,
        y=y_pred,
        mode='lines',
        name='Logistic Fit',
        line=dict(color='#E10600', width=3),
        hovertemplate=f'<b>Grid Position: %{{x:.0f}}</b><br>Top {top_n} Probability: %{{y:.1%}}<extra></extra>',
    ))

    # Add actual data points (observed probabilities)
    fig.add_trace(go.Scatter(
        x=grid_probs["GridPosition"].astype(int),
        y=grid_probs["Probability"],
        mode='markers',
        name='Observed',
        marker=dict(
            size=8,
            color=['#FFD700'] * len(grid_probs),
            line=dict(color='rgba(255, 255, 255, 0.9)', width=2),
            opacity=1.0,
        ),
        text=[f"Grid {int(g)}<br>Top {top_n}: {p:.0%}<br>Races: {r}"
              for g, p, r in zip(grid_probs["GridPosition"],
                                grid_probs["Probability"],
                                grid_probs["TotalRaces"])],
        hovertemplate='%{text}<extra></extra>',
    ))

    # Update layout
    fig.update_layout(
        title=f"Logistic Regression: Probability of Top {top_n} Finish by Grid Position",
        xaxis_title="Starting Grid Position",
        yaxis_title=f"Probability of Finishing Top {top_n}",
        hovermode='x unified',
        plot_bgcolor="#1A1A2E",
        paper_bgcolor="#0F0F1E",
        font=dict(size=12, family="Arial", color="#FFF"),
        margin=dict(l=60, r=20, t=80, b=60),
        height=500,
        xaxis=dict(
            zeroline=False,
            showgrid=True,
            gridwidth=1,
            gridcolor="#333",
            tickmode="linear",
            tick0=1,
            dtick=1,
            range=[0.5, 20.5],
            tickformat=".0f",
        ),
        yaxis=dict(
            zeroline=False,
            showgrid=True,
            gridwidth=1,
            gridcolor="#333",
            tickformat=".0%",
        ),
    )

    return fig


def _empty_fig(message):
    """Return an empty figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#888"),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="#1A1A2E",
        paper_bgcolor="#0F0F1E",
    )
    return fig
