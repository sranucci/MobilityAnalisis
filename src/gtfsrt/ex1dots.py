import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
from helpers.database_helpers import get_db_conn

def fetch_trip_ids(cur):

    cur.execute("SELECT DISTINCT trip_id FROM vehicle_positions;")
    trips = [row[0] for row in cur.fetchall()]
    return trips

def fetch_vehicle_positions(trip_id):
    conn = get_db_conn()
    if not conn:
        return pd.DataFrame()
    cur = conn.cursor()
    cur.execute("""
        SELECT latitude
             , longitude
             , vehicle_id
             , speed
             , to_timestamp(timestamp) AT TIME ZONE 'UTC' AS ts
        FROM vehicle_positions
        WHERE trip_id = %s
        ORDER BY timestamp;
    """, (trip_id,))
    df = pd.DataFrame(cur.fetchall(), columns=['latitude','longitude','vehicle_id','speed','timestamp'])
    cur.close()
    conn.close()
    return df

def doExerciseRealtime1(cur):
    # 1. Create the Dash app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # 2. Fetch trips and set up layout
    trip_ids = fetch_trip_ids(cur)
    initial = trip_ids[0] if trip_ids else None

    app.layout = dbc.Container([
        html.H1("Visualization of Vehicle Positions"),
        dcc.Dropdown(
            id="trip-dropdown",
            options=[{'label': t, 'value': t} for t in trip_ids],
            value=initial,
            clearable=False,
            style={"width": "80%"}
        ),
        dcc.Graph(id="vehicle-map")
    ], fluid=True)

    # 3. Wire the callback directly here
    @app.callback(
        Output("vehicle-map", "figure"),
        Input("trip-dropdown", "value")
    )
    def update_map(trip_id):
        if not trip_id:
            return px.scatter_mapbox()  # empty
        df = fetch_vehicle_positions(trip_id)
        if df.empty:
            return px.scatter_mapbox()

        fig = px.scatter_mapbox(
            df,
            lat="latitude", lon="longitude",
            hover_name="vehicle_id",
            hover_data={"speed":True, "timestamp":True},
            title=f"Positions for {trip_id}",
            zoom=12
        )
        fig.update_traces(marker=dict(size=8, color="red"))
        center = {"lat": df.latitude.mean(), "lon": df.longitude.mean()}
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_center=center,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        return fig

    # 4. Return the app so main.py can run it
    return app
