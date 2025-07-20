import os
import folium
import geopandas as gpd
import branca  # for colormaps

def doExercise4(cur, results_path):
    """
    Generates and saves an HTML map showing, for each route shape,
    a colored line where the color represents the number of distinct trips.
    """
    # 1) Define the SQL to count trips per route+shape
    sql = """
    SELECT
        t.route_id,
        COUNT(DISTINCT t.trip_id) AS trip_count,
        s.shape AS geometry
    FROM trips t
    JOIN shapes_aggregated s
      ON s.shape_id = t.shape_id
    GROUP BY t.route_id, s.shape
    ORDER BY trip_count DESC;
    """

    # 2) Load results into a GeoDataFrame (geometry already in EPSG:4326)
    gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=cur.connection,
        geom_col="geometry",
        crs="EPSG:4326"
    )

    # 2) load into a GeoDataFrame (geometry_3161 in EPSG:3161)
    speed_gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=cur.connection,
        geom_col="geometry_3161",
        crs="EPSG:3161",
    )

    # 4) build the color scale (yellow→red) based on Δ
    vmin = speed_gdf["speed_delta_kmh"].min()
    vmax = speed_gdf["speed_delta_kmh"].max()
    colormap = branca.colormap.LinearColormap(
        colors=["yellow", "red"],
        vmin=vmin,
        vmax=vmax
    )
    colormap.caption = "Speed Δ (km/h)"  # legend title

    # 5) init map
    center = speed_gdf.geometry.unary_union.centroid
    m = folium.Map(
        location=[center.y, center.x],
        tiles="CartoDB positron",
        zoom_start=12,
        control_scale=True
    )

    # 6) add each segment, coloring by its delta
    for _, row in speed_gdf.iterrows():
        geom = row.geometry
        coords = [(lat, lon) for lon, lat in geom.coords]
        color = colormap(row.speed_delta_kmh)
        tooltip = (
            f"Expected: {row.expected_speed_kmh:.1f} km/h<br>"
            f"Actual: {row.actual_speed_kmh:.1f} km/h<br>"
            f"Δ: {row.speed_delta_kmh:.1f} km/h"
        )
        folium.PolyLine(
            locations=coords,
            color=color,
            weight=4,
            opacity=0.8,
            tooltip=tooltip
        ).add_to(m)

    # 7) add the legend and save
    colormap.add_to(m)
    out_fp = os.path.join(results_path, "ex3_speed_segments_gradient_map.html")
    m.save(out_fp)
    print(f"✅ Gradient speed map saved to '{out_fp}'.")