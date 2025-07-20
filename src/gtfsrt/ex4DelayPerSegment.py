import os
import folium
import geopandas as gpd
import branca
from branca.element import Template, MacroElement

def doExercise4SegmentsDelayMap(cur, results_path):
    # 1) Pull segment stats
    sql = """
    WITH agg_by_seg AS (
      SELECT 
        start_stop_id,
        end_stop_id,
        seg_geo,
        COUNT(*)                   AS no_trips_seg,
        AVG(elapsed_time_actual)   AS avg_span_actual,
        AVG(elapsed_time_schedule) AS avg_span_schedule
      FROM trips_join_segments
      GROUP BY start_stop_id, end_stop_id, seg_geo
    )
    SELECT
      seg_geo   AS geometry,
      no_trips_seg,
      CASE WHEN avg_span_actual - avg_span_schedule < 0 THEN 1 ELSE 0 END
         AS has_delay
    FROM agg_by_seg
    """
    gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=cur.connection,
        geom_col="geometry",
        crs="EPSG:4326"
    )

    # 2) Prepare map centered on data
    minx, miny, maxx, maxy = gdf.total_bounds
    center = [(miny + maxy) / 2, (minx + maxx) / 2]
    m = folium.Map(center, zoom_start=12)

    # 3) Draw each segment with a fixed weight
    for _, row in gdf.iterrows():
        color = 'red' if row['has_delay'] == 1 else 'green'
        folium.GeoJson(
            row['geometry'],
            style_function=lambda feat, col=color: {
                'color': col,
                'weight': 4,
                'opacity': 0.7
            },
            tooltip=folium.Tooltip(
                f"Trips: {row['no_trips_seg']}<br>"
                f"{'Delayed' if row['has_delay']==1 else 'On‑time'}"
            )
        ).add_to(m)

    # 4) Inject a simple color legend
    legend = MacroElement()
    legend._template = Template("""
    {% macro html(this, kwargs) %}
    <div class="maplegend">
      <div class="legend-title">Segment Status</div>
      <ul class="legend-scale">
        <li><span style="background:green;"></span>On‑time</li>
        <li><span style="background:red;"></span>Delayed</li>
      </ul>
    </div>
    <style>
      .maplegend {
        position:absolute;
        bottom:20px; left:20px;
        z-index:9999;
        background:rgba(255,255,255,0.9);
        padding:8px; border:1px solid #999;
        border-radius:4px; font-size:12px;
        box-shadow:0 0 15px rgba(0,0,0,0.2);
      }
      .maplegend .legend-title {
        font-weight:bold;
        margin-bottom:4px;
      }
      .maplegend .legend-scale {
        list-style:none; margin:0; padding:0;
      }
      .maplegend .legend-scale li {
        display:flex; align-items:center;
        margin-bottom:4px;
      }
      .maplegend .legend-scale span {
        display:inline-block; width:12px; height:12px;
        margin-right:6px; border:1px solid #999;
      }
    </style>
    {% endmacro %}
    """)
    m.get_root().add_child(legend)

    # 5) Save out
    out_file = os.path.join(results_path, 'ex4_segments_delay_map.html')
    m.save(out_file)
    print(f"Map saved to {out_file}")
