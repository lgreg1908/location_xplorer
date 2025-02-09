import dash
from dash import dcc, html, Input, Output, callback_context, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Load your CSV data.
df = pd.read_csv("data/final_data.csv")

# List of continuous variables available for the scatter plot axes.
cont_vars = [
    'median_household_income', 'population', 'median_age', 'intersection_density',
    'population_density', 'pct_bachelor', 'median_sale_price'
]

# Create a unique town key as "state_name, town" for town selection.
df["town_key"] = df["state_name"] + ", " + df["town"]

# Create the Dash app.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)
app.title = "Location Explorer"

# Common style for small input boxes.
small_input_style = {"width": "60px", "fontSize": "12px"}

# ------------------------------------------------------------------
# Dashboard Tab Content
# ------------------------------------------------------------------
dashboard_content = html.Div([
    # Header and About Metrics modal (shared on all tabs)
    html.H1("Business Location Explorer", style={"textAlign": "center", "marginTop": "20px", "marginBottom": "10px"}),
    html.Div([
        html.A("About the Metrics", id="open-about", href="#",
               style={"cursor": "pointer", "textDecoration": "underline", "color": "#007bff"})
    ], style={"textAlign": "center", "marginBottom": "20px"}),
    dbc.Modal(
        [
            dbc.ModalHeader("About the Metrics"),
            dbc.ModalBody(
                dcc.Markdown("""
**Composite Score**  
This metric is computed using Principal Component Analysis (PCA) on several continuous variables. The process involves:  
1. **Adjustments:** Each variable is adjusted by a specific factor.  
2. **Standardization:** The adjusted values are standardized.  
3. **PCA:** The first principal component is extracted.  
4. **Scaling:** The component is scaled to a range of 0–100.

**Intersection Density and Area**  
Derived from the walking network of a location:  
- The number of intersections (nodes) is counted.  
- The area is computed from the convex hull of these intersections (converted to square kilometers).

**Percentage with Bachelor’s Degree**  
Calculated as the proportion of the population over 25 years old with a bachelor’s degree.

**Data Sources and Imputation**  
- **Census Data:** Sourced from the 2021 Census for variables such as population and median age.  
- **Median Sale Price:** Obtained from Redfin at the county level.  
- **Data Integration:** OpenAI was used to impute county data for joining census and real estate datasets.  
- **House Price Imputation:** Missing house prices were imputed using random forest regression (R² = 0.62 on test data).
                """)
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-about", className="ml-auto")
            ),
        ],
        id="modal-about",
        is_open=False,
        centered=True,
    ),

    # Row 1: Town Detail Section with Info Tooltip and Add Town Button
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H2("Town Detail", style={"textAlign": "center", "display": "inline-block"}),
                html.Span("ℹ️", id="town-detail-info", style={"cursor": "pointer", "marginLeft": "5px", "fontSize": "18px"})
            ]),
            dcc.Graph(id="town-detail-chart", config={"displayModeBar": False}, style={"height": "400px"}),
            dbc.Button("Clear Town Selection", id="clear-town-button", color="secondary", className="mt-2"),
            dbc.Button("Add Town to List", id="add-town-button", color="primary", className="mt-2", style={"marginLeft": "10px"})
        ], width=12)
    ], id="town-detail-container", style={"display": "none", "marginBottom": "40px"}),
    dbc.Tooltip(
        "This section shows detailed normalized metrics for the town you select from one of the charts below.",
        target="town-detail-info",
        placement="right"
    ),

    # Stores for selected town and town list.
    dcc.Store(id="selected-town-store", data=None),
    dcc.Store(id="town-list-store", data=[]),

    # Row 2: Basic Filters (County, State, Population)
    dbc.Row([
        dbc.Col([
            html.Label("County Filter"),
            dcc.Dropdown(
                id="county-filter",
                options=[{"label": c, "value": c} for c in sorted(df["county"].unique())],
                multi=True,
                placeholder="Select county(ies)"
            )
        ], width=3),
        dbc.Col([
            html.Label("State Filter"),
            dcc.Dropdown(
                id="state-filter",
                options=[{"label": s, "value": s} for s in sorted(df["state_name"].unique())],
                multi=True,
                placeholder="Select state(s)"
            )
        ], width=3),
        dbc.Col([
            html.Label("Population Filter"),
            html.Div([
                dcc.Input(
                    id="population-min-input",
                    type="number",
                    placeholder="Min",
                    value=int(df["population"].min()),
                    debounce=True,
                    style=small_input_style
                ),
                html.Div(
                    dcc.RangeSlider(
                        id="population-slider",
                        min=int(df["population"].min()),
                        max=int(df["population"].max()),
                        step=1000,
                        value=[int(df["population"].min()), int(df["population"].max())],
                        marks={
                            int(df["population"].min()): str(int(df["population"].min())),
                            int((df["population"].min() + df["population"].max()) / 2): str(int((df["population"].min() + df["population"].max()) / 2)),
                            int(df["population"].max()): str(int(df["population"].max()))
                        },
                        tooltip={"always_visible": True, "placement": "bottom"}
                    ),
                    style={"flex": "1", "margin": "0 10px"}
                ),
                dcc.Input(
                    id="population-max-input",
                    type="number",
                    placeholder="Max",
                    value=int(df["population"].max()),
                    debounce=True,
                    style=small_input_style
                )
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], width=6)
    ], style={"marginBottom": "20px"}),

    # Row 3: Additional Filters (Age, Pct Bachelor, Income, House Price)
    dbc.Row([
        dbc.Col([
            html.Label("Age Filter"),
            html.Div([
                dcc.Input(
                    id="age-min-input",
                    type="number",
                    placeholder="Min",
                    value=int(df["median_age"].min()),
                    debounce=True,
                    style=small_input_style
                ),
                html.Div(
                    dcc.RangeSlider(
                        id="age-slider",
                        min=int(df["median_age"].min()),
                        max=int(df["median_age"].max()),
                        step=1,
                        value=[int(df["median_age"].min()), int(df["median_age"].max())],
                        marks={
                            int(df["median_age"].min()): str(int(df["median_age"].min())),
                            int((df["median_age"].min() + df["median_age"].max()) / 2): str(int((df["median_age"].min() + df["median_age"].max()) / 2)),
                            int(df["median_age"].max()): str(int(df["median_age"].max()))
                        },
                        tooltip={"always_visible": True, "placement": "bottom"}
                    ),
                    style={"flex": "1", "margin": "0 10px"}
                ),
                dcc.Input(
                    id="age-max-input",
                    type="number",
                    placeholder="Max",
                    value=int(df["median_age"].max()),
                    debounce=True,
                    style=small_input_style
                )
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], width=3),
        dbc.Col([
            html.Label("Pct Bachelor Filter"),
            html.Div([
                dcc.Input(
                    id="bachelor-min-input",
                    type="number",
                    placeholder="Min",
                    value=df["pct_bachelor"].min(),
                    debounce=True,
                    style=small_input_style
                ),
                html.Div(
                    dcc.RangeSlider(
                        id="bachelor-slider",
                        min=df["pct_bachelor"].min(),
                        max=df["pct_bachelor"].max(),
                        step=0.01,
                        value=[df["pct_bachelor"].min(), df["pct_bachelor"].max()],
                        marks={
                            round(df["pct_bachelor"].min(), 2): str(round(df["pct_bachelor"].min(), 2)),
                            round((df["pct_bachelor"].min() + df["pct_bachelor"].max()) / 2, 2): str(round((df["pct_bachelor"].min() + df["pct_bachelor"].max()) / 2, 2)),
                            round(df["pct_bachelor"].max(), 2): str(round(df["pct_bachelor"].max(), 2))
                        },
                        tooltip={"always_visible": True, "placement": "bottom"}
                    ),
                    style={"flex": "1", "margin": "0 10px"}
                ),
                dcc.Input(
                    id="bachelor-max-input",
                    type="number",
                    placeholder="Max",
                    value=df["pct_bachelor"].max(),
                    debounce=True,
                    style=small_input_style
                )
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], width=3),
        dbc.Col([
            html.Label("Income Filter"),
            html.Div([
                dcc.Input(
                    id="income-min-input",
                    type="number",
                    placeholder="Min",
                    value=int(df["median_household_income"].min()),
                    debounce=True,
                    style=small_input_style
                ),
                html.Div(
                    dcc.RangeSlider(
                        id="income-slider",
                        min=int(df["median_household_income"].min()),
                        max=int(df["median_household_income"].max()),
                        step=1000,
                        value=[int(df["median_household_income"].min()), int(df["median_household_income"].max())],
                        marks={
                            int(df["median_household_income"].min()): str(int(df["median_household_income"].min())),
                            int((df["median_household_income"].min() + df["median_household_income"].max()) / 2): str(int((df["median_household_income"].min() + df["median_household_income"].max()) / 2)),
                            int(df["median_household_income"].max()): str(int(df["median_household_income"].max()))
                        },
                        tooltip={"always_visible": True, "placement": "bottom"}
                    ),
                    style={"flex": "1", "margin": "0 10px"}
                ),
                dcc.Input(
                    id="income-max-input",
                    type="number",
                    placeholder="Max",
                    value=int(df["median_household_income"].max()),
                    debounce=True,
                    style=small_input_style
                )
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], width=3),
        dbc.Col([
            html.Label("House Price Filter"),
            html.Div([
                dcc.Input(
                    id="houseprice-min-input",
                    type="number",
                    placeholder="Min",
                    value=int(df["median_sale_price"].min()),
                    debounce=True,
                    style=small_input_style
                ),
                html.Div(
                    dcc.RangeSlider(
                        id="houseprice-slider",
                        min=int(df["median_sale_price"].min()),
                        max=int(df["median_sale_price"].max()),
                        step=1000,
                        value=[int(df["median_sale_price"].min()), int(df["median_sale_price"].max())],
                        marks={
                            int(df["median_sale_price"].min()): str(int(df["median_sale_price"].min())),
                            int((df["median_sale_price"].min() + df["median_sale_price"].max()) / 2): str(int((df["median_sale_price"].min() + df["median_sale_price"].max()) / 2)),
                            int(df["median_sale_price"].max()): str(int(df["median_sale_price"].max()))
                        },
                        tooltip={"always_visible": True, "placement": "bottom"}
                    ),
                    style={"flex": "1", "margin": "0 10px"}
                ),
                dcc.Input(
                    id="houseprice-max-input",
                    type="number",
                    placeholder="Max",
                    value=int(df["median_sale_price"].max()),
                    debounce=True,
                    style=small_input_style
                )
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
        ], width=3)
    ], style={"marginBottom": "20px"}),

    # Row 4: Town Search
    dbc.Row([
        dbc.Col([
            html.Label("Town Search"),
            dcc.Dropdown(
                id="town-search",
                options=[{"label": t, "value": t} for t in sorted(df["town_key"].unique())],
                placeholder="Type a town name",
                multi=False,
                searchable=True,
                clearable=True
            )
        ], width=12)
    ], style={"marginBottom": "20px"}),

    # Row 5: Scatter Plot
    dbc.Row([
        dbc.Col(html.H2("Scatter Plot", style={"textAlign": "center"}), width=12),
        dbc.Row([
            dbc.Col([
                html.Label("X Variable"),
                dcc.Dropdown(
                    id="x-variable",
                    options=[{"label": var.replace("_", " ").title(), "value": var} for var in cont_vars],
                    value=cont_vars[0]
                )
            ], width=6),
            dbc.Col([
                html.Label("Y Variable"),
                dcc.Dropdown(
                    id="y-variable",
                    options=[{"label": var.replace("_", " ").title(), "value": var} for var in cont_vars],
                    value=cont_vars[1]
                )
            ], width=6)
        ], style={"marginBottom": "20px"}),
        dbc.Col(
            dcc.Graph(id="scatter-plot", config={"displayModeBar": False}, style={"height": "600px"}),
            width=12
        )
    ], style={"marginBottom": "20px"}),

    # Row 6: Bar Chart with Dimension Selector
    dbc.Row([
        dbc.Col(html.H2("Bar Chart", style={"textAlign": "center"}), width=12),
        dbc.Row([
            dbc.Col(html.Label("Select Dimension"), width=3),
            dbc.Col(
                dcc.Dropdown(
                    id="bar-dimension",
                    options=[{"label": "Composite Score", "value": "composite_score"}] +
                            [{"label": var.replace("_", " ").title(), "value": var} for var in cont_vars if var != "composite_score"],
                    value="composite_score"
                ),
                width=9
            )
        ], style={"marginBottom": "20px"}),
        dbc.Col(
            dcc.Graph(id="bar-chart", config={"displayModeBar": False}),
            width=12, style={"height": "800px", "overflowY": "scroll"}
        )
    ], style={"marginBottom": "20px"}),

    # Row 7: Side-by-Side Town Comparison Section with Guidance
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H3("Town Comparison", style={"textAlign": "center", "display": "inline-block"}),
                html.Span("ℹ️", id="comparison-info", style={"cursor": "pointer", "marginLeft": "5px", "fontSize": "18px"})
            ]),
            width=12
        ),
        dbc.Tooltip(
            "Select two towns from the dropdowns below to compare their detailed metrics side-by-side.",
            target="comparison-info",
            placement="right"
        ),
        dbc.Row([
            dbc.Col([
                html.Label("Town 1"),
                dcc.Dropdown(
                    id="town-compare-1",
                    options=[{"label": t, "value": t} for t in sorted(df["town_key"].unique())],
                    placeholder="Select Town 1",
                    clearable=True,
                    searchable=True
                )
            ], width=6),
            dbc.Col([
                html.Label("Town 2"),
                dcc.Dropdown(
                    id="town-compare-2",
                    options=[{"label": t, "value": t} for t in sorted(df["town_key"].unique())],
                    placeholder="Select Town 2",
                    clearable=True,
                    searchable=True
                )
            ], width=6)
        ], style={"marginBottom": "20px"}),
        dbc.Row([
            dbc.Col(dcc.Graph(id="comparison-chart-1", config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(id="comparison-chart-2", config={"displayModeBar": False}), width=6)
        ])
    ], style={"marginBottom": "40px"})
])

# ------------------------------------------------------------------
# Town List Tab Content
# ------------------------------------------------------------------
town_list_content = html.Div([
    html.H2("Town List", style={"textAlign": "center", "marginTop": "20px"}),
    dbc.Button("Export Town List", id="export-town-list-button", color="primary", className="mb-2", style={"marginRight": "10px"}),
    dbc.Button("Clear Town List", id="clear-town-list-button", color="danger", className="mb-2"),
    dcc.Download(id="download-town-list"),
    dash_table.DataTable(
        id="town-list-table",
        columns=[{"name": col, "id": col} for col in [
            "town_key", "composite_score", "median_household_income", 
            "population", "median_age", "intersection_density", 
            "population_density", "pct_bachelor", "median_sale_price"
        ]],
        data=[],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )
])

# ------------------------------------------------------------------
# Main Layout with Tabs
# ------------------------------------------------------------------
app.layout = dbc.Container([
    dbc.Tabs(
        [
            dbc.Tab(dashboard_content, label="Dashboard", tab_id="dashboard-tab"),
            dbc.Tab(town_list_content, label="Town List", tab_id="town-list-tab"),
        ],
        id="tabs",
        active_tab="dashboard-tab",
        className="mb-3"
    ),
    # Dummy output for clientside callbacks.
    html.Div(id="dummy-output", style={"display": "none"})
], fluid=True, style={"padding": "20px"})

# ------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------

# Callback to toggle the About Metrics modal.
@app.callback(
    Output("modal-about", "is_open"),
    [Input("open-about", "n_clicks"), Input("close-about", "n_clicks")],
    [State("modal-about", "is_open")]
)
def toggle_modal(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

# Callback A: Update Selected Town based on clicks (scatter or bar) or town search.
@app.callback(
    Output("selected-town-store", "data"),
    [Input("bar-chart", "clickData"),
     Input("scatter-plot", "clickData"),
     Input("clear-town-button", "n_clicks"),
     Input("town-search", "value")]
)
def update_selected_town(bar_click, scatter_click, clear_click, town_search):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'clear-town-button':
        return None
    elif triggered_id == 'town-search':
        return town_search
    elif triggered_id == 'bar-chart':
        if bar_click and 'points' in bar_click and len(bar_click['points']) > 0:
            point = bar_click['points'][0]
            # For bar chart, customdata = [id, town_key]
            if 'customdata' in point and isinstance(point['customdata'], list) and len(point['customdata']) >= 2:
                return point['customdata'][1]
    elif triggered_id == 'scatter-plot':
        if scatter_click and 'points' in scatter_click and len(scatter_click['points']) > 0:
            point = scatter_click['points'][0]
            # For scatter plot, customdata = [town_key]
            if 'customdata' in point and isinstance(point['customdata'], list) and len(point['customdata']) >= 1:
                return point['customdata'][0]
    return dash.no_update

# Callback B: Update the Town Detail Chart based on the selected town.
@app.callback(
    [Output("town-detail-chart", "figure"),
     Output("town-detail-container", "style")],
    Input("selected-town-store", "data")
)
def update_town_detail_chart(selected_town):
    if selected_town is None:
        return {}, {"display": "none"}
    dff = df[df["town_key"] == selected_town]
    if dff.empty:
        return {}, {"display": "none"}
    row = dff.iloc[0]
    metrics = ["composite_score"] + cont_vars
    metric_data = []
    for m in metrics:
        global_min = df[m].min()
        global_max = df[m].max()
        value = row[m]
        norm_value = (value - global_min) / (global_max - global_min) if global_max > global_min else 0
        color = "#636efa" if m == "composite_score" else "#ffa15a"
        metric_data.append({"metric": m, "value": value, "norm": norm_value, "color": color})
    detail_df = pd.DataFrame(metric_data)
    fig = px.bar(detail_df, x="norm", y="metric", orientation="h",
                 text="value", color="color", title=f"Town Detail: {selected_town}",
                 color_discrete_map="identity")
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(xaxis_title="Normalized Value (0-1)", yaxis_title="Metric")
    return fig, {"display": "block", "marginBottom": "40px"}

# Callback to update the town list store (handles both adding and clearing).
@app.callback(
    Output("town-list-store", "data"),
    [Input("add-town-button", "n_clicks"),
     Input("clear-town-list-button", "n_clicks")],
    [State("selected-town-store", "data"),
     State("town-list-store", "data")]
)
def update_town_list_store(add_clicks, clear_clicks, selected_town, current_list):
    ctx = callback_context
    if not ctx.triggered:
        return current_list
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == "clear-town-list-button":
        return []  # Clear the list.
    elif triggered_id == "add-town-button":
        if selected_town is None:
            return current_list
        # Prevent duplicate entries.
        if any(entry["town_key"] == selected_town for entry in current_list):
            return current_list
        town_data = df[df["town_key"] == selected_town]
        if town_data.empty:
            return current_list
        row = town_data.iloc[0]
        new_entry = {
            "town_key": row["town_key"],
            "composite_score": row.get("composite_score", None),
            "median_household_income": row["median_household_income"],
            "population": row["population"],
            "median_age": row["median_age"],
            "intersection_density": row["intersection_density"],
            "population_density": row["population_density"],
            "pct_bachelor": row["pct_bachelor"],
            "median_sale_price": row["median_sale_price"],
        }
        current_list.append(new_entry)
        return current_list
    return current_list

# Callback to update the table of added towns.
@app.callback(
    Output("town-list-table", "data"),
    Input("town-list-store", "data")
)
def update_town_list_table(town_list):
    return town_list

# Callback C: Update the Bar Chart (with selectable dimension) based on filters.
@app.callback(
    Output("bar-chart", "figure"),
    [Input("county-filter", "value"),
     Input("state-filter", "value"),
     Input("population-slider", "value"),
     Input("population-min-input", "value"),
     Input("population-max-input", "value"),
     Input("age-slider", "value"),
     Input("bachelor-slider", "value"),
     Input("income-slider", "value"),
     Input("houseprice-slider", "value"),
     Input("bar-dimension", "value")]
)
def update_bar_chart(county_filter, state_filter, pop_slider, pop_min, pop_max,
                     age_slider, bachelor_slider, income_slider, houseprice_slider, bar_dimension):
    dff = df.copy()
    if county_filter:
        dff = dff[dff["county"].isin(county_filter)]
    if state_filter:
        dff = dff[dff["state_name"].isin(state_filter)]
    effective_pop_range = [pop_min if pop_min is not None else pop_slider[0],
                           pop_max if pop_max is not None else pop_slider[1]]
    dff = dff[(dff["population"] >= effective_pop_range[0]) & (dff["population"] <= effective_pop_range[1])]
    dff = dff[(dff["median_age"] >= age_slider[0]) & (dff["median_age"] <= age_slider[1])]
    dff = dff[(dff["pct_bachelor"] >= bachelor_slider[0]) & (dff["pct_bachelor"] <= bachelor_slider[1])]
    dff = dff[(dff["median_household_income"] >= income_slider[0]) & (dff["median_household_income"] <= income_slider[1])]
    dff = dff[(dff["median_sale_price"] >= houseprice_slider[0]) & (dff["median_sale_price"] <= houseprice_slider[1])]
    dff["label"] = dff["state_name"] + ", " + dff["town"]
    dff_sorted = dff.sort_values(bar_dimension, ascending=False).reset_index(drop=True)
    dff_sorted["id"] = dff_sorted.index
    fig = px.bar(
        dff_sorted,
        x=bar_dimension,
        y="label",
        orientation="h",
        title=f"{bar_dimension.replace('_', ' ').title()} by Town (Descending)",
        custom_data=["id", "town_key"],
        text=bar_dimension
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig.update_traces(customdata=dff_sorted[["id", "town_key"]].values.tolist())
    default_color = "#636efa"
    marker_colors = [default_color] * len(dff_sorted)
    fig.update_traces(marker=dict(color=marker_colors))
    fig.update_traces(textposition='auto', texttemplate='%{text:.2f}')
    height = max(800, len(dff_sorted) * 40)
    fig.update_layout(height=height)
    return fig

# Callback D: Update the Scatter Plot based on filters.
@app.callback(
    Output("scatter-plot", "figure"),
    [Input("x-variable", "value"),
     Input("y-variable", "value"),
     Input("county-filter", "value"),
     Input("state-filter", "value"),
     Input("population-slider", "value"),
     Input("population-min-input", "value"),
     Input("population-max-input", "value"),
     Input("age-slider", "value"),
     Input("bachelor-slider", "value"),
     Input("income-slider", "value"),
     Input("houseprice-slider", "value")]
)
def update_scatter(x_var, y_var, county_filter, state_filter, pop_slider, pop_min, pop_max,
                   age_slider, bachelor_slider, income_slider, houseprice_slider):
    dff = df.copy()
    if county_filter:
        dff = dff[dff["county"].isin(county_filter)]
    if state_filter:
        dff = dff[dff["state_name"].isin(state_filter)]
    effective_pop_range = [pop_min if pop_min is not None else pop_slider[0],
                           pop_max if pop_max is not None else pop_slider[1]]
    dff = dff[(dff["population"] >= effective_pop_range[0]) & (dff["population"] <= effective_pop_range[1])]
    dff = dff[(dff["median_age"] >= age_slider[0]) & (dff["median_age"] <= age_slider[1])]
    dff = dff[(dff["pct_bachelor"] >= bachelor_slider[0]) & (dff["pct_bachelor"] <= bachelor_slider[1])]
    dff = dff[(dff["median_household_income"] >= income_slider[0]) & (dff["median_household_income"] <= income_slider[1])]
    dff = dff[(dff["median_sale_price"] >= houseprice_slider[0]) & (dff["median_sale_price"] <= houseprice_slider[1])]
    dff = dff.reset_index(drop=True)
    dff["id"] = dff.index
    hover_order = {"state_name": True, "county": True, "town": True}
    for var in cont_vars:
        hover_order[var] = True
    fig = px.scatter(
        dff,
        x=x_var,
        y=y_var,
        hover_data=hover_order,
        custom_data=["town_key"],
        title="Scatter Plot"
    )
    default_color = "#636efa"
    fig.update_traces(marker=dict(color=default_color, size=12))
    fig.update_layout(transition_duration=500, clickmode='event')
    return fig

# Callback E (Client-side): Scroll to the Town Detail view when a town is selected.
app.clientside_callback(
    """
    function(selectedTown) {
        if (selectedTown) {
            var element = document.getElementById("town-detail-container");
            if (element) {
                element.scrollIntoView({behavior: "smooth"});
            }
        }
        return "";
    }
    """,
    Output("dummy-output", "children"),
    Input("selected-town-store", "data")
)

# Callback F: Update the Side-by-Side Comparison Charts.
@app.callback(
    [Output("comparison-chart-1", "figure"),
     Output("comparison-chart-2", "figure")],
    [Input("town-compare-1", "value"),
     Input("town-compare-2", "value")]
)
def update_comparison_charts(town1, town2):
    def create_detail_figure(town_key):
        if not town_key:
            return {}
        dff = df[df["town_key"] == town_key]
        if dff.empty:
            return {}
        row = dff.iloc[0]
        metrics = ["composite_score"] + cont_vars
        metric_data = []
        for m in metrics:
            global_min = df[m].min()
            global_max = df[m].max()
            value = row[m]
            norm_value = (value - global_min) / (global_max - global_min) if global_max > global_min else 0
            color = "#636efa" if m == "composite_score" else "#ffa15a"
            metric_data.append({"metric": m, "value": value, "norm": norm_value, "color": color})
        detail_df = pd.DataFrame(metric_data)
        fig = px.bar(detail_df, x="norm", y="metric", orientation="h",
                     text="value", color="color", title=f"Town Detail: {town_key}",
                     color_discrete_map="identity")
        fig.update_traces(texttemplate="%{text}", textposition="outside")
        fig.update_layout(xaxis_title="Normalized Value (0-1)", yaxis_title="Metric")
        return fig
    fig1 = create_detail_figure(town1)
    fig2 = create_detail_figure(town2)
    return fig1, fig2

# ------------------------------------------------------------------
# Synchronization Callbacks for Filters
# ------------------------------------------------------------------
@app.callback(
    [Output("population-slider", "value"),
     Output("population-min-input", "value"),
     Output("population-max-input", "value")],
    [Input("population-slider", "value"),
     Input("population-min-input", "value"),
     Input("population-max-input", "value")]
)
def sync_population_slider_and_inputs(slider_val, min_input, max_input):
    if not callback_context.triggered:
        return slider_val, slider_val[0], slider_val[1]
    trigger_id = callback_context.triggered[0]["prop_id"].split('.')[0]
    if trigger_id == "population-slider":
        return slider_val, slider_val[0], slider_val[1]
    elif trigger_id in ["population-min-input", "population-max-input"]:
        new_min = min_input if min_input is not None else slider_val[0]
        new_max = max_input if max_input is not None else slider_val[1]
        if new_min > new_max:
            new_max = new_min
        new_slider_val = [new_min, new_max]
        return new_slider_val, new_min, new_max
    return slider_val, slider_val[0], slider_val[1]

@app.callback(
    [Output("age-slider", "value"),
     Output("age-min-input", "value"),
     Output("age-max-input", "value")],
    [Input("age-slider", "value"),
     Input("age-min-input", "value"),
     Input("age-max-input", "value")]
)
def sync_age_slider_and_inputs(slider_val, min_input, max_input):
    if not callback_context.triggered:
        return slider_val, slider_val[0], slider_val[1]
    trigger_id = callback_context.triggered[0]["prop_id"].split('.')[0]
    if trigger_id == "age-slider":
        return slider_val, slider_val[0], slider_val[1]
    elif trigger_id in ["age-min-input", "age-max-input"]:
        new_min = min_input if min_input is not None else slider_val[0]
        new_max = max_input if max_input is not None else slider_val[1]
        if new_min > new_max:
            new_max = new_min
        new_slider_val = [new_min, new_max]
        return new_slider_val, new_min, new_max
    return slider_val, slider_val[0], slider_val[1]

@app.callback(
    [Output("bachelor-slider", "value"),
     Output("bachelor-min-input", "value"),
     Output("bachelor-max-input", "value")],
    [Input("bachelor-slider", "value"),
     Input("bachelor-min-input", "value"),
     Input("bachelor-max-input", "value")]
)
def sync_bachelor_slider_and_inputs(slider_val, min_input, max_input):
    if not callback_context.triggered:
        return slider_val, slider_val[0], slider_val[1]
    trigger_id = callback_context.triggered[0]["prop_id"].split('.')[0]
    if trigger_id == "bachelor-slider":
        return slider_val, slider_val[0], slider_val[1]
    elif trigger_id in ["bachelor-min-input", "bachelor-max-input"]:
        new_min = min_input if min_input is not None else slider_val[0]
        new_max = max_input if max_input is not None else slider_val[1]
        if new_min > new_max:
            new_max = new_min
        new_slider_val = [new_min, new_max]
        return new_slider_val, new_min, new_max
    return slider_val, slider_val[0], slider_val[1]

@app.callback(
    [Output("income-slider", "value"),
     Output("income-min-input", "value"),
     Output("income-max-input", "value")],
    [Input("income-slider", "value"),
     Input("income-min-input", "value"),
     Input("income-max-input", "value")]
)
def sync_income_slider_and_inputs(slider_val, min_input, max_input):
    if not callback_context.triggered:
        return slider_val, slider_val[0], slider_val[1]
    trigger_id = callback_context.triggered[0]["prop_id"].split('.')[0]
    if trigger_id == "income-slider":
        return slider_val, slider_val[0], slider_val[1]
    elif trigger_id in ["income-min-input", "income-max-input"]:
        new_min = min_input if min_input is not None else slider_val[0]
        new_max = max_input if max_input is not None else slider_val[1]
        if new_min > new_max:
            new_max = new_min
        new_slider_val = [new_min, new_max]
        return new_slider_val, new_min, new_max
    return slider_val, slider_val[0], slider_val[1]

@app.callback(
    [Output("houseprice-slider", "value"),
     Output("houseprice-min-input", "value"),
     Output("houseprice-max-input", "value")],
    [Input("houseprice-slider", "value"),
     Input("houseprice-min-input", "value"),
     Input("houseprice-max-input", "value")]
)
def sync_houseprice_slider_and_inputs(slider_val, min_input, max_input):
    if not callback_context.triggered:
        return slider_val, slider_val[0], slider_val[1]
    trigger_id = callback_context.triggered[0]["prop_id"].split('.')[0]
    if trigger_id == "houseprice-slider":
        return slider_val, slider_val[0], slider_val[1]
    elif trigger_id in ["houseprice-min-input", "houseprice-max-input"]:
        new_min = min_input if min_input is not None else slider_val[0]
        new_max = max_input if max_input is not None else slider_val[1]
        if new_min > new_max:
            new_max = new_min
        new_slider_val = [new_min, new_max]
        return new_slider_val, new_min, new_max
    return slider_val, slider_val[0], slider_val[1]

server = app.server

# ------------------------------------------------------------------
# Callback for exporting the town list as CSV.
@app.callback(
    Output("download-town-list", "data"),
    Input("export-town-list-button", "n_clicks"),
    State("town-list-store", "data"),
    prevent_initial_call=True
)
def export_town_list(n_clicks, town_list):
    if not town_list:
        return dash.no_update
    df_export = pd.DataFrame(town_list)
    return dcc.send_data_frame(df_export.to_csv, "town_list.csv", index=False)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run_server(host="0.0.0.0", port=port, debug=True)
