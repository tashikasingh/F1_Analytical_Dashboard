def get_driver_toggle_button_style(n_clicks):
    active = n_clicks and n_clicks % 2 == 1
    return {
        "backgroundColor": "#1E1E2E" if active else "rgba(0,0,0,0)",
        "color": "#FFFFFF" if active else "#666",
        "border": "1px solid #555" if active else "1px solid #333",
        "borderRadius": "20px",
        "padding": "5px 14px",
        "fontSize": "12px",
        "fontFamily": "'Titillium Web', Arial, sans-serif",
        "fontWeight": "700",
        "cursor": "pointer",
        "letterSpacing": "1px",
    }
