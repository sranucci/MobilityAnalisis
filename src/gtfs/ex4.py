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

    # 3) Build color scale based on trip_count (yellow → red)
    vmin = gdf["trip_count"].min()
    vmax = gdf["trip_count"].max()
    colormap = branca.colormap.LinearColormap(
        colors=["green", "red"],
        vmin=vmin,
        vmax=vmax
    )
    colormap.caption = "Trip Count"  # legend title

    # 4) Initialize map centered on all shapes
    center = gdf.geometry.unary_union.centroid
    m = folium.Map(
        location=[center.y, center.x],
        tiles="CartoDB positron",
        zoom_start=12,
        control_scale=True
    )

    # 5) Add each shape, coloring by trip_count
    for _, row in gdf.iterrows():
        geom = row.geometry
        # Extract coordinates (handles both LineString and MultiLineString)
        if geom.geom_type == "MultiLineString":
            coords_list = [list(seg.coords) for seg in geom.geoms]
        else:
            coords_list = [list(geom.coords)]
        
        color = colormap(row.trip_count)
        tooltip = f"Route {row.route_id}: {row.trip_count} trips"

        for coords in coords_list:
            # folium expects [(lat, lon), ...]
            locations = [(lat, lon) for lon, lat in coords]
            folium.PolyLine(
                locations=locations,
                color=color,
                weight=4,
                opacity=0.8,
                tooltip=tooltip
            ).add_to(m)

    # 6) Add the legend and save the map
    colormap.add_to(m)
    out_fp = os.path.join(results_path, "ex4_trip_count_map.html")
    m.save(out_fp)
    print(f"✅ Trip count map saved to '{out_fp}'.")
