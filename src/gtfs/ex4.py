import os
import pandas as pd
import plotly.express as px

def doExercise4(cur, results_path):
    # 1) Query trip counts per route
    sql = """
    SELECT
      r.route_id,
      r.route_long_name,
      COUNT(*) AS trip_count
    FROM trips t
    JOIN routes r
      ON r.route_id = t.route_id
    JOIN shapes_aggregated s
      ON t.shape_id = s.shape_id
    GROUP BY
      r.route_id,
      r.route_long_name
    ORDER BY
      trip_count DESC;
    """

    # 2) Load into a DataFrame
    df = pd.read_sql_query(sql, con=cur.connection)

    # 3) Plot a bar chart with Plotly
    fig = px.bar(
        df,
        x='route_long_name',
        y='trip_count',
        title='Trip Count per Route',
        labels={'route_long_name': 'Route', 'trip_count': 'Number of Trips'}
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        margin=dict(t=50, b=200)
    )

    # 4) Save as interactive HTML
    out_html = os.path.join(results_path, "ex4_trip_count_bar_chart.html")
    fig.write_html(out_html)
    print(f"Interactive bar chart saved to {out_html}")

    return fig