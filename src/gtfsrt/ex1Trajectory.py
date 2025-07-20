import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
import json
from helpers.database_helpers import get_db_conn

def fetch_trip_ids(cur):
    cur.execute("SELECT DISTINCT trip_id FROM vehicle_positions;")
    return [row[0] for row in cur.fetchall()]

def fetch_trip_trajectory(trip_id, cur):
    # pull the geometry as GeoJSON, reproject to 4326
    cur.execute("""
        SELECT ST_AsGeoJSON(
                 ST_Transform(trajectory, 4326)
               ) 
          FROM actual_trips
         WHERE trip_id = %s;
    """, (trip_id,))
    row = cur.fetchone()
    if not row or row[0] is None:
        return []
    geo = json.loads(row[0])
    # GeoJSON LineString: { "type":"LineString", "coordinates":[ [lon,lat], … ] }
    return geo.get("coordinates", [])

def doExerciseRealtime1Trajectory(cur):
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # fetch all trip_ids up front
    trip_ids = fetch_trip_ids(cur)
    initial = trip_ids[0] if trip_ids else None

    app.layout = dbc.Container([
        html.H1("Trajectories of Vehicle Trips"),
        dcc.Dropdown(
            id="trip-dropdown",
            options=[{"label": t, "value": t} for t in trip_ids],
            value=initial,
            clearable=False,
            style={"width": "80%"}
        ),
        dcc.Graph(id="vehicle-map")
    ], fluid=True)

    @app.callback(
        Output("vehicle-map", "figure"),
        Input("trip-dropdown", "value")
    )
    def update_map(trip_id):
        # blank map if nothing selected or no geometry
        if not trip_id:
            return px.line_mapbox()
        coords = fetch_trip_trajectory(trip_id, cur)
        if not coords:
            return px.line_mapbox()

        # build a DataFrame of lon/lat pairs
        df = pd.DataFrame(coords, columns=["lon", "lat"])

        # draw the trajectory
        fig = px.line_mapbox(
            df,
            lat="lat", lon="lon",
            title=f"Trajectory for {trip_id}",
            zoom=12
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox_center={"lat": df.lat.mean(), "lon": df.lon.mean()},
            margin={"l":0, "r":0, "t":30, "b":0}
        )
        return fig

    return app
