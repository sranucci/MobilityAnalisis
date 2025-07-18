import os
import folium as fl
import geopandas as gpd
from sqlalchemy import text


def doExcersise3a(cur, path_results, ex3Json):
    # Extract parameters from ex2Json
    start_date = ex2Json["startDate"]
    end_date = ex2Json["endDate"]
    limit = ex2Json.get("limit", 1000)  # default to 1000 if not present

    # SQL query with limit parameter
    sql = """
        SELECT AVG(st_length(s.geom_31370) /
                   EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure)) * 3.6) AS avg_speed_kmh,
               c.from_stop_id,
               c.from_stop_name,
               c.to_stop_id,
               c.to_stop_name,
               s.geom_31370
        FROM connections c, segments s
        WHERE c.route_id = s.route_id
          AND c.direction_id = s.direction_id
          AND c.from_stop_id = s.start_stop_id
          AND c.to_stop_id = s.end_stop_id
          AND c.date BETWEEN %s AND %s
          AND EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure)) > 0
        GROUP BY c.from_stop_id, c.from_stop_name, c.to_stop_id, c.to_stop_name, s.geom_31370
        ORDER BY c.from_stop_id
        LIMIT %s;
    """

    # Use SQLAlchemy connection from psycopg2 cursor
    con = cur.connection
    gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=con,
        geom_col="geom_31370",
        crs="EPSG:31370",
        params=[start_date, end_date, limit]
    ).to_crs("EPSG:4326")

    # Create folium map
    map_speed = fl.Map(location=[50.85, 4.35], tiles='CartoDB positron', zoom_start=11)

    # Normalize speed for color scale
    speeds = gdf["avg_speed_kmh"]
    min_speed, max_speed = speeds.min(), speeds.max()

    def get_color(speed):
        if max_speed == min_speed:
            return "#0000FF"
        ratio = (speed - min_speed) / (max_speed - min_speed)
        r = int(255 * ratio)
        b = int(255 * (1 - ratio))
        return f"#{r:02x}00{b:02x}"

    for _, row in gdf.iterrows():
        if hasattr(row["geom_31370"], "geom_type") and row["geom_31370"].geom_type == "LineString":
            coords = [(lat, lon) for lon, lat in row["geom_31370"].coords]
            fl.PolyLine(
                locations=coords,
                color=get_color(row["avg_speed_kmh"]),
                weight=4,
                opacity=0.8,
                tooltip=f"{row['from_stop_name']} ➝ {row['to_stop_name']} ({row['avg_speed_kmh']:.1f} km/h)"
            ).add_to(map_speed)

    fl.LayerControl(collapsed=False).add_to(map_speed)

    # Save to file
    output_file = os.path.join(path_results, "exercise3_map.html")
    map_speed.save(output_file)
    print(f"Map saved to {output_file}")


def doExcercsise3b(cur,path_results,ex3Json):




def doExcersise3(cur, path_results, ex3Json):

    if ex3Json.get("speedPerSegmentAverage", {}).get("display", False):
        doExcersise3a(cur,path_results,ex3Json.get("speedPerSegmentAverage", {}) )
    elif ex3Json.get("trackTripSpeedAverage", {}).get("display", False):
        doExcersise3a(cur,path_results,ex3Json.get("trackTripSpeedAverage", {}) )


