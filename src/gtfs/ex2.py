import os
import folium
import geopandas as gpd

def doExcersise2(cur, results_path,ex2Json):
    """
    cur: psycopg2 cursor
    ex2Json: {
      "limit":    int,    # how many segments to fetch (default 100)
      "route_id": str,    # optional filter on route_id
    }
    """

    limit       = ex2Json.get("limit", 100)
    route_id    = ex2Json.get("route_id", False)


    base_sql = """
        SELECT
          segment_id,
          route_id
          route_name,
          start_stop_name,
          end_stop_name,
          distance_m,
          geometry
        FROM public.segments
        {where_clause}
        ORDER BY route_id , stop_sequence  
        LIMIT %s;
    """
    if route_id:
        where_clause = "WHERE route_id = %s"
        params = [route_id, limit]
    else:
        where_clause = ""
        params = [limit]

    sql = base_sql.format(where_clause=where_clause)

    segs_gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        cur.connection,
        geom_col="geometry",
        crs="EPSG:4326",
        params=params
    )

    center = segs_gdf.geometry.unary_union.centroid
    m = folium.Map(
        location=[center.y, center.x],
        tiles="CartoDB positron",
        zoom_start=12,
        control_scale=True
    )

    for seg_id, group in segs_gdf.groupby("segment_id"):
        fg = folium.FeatureGroup(name=f"Segment {seg_id}", show=False)
        for geom in group.geometry:
            if geom.geom_type == "LineString":
                coords = [(lat, lon) for lon, lat in geom.coords]
                folium.PolyLine(
                    locations=coords,
                    color="steelblue",
                    weight=3,
                    opacity=0.7
                ).add_to(fg)
        fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(os.path.join(results_path, "exercise2_map.html"))
    print(f"✅ Exercise 2 map saved to '{os.path.join(results_path, 'exercise2_map.html')}'. Open this file in your browser.")
