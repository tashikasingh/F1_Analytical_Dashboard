from dash import html

F1_RED = "#E10600"
CARD_BG = "#1A1A2E"


def table_header(columns):
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


def get_driver_standings_df(results_df):
    if results_df is None or results_df.empty:
        return None

    driver_standings = (
        results_df.groupby("Abbreviation")
        .agg({"Points": "sum", "BroadcastName": "first", "TeamName": "first", "TeamColor": "first"})
        .reset_index()
        .sort_values(["Points", "Abbreviation"], ascending=[False, True])
    )
    driver_standings["Position"] = range(1, len(driver_standings) + 1)
    driver_standings["DisplayName"] = driver_standings["BroadcastName"].fillna(
        driver_standings["Abbreviation"]
    )
    driver_standings["TeamColor"] = (
        driver_standings["TeamColor"].fillna("4F8CFF").apply(lambda c: f"#{str(c).lstrip('#')}")
    )
    return driver_standings


def driver_standings_card(driver_standings):
    return html.Div(
        [
            html.H4("Driver Championship", style={"color": "#FFFFFF", "marginBottom": "16px"}),
            html.Table(
                [
                    table_header(
                        [
                            ("Pos", "left"),
                            ("Driver", "left"),
                            ("Team", "left"),
                            ("Points", "right"),
                        ]
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(
                                        row["Position"],
                                        style={"padding": "10px", "color": "#FFFFFF", "fontWeight": "bold"},
                                    ),
                                    html.Td(row["Abbreviation"], style={"padding": "10px", "color": "#CCCCCC"}),
                                    html.Td(
                                        row["TeamName"],
                                        style={"padding": "10px", "color": "#999", "fontSize": "13px"},
                                    ),
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
                            for i, (_, row) in enumerate(driver_standings.head(20).iterrows())
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
