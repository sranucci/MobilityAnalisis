import os
import folium
import geopandas as gpd
import branca  # for colormaps

def doExercise2RealtimeAverageSpeeds(cur, results_path):
    # 1) Define and run the SQL to compute avg speed per segment,
    #    joining stops s1 and s2 to get the stop names.
    sql = """
    SELECT 
      AVG(s.distance_m /
          EXTRACT(EPOCH FROM (t.end_time_actual - t.start_time_actual))
          * 3.6
      ) AS speed_kmh,
      s.geometry,
      t.start_stop_id,
      t.end_stop_id,
      s1.stop_name AS start_stop_name,
      s2.stop_name AS end_stop_name
    FROM trip_segments t
    JOIN segments s
      ON t.start_stop_id = s.start_stop_id
     AND t.end_stop_id   = s.end_stop_id
     AND t.shape_id      = s.shape_id
    -- join stops twice for the names
    JOIN stops s1
      ON s1.stop_id = t.start_stop_id
    JOIN stops s2
      ON s2.stop_id = t.end_stop_id
    WHERE t.start_time_actual IS NOT NULL
      AND EXTRACT(EPOCH FROM (t.end_time_actual - t.start_time_actual)) > 0
    GROUP BY 
      s.geometry, 
      t.start_stop_id, 
      t.end_stop_id,
      s1.stop_name,
      s2.stop_name
    """

    # 2) Load into a GeoDataFrame (already in EPSG:4326)
    gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=cur.connection,
        geom_col="geometry",
        crs="EPSG:4326"
    )

    # 3) Build a continuous colormap between min and max speeds
    vmin = gdf['speed_kmh'].min()
    vmax = gdf['speed_kmh'].max()
    colormap = branca.colormap.LinearColormap(
        colors=['green', 'yellow', 'red'],
        vmin=vmin, vmax=vmax,
        caption='Avg Speed (km/h)'
    )

    # 4) Center the map on the data extent
    minx, miny, maxx, maxy = gdf.total_bounds
    center = [(miny + maxy) / 2, (minx + maxx) / 2]
    m = folium.Map(location=center, zoom_start=12)

    # 5) Add the colormap legend
    colormap.add_to(m)

    # 6) Draw each segment with its speed‑based colour and a richer tooltip
    for _, row in gdf.iterrows():
        speed = row['speed_kmh']
        start_name = row['start_stop_name']
        end_name = row['end_stop_name']
        color = colormap(speed)
        tooltip_html = (
            f"<b>{start_name}</b> → <b>{end_name}</b><br>"
            f"Speed: {speed:.1f} km/h"
        )
        folium.GeoJson(
            row['geometry'],
            style_function=lambda feature, col=color: {
                'color': col,
                'weight': 4,
                'opacity': 0.8
            },
            tooltip=folium.Tooltip(tooltip_html, sticky=True)
        ).add_to(m)

    # 7) Save the map as an HTML file
    out_file = os.path.join(results_path, 'ex2_realtime_average_speeds.html')
    m.save(out_file)
    print(f"Map saved to {out_file}")
