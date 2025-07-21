import os
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

def fetch_trip_ids(cur):
    cur.execute("SELECT DISTINCT actual_trip_id FROM trip_stops;")
    return [row[0] for row in cur.fetchall()]

def fetch_trip_delays(trip_id, cur):
    sql = """
    WITH actual_schedule_trips AS (
      SELECT
        actual_trip_id,
        stop_id,
        schedule_time,
        actual_time,
        tgeompointSeq(
          array_agg(tgeompoint(stop_loc, schedule_time)
            ORDER BY schedule_time)
        ) AS schedule_trip,
        tgeompointSeq(
          array_agg(tgeompoint(trip_geom, actual_time)
            ORDER BY actual_time)
        ) AS actual_trip
      FROM trip_stops
      WHERE actual_trip_id = %s
      GROUP BY
        actual_trip_id,
        stop_id,
        schedule_time,
        actual_time
    )
    SELECT
      stop_id,
      schedule_time_unnested AS schedule_time,
      EXTRACT(
        EPOCH
        FROM (actual_time_unnested - schedule_time_unnested)
      ) / 60 AS delay_minutes
    FROM (
      SELECT
        unnest(timestamps(actual_trip))   AS actual_time_unnested,
        unnest(timestamps(schedule_trip)) AS schedule_time_unnested,
        stop_id
      FROM actual_schedule_trips
    ) t
    ORDER BY schedule_time_unnested;
    """
    df = pd.read_sql_query(sql, cur.connection, params=(trip_id,))
    df['schedule_time'] = pd.to_datetime(df['schedule_time'])
    return df

def doExercise4DelayDashboard(cur):

    trip_ids = fetch_trip_ids(cur)
    initial = trip_ids[0] if trip_ids else None

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.layout = dbc.Container([
        html.H1("Trip Delay Analysis"),
        dcc.Dropdown(
            id="trip-dropdown",
            options=[{"label": t, "value": t} for t in trip_ids],
            value=initial,
            clearable=False,
            style={"width": "50%"}
        ),
        dcc.Graph(id="delay-chart")
    ], fluid=True)

    @app.callback(
        Output("delay-chart", "figure"),
        Input("trip-dropdown", "value")
    )
    def update_delay_chart(trip_id):
        if not trip_id:
            return px.line()
        df = fetch_trip_delays(trip_id, cur)
        if df.empty:
            return px.line()

        # <-- SWITCH TO A LINE+MARKER CHART
        fig = px.line(
            df,
            x='schedule_time',
            y='delay_minutes',
            markers=True,
            hover_data=['stop_id'],
            title=f"Delays for Trip {trip_id}",
            labels={'schedule_time': 'Scheduled Time', 'delay_minutes': 'Delay (min)'}
        )
        fig.update_traces(mode='lines+markers')
        fig.update_layout(
            xaxis_tickformat='%H:%M',
            margin={'t':40, 'b':40}
        )
        return fig

    return app
