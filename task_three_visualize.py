import dash
import pandas as pd
from dash import dcc, html
import plotly.express as px
import os

# configuration
DATA_FILE = 'pink_morsel_sales_summary.csv' 
DEFAULT_CURRENCY_SYMBOL = '$'

# data loading and cleaning
def load_and_clean_data(file_path):
    """
    Loads the sales summary CSV, detects the currency symbol,
    cleans the 'sales' column into a numeric format, and prepares the DataFrame.
    """
    if not os.path.exists(file_path):
        print(f"Error: Data file not found at {file_path}. Please run 'process_sales_data.py' first.")
        # return an empty DataFrame to prevent app crash
        return pd.DataFrame({'sales': [], 'date': [], 'region': []}), DEFAULT_CURRENCY_SYMBOL

    df = pd.read_csv(file_path)

    if df.empty:
        print("Warning: Data file is empty.")
        return pd.DataFrame({'sales': [], 'date': [], 'region': []}), DEFAULT_CURRENCY_SYMBOL

    # get the first sales string value to detect the symbol
    first_sales_value = df['sales'].astype(str).dropna().iloc[0] if not df['sales'].dropna().empty else None
    
    if first_sales_value and len(first_sales_value) > 1:
        currency_symbol = first_sales_value[0]
        slice_start_index = 1
    else:
        # fallback to default symbol and no slicing
        currency_symbol = DEFAULT_CURRENCY_SYMBOL
        slice_start_index = 0

    # clean 'sales' column (convert string back to numeric float)
    df['Sales_Value'] = (
        df['sales']
        .astype(str)
        .str.slice(slice_start_index)
    )
    df['Sales_Value'] = pd.to_numeric(df['Sales_Value'], errors='coerce').fillna(0)

    # ensure 'date' is a datetime object for proper visualization on the X-axis
    df['date'] = pd.to_datetime(df['date'])

    return df, currency_symbol

# load the data once
df, currency_symbol = load_and_clean_data(DATA_FILE)

# data Aggregation for Line Chart
daily_sales = df.groupby(['date', 'region'])['Sales_Value'].sum().reset_index()
daily_sales.rename(columns={'Sales_Value': 'Total Daily Sales'}, inplace=True)

# dash App Setup
app = dash.Dash(__name__)

# create the Plotly Line Chart
fig = px.line(
    daily_sales, 
    x='date', 
    y='Total Daily Sales', 
    color='region', 
    title=f'Pink Morsel Total Daily Sales by Region',
    labels={
        'date': 'Date',
        'Total Daily Sales': f'Total Sales ({currency_symbol})',
        'region': 'Region'
    },
    template='plotly_white'
)

# customize layout for better readability
fig.update_layout(
    xaxis_title='Date',
    yaxis_title=f'Total Sales ({currency_symbol})',
    xaxis={'tickformat': '%Y-%m-%d'}, # Explicit date format
    margin=dict(l=40, r=40, t=60, b=40),
    transition_duration=500
)

# app layout
app.layout = html.Div(
    style={
        'fontFamily': 'Arial, sans-serif',
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '20px'
    },
    children=[
        html.H1(
            "Pink Morsel Sales Analysis Dashboard", 
            style={'textAlign': 'center', 'color': '#333'}
        ),
        html.Div(
            [
                html.P(
                    f"Data Source: {DATA_FILE}",
                    style={'textAlign': 'center', 'color': '#666'}
                ),
            ],
            style={'marginBottom': '20px', 'borderBottom': '1px solid #ddd', 'paddingBottom': '10px'}
        ),
        dcc.Graph(
            id='sales-line-chart',
            figure=fig,
            style={'height': '600px'}
        )
    ]
)

if __name__ == '__main__':
    # setting debug=True allows for automatic reloading on code changes
    app.run(debug=True)