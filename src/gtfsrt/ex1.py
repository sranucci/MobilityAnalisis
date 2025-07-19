# Library imports
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from helpers.database_helpers import get_db_conn

    
# Function that fetches available trip_ids from table vehicle_positions
def fetch_trip_ids():
    conn = get_db_conn()
    cur = conn.cursor()
    if conn is None or cur is None:
        return []
    trip_id_query = "SELECT DISTINCT trip_id FROM vehicle_positions;"
    cur.execute(trip_id_query)
    trip_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return trip_ids


# Function that fetches the vehicle positions for a specifc trip_id
def fetch_vehicle_positions(trip_id):
    conn = get_db_conn()
    cur = conn.cursor()
    if conn is None or cur is None:
        return pd.DataFrame()
    query = """
    SELECT latitude, longitude, vehicle_id, speed, timestamp
    FROM vehicle_positions
    WHERE trip_id = %s
    ORDER BY timestamp;
    """
    cur.execute(query, (trip_id,))
    vehicle_positions = pd.DataFrame(cur.fetchall(), columns=['latitude', 'longitude', 'vehicle_id', 'speed', 'timestamp'])
    cur.close()
    conn.close()
    return vehicle_positions


# Dash visualization layout
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Get initial trip_ids to populate the dropdown
trip_ids = fetch_trip_ids()
# Set default trip_id (frst one in the list)
initial_trip_id = trip_ids[0] if trip_ids else None
app.layout = dbc.Container([
    html.H1("Visualization of the Vehicle Positions"),
    # Dropdown for selecting trip_id
    dcc.Dropdown(
        id="trip-dropdown",
        options=[{'label': trip_id, 'value': trip_id} for trip_id in trip_ids],
        value=initial_trip_id, # Default to the frst trip_id
        clearable=False, style={"width": "80%"}),
    # Graph to display vehicle positions
    dcc.Graph(id="vehicle-map")
    ])
# Callback function to update map based on selected trip_id
@app.callback(
    Output("vehicle-map", "figure"),
    Input("trip-dropdown", "value"))


def update_map(trip_id):
    if trip_id is None:
        return px.scatter_mapbox() # Empty map if no trip_id is selected
    
    # Fetch vehicle positions for the selected trip_id
    vehicle_positions_df = fetch_vehicle_positions(trip_id)
    if vehicle_positions_df.empty:
        return px.scatter_mapbox() # Return empty map if no data
    
    # Create a map visualization using Plotly
    fg = px.scatter_mapbox(vehicle_positions_df,
        lat="latitude", lon="longitude", hover_name="vehicle_id",
        hover_data=["speed", "timestamp"],
        title=f"Vehicle positions for {trip_id}", zoom=12)
    
    fg.update_traces(marker=dict(size=10, color='red')) # Increase the size and set color to red

    fg.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": vehicle_positions_df["latitude"].mean(),"lon": vehicle_positions_df["longitude"].mean()},
        margin={"r":0,"t":0,"l":0,"b":0})
    
    return fg


app.run_server(debug=True, port=8050)