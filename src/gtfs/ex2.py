import os
import folium
import geopandas as gpd

def doExcersise2(cur, results_path, ex2Json):
    route_id = ex2Json.get("route_id")
    if not route_id:
        raise ValueError("route_id must be provided in ex2Json for Exercise 2.")

    sql = """
        WITH first_shape AS (
  SELECT shape_id
  FROM public.segments
  WHERE route_id = %s::text
  ORDER BY shape_id
  LIMIT 1
)
SELECT
  segment_id, route_id, route_name,
  start_stop_name, end_stop_name,
  distance_m, geometry, stop_sequence
FROM public.segments s
JOIN first_shape fs USING (shape_id)
ORDER BY stop_sequence;
    """


    segs_gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        cur.connection,
        geom_col="geometry",
        crs="EPSG:4326",
        params=[str(route_id)]
    )

    # now segs_gdf is sorted by stop_sequence
    m = folium.Map(
        location=[segs_gdf.geometry.unary_union.centroid.y,
                  segs_gdf.geometry.unary_union.centroid.x],
        tiles="CartoDB positron",
        zoom_start=12,
        control_scale=True
    )

    # groupby with sort=False preserves the order of first‐appearance (i.e. your stop_sequence ordering)
    for seg_id, group in segs_gdf.groupby("stop_sequence", sort=True):
        fg = folium.FeatureGroup(name=f"Segment {seg_id}", show=False)
        # even though each group is one row, this guarantees the layer list follows stop_sequence
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

    out_fp = os.path.join(results_path, "ex2_route_segments_map.html")
    m.save(out_fp)
    print(f"✅ Exercise 2 map saved to '{out_fp}'.")
