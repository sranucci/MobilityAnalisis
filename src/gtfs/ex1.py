# Library imports
import os
import folium as fl
import geopandas as gpd


def doPerRouteViewDisplay(cur):
    sql = """
    SELECT DISTINCT ON (sa.shape_id)
        sa.shape_id,
        r.route_long_name AS route_name,
        sa.shape
    FROM shapes_aggregated sa
    JOIN trips t
      ON t.shape_id = sa.shape_id
    JOIN routes r
      ON r.route_id = t.route_id
    ORDER BY sa.shape_id, r.route_long_name
    """

    # Read the data (already in EPSG:4326) for mapping
    shapes_gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        cur.connection,
        geom_col='shape',
        crs='EPSG:4326'
    )

    # Initialize the map centered on Guelph, Ontario
    map_indiv_lines = fl.Map(
        location=[43.5448, -80.2482],
        tiles='CartoDB positron',
        zoom_start=13,
        control_scale=True
    )

    # Add each route as its own layer, labeled by route_name
    for _, row in shapes_gdf.iterrows():
        fg = fl.FeatureGroup(name=row['route_name'], show=True)
        geom = row['shape']

        if geom.geom_type == 'LineString':
            coords = [(lat, lon) for lon, lat in geom.coords]
            fl.PolyLine(
                locations=coords,
                weight=2,
                opacity=0.8
            ).add_to(fg)

        fg.add_to(map_indiv_lines)

    fl.LayerControl(collapsed=False).add_to(map_indiv_lines)
    return map_indiv_lines


def doExcersise1(cur, results_path, ex1Json):
    if ex1Json.get("perRouteViewDisplay", False):
        map_indiv_lines = doPerRouteViewDisplay(cur)
        output_file = os.path.join(results_path, "ex1PerViewRoutes.html")
        map_indiv_lines.save(output_file)
        print(f"Saved per-route view map to {output_file}")
