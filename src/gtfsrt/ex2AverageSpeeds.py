import os
import folium
import geopandas as gpd
import branca  # for colormaps

def doExercise2RealtimeAverageSpeeds(cur, results_path):
    # 1) Run the combined actual/expected speeds SQL
    sql = """
    WITH actual_speeds AS MATERIALIZED (
      SELECT
        t.start_stop_id,
        t.end_stop_id,
        s.geometry,
        s1.stop_name AS start_stop_name,
        s2.stop_name AS end_stop_name,
        AVG(s.distance_m / dur_secs * 3.6) AS actual_speed_kmh
      FROM (
        SELECT *,
               EXTRACT(EPOCH FROM (end_time_actual - start_time_actual)) AS dur_secs
        FROM trip_segments
        WHERE start_time_actual IS NOT NULL
          AND end_time_actual IS NOT NULL
      ) t
      JOIN segments s
        ON t.start_stop_id = s.start_stop_id
       AND t.end_stop_id   = s.end_stop_id
       AND t.shape_id      = s.shape_id
      JOIN stops s1
        ON s1.stop_id = t.start_stop_id
      JOIN stops s2
        ON s2.stop_id = t.end_stop_id
      WHERE t.dur_secs > 0
      GROUP BY
        t.start_stop_id,
        t.end_stop_id,
        s.geometry,
        s1.stop_name,
        s2.stop_name
    ),
    expected_speeds AS MATERIALIZED (
      SELECT
        c.from_stop_id,
        c.to_stop_id,
        AVG(s.distance_m_3161 / dur_secs * 3.6) AS expected_speed_kmh
      FROM (
        SELECT *,
               EXTRACT(EPOCH FROM (t_arrival - t_departure)) AS dur_secs
        FROM connections
        WHERE date BETWEEN '2025-05-04' AND '2025-08-30'
          AND t_arrival IS NOT NULL
          AND t_departure IS NOT NULL
      ) c
      JOIN segments s
        ON c.route_id     = s.route_id
       AND c.direction_id = s.direction_id
       AND c.from_stop_id = s.start_stop_id
       AND c.to_stop_id   = s.end_stop_id
      WHERE c.dur_secs > 30
      GROUP BY
        c.from_stop_id,
        c.to_stop_id
    )
    SELECT
      a.start_stop_id,
      a.end_stop_id,
      a.start_stop_name,
      a.end_stop_name,
      a.geometry,
      a.actual_speed_kmh,
      e.expected_speed_kmh
    FROM actual_speeds a
    JOIN expected_speeds e
      ON a.start_stop_id = e.from_stop_id
     AND a.end_stop_id   = e.to_stop_id;
    """

    # 2) Load into a GeoDataFrame
    gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=cur.connection,
        geom_col="geometry",
        crs="EPSG:4326"
    )

    # 3) Compute the speed difference
    gdf["diff_kmh"] = gdf["actual_speed_kmh"] - gdf["expected_speed_kmh"]
    vmin, vmax = gdf["diff_kmh"].min(), gdf["diff_kmh"].max()

    # 4) Create a diverging colormap: blue → green → red
    div_colormap = branca.colormap.LinearColormap(
        ["blue", "green", "red"],
        vmin=vmin, vmax=vmax,
        caption="Actual – Expected Speed (km/h)"
    )

    # 5) Center the map
    minx, miny, maxx, maxy = gdf.total_bounds
    center = [(miny + maxy) / 2, (minx + maxx) / 2]
    m = folium.Map(location=center, zoom_start=12)

    # 6) Add the legend
    div_colormap.add_to(m)

    # 7) Draw each segment with tooltip showing both speeds and the difference
    for _, row in gdf.iterrows():
        diff = row["diff_kmh"]
        color = div_colormap(diff)
        tooltip_html = (
            f"<b>{row['start_stop_name']}</b> → <b>{row['end_stop_name']}</b><br>"
            f"Actual: {row['actual_speed_kmh']:.1f} km/h<br>"
            f"Expected: {row['expected_speed_kmh']:.1f} km/h<br>"
            f"Δ = {diff:.1f} km/h"
        )

        folium.GeoJson(
            row["geometry"],
            style_function=lambda feature, col=color: {
                "color": col,
                "weight": 4,
                "opacity": 0.8
            },
            tooltip=folium.Tooltip(tooltip_html, sticky=True)
        ).add_to(m)

    # 8) Save the map
    out_file = os.path.join(results_path, "ex2_realtime_average_speeds.html")
    m.save(out_file)
    print(f"Map saved to {out_file}")
