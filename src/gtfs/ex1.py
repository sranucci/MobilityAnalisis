# Library imports
import folium as fl
import geopandas as gpd

# Function that obtains the geometries of the transit lines from a PostgreSQL cursor
def doExcersise1(cur,results_path, ex1Json):
    # SQL query to get the first 100 shapes, ordered by shape_id
    sql = '''
    SELECT * 
    FROM shapes_aggregated_31370
    ORDER BY shape_id
    LIMIT 100;
    '''

    # Read the data using EPSG:31370 and reproject to EPSG:4326 for mapping
    shapes_gdf = gpd.GeoDataFrame.from_postgis(sql, cur.connection,geom_col='shape', crs='EPSG:31370').to_crs('EPSG:4326')

    # Initialize the map centered approximately on Belgium
    map_indiv_lines = fl.Map(location=[50.85, 4.35], tiles='CartoDB positron',
                             zoom_start=11, control_scale=True)

    # Add each route as a FeatureGroup
    for shape_id, shape_group in shapes_gdf.groupby('shape_id'):
        feature_group = fl.FeatureGroup(name=f"Route {shape_id}", show=True)

        for geometry in shape_group.geometry:
            if geometry.geom_type == 'LineString':
                coords = [(lat, lon) for lon, lat in geometry.coords]  # Reverse for folium
                fl.PolyLine(locations=coords, color="blue", weight=2, opacity=0.8).add_to(feature_group)

        feature_group.add_to(map_indiv_lines)

    fl.LayerControl(collapsed=False).add_to(map_indiv_lines)
    return map_indiv_lines
