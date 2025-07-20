import os
import folium as fl
import geopandas as gpd

def doExcersise1TrajectoryAllRealtime(cur, results_path):
    """
    Draw every trajectory in actual_trips as a separate layer
    and save to an HTML file.
    """
    # 1. Read all trajectories (transform to EPSG:4326)
    sql = """
    SELECT
      trip_id,
      ST_Transform(trajectory, 4326) AS geom
    FROM public.actual_trips;
    """
    trajs_gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        cur.connection,         # psycopg2 connection
        geom_col='geom',
        crs='EPSG:4326'
    )

    if trajs_gdf.empty:
        print("No trajectories found in actual_trips.")
        return

    # 2. Compute map center from bounds
    minx, miny, maxx, maxy = trajs_gdf.total_bounds
    center_lat = (miny + maxy) / 2
    center_lon = (minx + maxx) / 2

    # 3. Create the folium map
    m = fl.Map(
        location=[center_lat, center_lon],
        tiles='CartoDB positron',
        zoom_start=12,
        control_scale=True
    )

    # 4. Add each trajectory as its own layer
    for _, row in trajs_gdf.iterrows():
        fg = fl.FeatureGroup(name=str(row['trip_id']), show=True)
        geom = row['geom']

        # Handle both LineString and MultiLineString
        if geom.geom_type == 'LineString':
            coords = [(lat, lon) for lon, lat in geom.coords]
            fl.PolyLine(locations=coords, weight=3, opacity=0.8).add_to(fg)

        fg.add_to(m)

    # 5. Add layer control and save
    fl.LayerControl(collapsed=False).add_to(m)
    output_file = os.path.join(results_path, "ex1_realtime_all_trajectories.html")
    m.save(output_file)
    print(f"Saved all‑trajectories map to {output_file}")
