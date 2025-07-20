import os
import folium
import geopandas as gpd
import branca
from branca.element import Template, MacroElement

def doExercise3DelayPerStopRealtime(cur, results_path):
    # 1) Pull avg_delay per stop (in minutes)
    sql = """
    SELECT 
      stop_id,
      stop_loc   AS geometry,
      AVG(delay) AS avg_delay
    FROM trip_stops
    GROUP BY stop_id, stop_loc
    """
    gdf = gpd.GeoDataFrame.from_postgis(
        sql, con=cur.connection, geom_col="geometry", crs="EPSG:4326"
    )

    # 2) Classify by sign + threshold
    def classify_and_color(delay):
        if delay < -1:
            return "Late (> 1 min behind)", "red"
        elif delay > 1:
            return "Early (> 1 min ahead)",   "green"
        else:
            return "On‑time (± 1 min)",       "gray"

    # 3) Initialize map
    minx, miny, maxx, maxy = gdf.total_bounds
    center = [(miny + maxy)/2, (minx + maxx)/2]
    m = folium.Map(center, zoom_start=12)

    # 4) Draw each stop
    for _, row in gdf.iterrows():
        label, color = classify_and_color(row["avg_delay"])
        folium.CircleMarker(
            location=(row.geometry.y, row.geometry.x),
            radius=6,
            color=color,
            fill=True, fill_color=color, fill_opacity=0.8,
            tooltip=(
                f"{row['stop_id']}: {row['avg_delay']:.1f} min<br>"
                f"<i>{label}</i>"
            )
        ).add_to(m)

    # 5) Add a 3‑item legend on top
    legend = MacroElement()
    legend._template = Template("""
    {% macro html(this, kwargs) %}
    <div class="maplegend">
      <div class="legend-title">Avg Delay (min)</div>
      <ul class="legend-scale">
        <li><span style="background:red;"></span>Late (&lt; –1)</li>
        <li><span style="background:gray;"></span>On‑time (± 1)</li>
        <li><span style="background:green;"></span>Early (&gt; 1)</li>
      </ul>
    </div>
    <style>
      .maplegend {
        position:absolute; bottom:20px; left:20px;
        z-index:9999;
        background:rgba(255,255,255,0.9);
        padding:10px; border:1px solid #999;
        border-radius:4px; font-size:12px;
        box-shadow:0 0 15px rgba(0,0,0,0.2);
      }
      .maplegend .legend-title { font-weight:bold; margin-bottom:5px;}
      .maplegend .legend-scale { list-style:none; margin:0; padding:0;}
      .maplegend .legend-scale li {
        display:flex; align-items:center; margin-bottom:4px;
      }
      .maplegend .legend-scale span {
        display:inline-block; width:12px; height:12px;
        margin-right:6px; border:1px solid #999;
      }
    </style>
    {% endmacro %}
    """)
    m.get_root().add_child(legend)

    # 6) Save
    out_file = os.path.join(results_path, "ex3_real_time_avg_delay_per_stop.html")
    m.save(out_file)
    print(f"Map saved to {out_file}")
