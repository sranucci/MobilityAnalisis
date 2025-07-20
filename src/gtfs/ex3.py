import os
import folium
import geopandas as gpd

def plot_speed_segments(
    cur,
    results_path,
    minDateForAverage,
    maxDateForAverage,
    target_date,
    target_trip_id,
    km_above_expected
):
    # 1) get the SQL and params
    sql, params = generate_speed_query(
        minDateForAverage,
        maxDateForAverage,
        target_date,
        target_trip_id,
        km_above_expected
    )

    # 2) load into a GeoDataFrame (geometry_3161 in EPSG:3161), passing params as a dict
    speed_gdf = gpd.GeoDataFrame.from_postgis(
        sql,
        con=cur.connection,
        geom_col="geometry_3161",
        crs="EPSG:3161",
        params=params
    )

    # 3) reproject to WGS84 for display on a Leaflet map
    speed_gdf = speed_gdf.to_crs(epsg=4326)

    # 4) make "geometry_3161" the active geometry column and rename to "geometry"
    speed_gdf = (
        speed_gdf
        .set_geometry("geometry_3161")
        .rename_geometry("geometry")
    )

    # 5) init map centered on all segments
    center = speed_gdf.geometry.unary_union.centroid
    m = folium.Map(
        location=[center.y, center.x],
        tiles="CartoDB positron",
        zoom_start=12,
        control_scale=True
    )

    # 6) add each segment with a hover‐tooltip showing expected vs actual speed
    for _, row in speed_gdf.iterrows():
        geom = row.geometry
        coords = [(lat, lon) for lon, lat in geom.coords]
        tooltip = (
            f"Expected: {row.expected_speed_kmh:.1f} km/h<br>"
            f"Actual: {row.actual_speed_kmh:.1f} km/h<br>"
            f"Δ: {row.speed_delta_kmh:.1f} km/h"
        )
        folium.PolyLine(
            locations=coords,
            color="steelblue",
            weight=3,
            opacity=0.7,
            tooltip=tooltip
        ).add_to(m)

    # 7) save
    out_fp = os.path.join(results_path, "speed_segments_map.html")
    m.save(out_fp)
    print(f"✅ Speed segments map saved to '{out_fp}'.")


def doExercise3(cur, results_path, ex3Json):
    minDateForAverage = ex3Json["minDateForAverage"]
    maxDateForAverage = ex3Json["maxDateForAverage"]
    target_date = ex3Json["target_date"]
    target_trip_id = ex3Json["target_trip_id"]
    km_above_expected = ex3Json["km_h_above_expected"]

    plot_speed_segments(
        cur,
        results_path,
        minDateForAverage,
        maxDateForAverage,
        target_date,
        target_trip_id,
        km_above_expected
    )


def generate_speed_query(
    minDateForAverage,
    maxDateForAverage,
    target_date,
    target_trip_id,
    km_above_expected
):
    """
    Returns a parametrized SQL query and a dict of parameters to:
    1) compute expected speeds between stops (including geometry_3161) over a given date range,
    2) compute actual speeds for a specific trip on a given date,
    3) filter segments where actual_speed - expected_speed > km_above_expected.
    """
    query = """
WITH expected_speed_between_stops AS (
  SELECT
    c.route_id,
    c.direction_id,
    c.from_stop_id,
    c.to_stop_id,
    AVG(
      s.distance_m_3161
      / EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure))
      * 3.6
    ) AS expected_speed_kmh,
    s.geometry_3161
  FROM connections c
  JOIN segments s
    ON c.route_id     = s.route_id
   AND c.direction_id = s.direction_id
   AND c.from_stop_id = s.start_stop_id
   AND c.to_stop_id   = s.end_stop_id
  WHERE
    c.date BETWEEN %(minDateForAverage)s AND %(maxDateForAverage)s
    AND EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure)) > 30
  GROUP BY
    c.route_id,
    c.direction_id,
    c.from_stop_id,
    c.to_stop_id,
    s.geometry_3161
  ORDER BY expected_speed_kmh DESC
),
speed_per_vehicle_trip AS (
  SELECT
    c.route_id,
    c.direction_id,
    c.trip_id,
    c.from_stop_id,
    c.to_stop_id,
    (
      s.distance_m_3161
      / EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure))
      * 3.6
    ) AS actual_speed_kmh
  FROM connections c
  JOIN segments s
    ON c.route_id     = s.route_id
   AND c.direction_id = s.direction_id
   AND c.from_stop_id = s.start_stop_id
   AND c.to_stop_id   = s.end_stop_id
  WHERE
    c.date = %(target_date)s
    AND c.trip_id = %(target_trip_id)s
    AND EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure)) > 30
)
SELECT DISTINCT ON (sv.trip_id, sv.from_stop_id, sv.to_stop_id)
  sv.trip_id,
  sv.from_stop_id,
  sv.to_stop_id,
  sv.actual_speed_kmh,
  se.expected_speed_kmh,
  se.geometry_3161,
  (sv.actual_speed_kmh - se.expected_speed_kmh) AS speed_delta_kmh
FROM speed_per_vehicle_trip sv
JOIN expected_speed_between_stops se
  ON sv.route_id     = se.route_id
 AND sv.direction_id = se.direction_id
 AND sv.from_stop_id = se.from_stop_id
 AND sv.to_stop_id   = se.to_stop_id
WHERE
  sv.actual_speed_kmh - se.expected_speed_kmh > %(km_above_expected)s
ORDER BY
  sv.trip_id,
  sv.from_stop_id,
  sv.to_stop_id,
  speed_delta_kmh DESC;
"""
    params = {
        "minDateForAverage": minDateForAverage,
        "maxDateForAverage": maxDateForAverage,
        "target_date": target_date,
        "target_trip_id": target_trip_id,
        "km_above_expected": km_above_expected
    }
    return query, params










# import os
# import folium
# import geopandas as gpd

# def plot_speed_segments(
#     cur,
#     results_path,
#     minDateForAverage,
#     maxDateForAverage,
#     target_date,
#     target_trip_id,
#     km_above_expected
# ):
#     # 1) get the SQL and params
#     sql, params = generate_speed_query(
#         minDateForAverage,
#         maxDateForAverage,
#         target_date,
#         target_trip_id,
#         km_above_expected
#     )

#     # 2) load into a GeoDataFrame (assume geometry_3161 is EPSG:3161)
#     speed_gdf = gpd.GeoDataFrame.from_postgis(
#         sql,
#         cur.connection,
#         geom_col="geometry_3161",
#         crs="EPSG:3161",
#         params=params
#     )

#     # 3) reproject to WGS84 for display on a Leaflet map
#     speed_gdf = speed_gdf.to_crs(epsg=4326)

#     # 4) init map centered on all segments
#     center = speed_gdf.geometry.unary_union.centroid
#     m = folium.Map(
#         location=[center.y, center.x],
#         tiles="CartoDB positron",
#         zoom_start=12,
#         control_scale=True
#     )

#     # 5) add each segment with a hover‐tooltip showing expected vs actual speed
#     for _, row in speed_gdf.iterrows():
#         # extract lat/lon pairs
#         coords = [(lat, lon) for lon, lat in row.geometry.coords]
#         tooltip = (
#             f"Expected: {row.expected_speed_kmh:.1f} km/h<br>"
#             f"Actual: {row.actual_speed_kmh:.1f} km/h<br>"
#             f"Δ: {row.speed_delta_kmh:.1f} km/h"
#         )
#         folium.PolyLine(
#             locations=coords,
#             color="steelblue",
#             weight=3,
#             opacity=0.7,
#             tooltip=tooltip
#         ).add_to(m)

#     # 6) save
#     out_fp = os.path.join(results_path, "speed_segments_map.html")
#     m.save(out_fp)
#     print(f"✅ Speed segments map saved to '{out_fp}'.")




# def doExercise3(cur, results_path, ex3Json):
#     minDateForAverage = ex3Json["minDateForAverage"]
#     maxDateForAverage = ex3Json["maxDateForAverage"]
#     target_date = ex3Json["target_date"]
#     target_trip_id = ex3Json["target_trip_id"]
#     km_above_expected = ex3Json["km_h_above_expected"]
#     plot_speed_segments(cur,results_path,minDateForAverage,maxDateForAverage,target_date,target_trip_id,km_above_expected)


# def generate_speed_query(minDateForAverage, maxDateForAverage, target_date, target_trip_id, km_above_expected):
#     """
#     Returns a parametrized SQL query and a dict of parameters to:
#     1) compute expected speeds between stops (including geometry_3161) over a given date range,
#     2) compute actual speeds for a specific trip on a given date,
#     3) filter segments where actual_speed - expected_speed > km_above_expected.
#     """
#     query = """
# WITH expected_speed_between_stops AS (
#   SELECT
#     c.route_id,
#     c.direction_id,
#     c.from_stop_id,
#     c.to_stop_id,
#     AVG(
#       s.distance_m_3161
#       / EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure))
#       * 3.6
#     ) AS expected_speed_kmh,
#     s.geometry_3161
#   FROM connections c
#   JOIN segments s
#     ON c.route_id     = s.route_id
#    AND c.direction_id = s.direction_id
#    AND c.from_stop_id = s.start_stop_id
#    AND c.to_stop_id   = s.end_stop_id
#   WHERE
#     c.date BETWEEN %(minDateForAverage)s AND %(maxDateForAverage)s
#     AND EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure)) > 30
#   GROUP BY
#     c.route_id,
#     c.direction_id,
#     c.from_stop_id,
#     c.to_stop_id,
#     s.geometry_3161
#   ORDER BY expected_speed_kmh DESC
# ),
# speed_per_vehicle_trip AS (
#   SELECT
#     c.route_id,
#     c.direction_id,
#     c.trip_id,
#     c.from_stop_id,
#     c.to_stop_id,
#     (
#       s.distance_m_3161
#       / EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure))
#       * 3.6
#     ) AS actual_speed_kmh
#   FROM connections c
#   JOIN segments s
#     ON c.route_id     = s.route_id
#    AND c.direction_id = s.direction_id
#    AND c.from_stop_id = s.start_stop_id
#    AND c.to_stop_id   = s.end_stop_id
#   WHERE
#     c.date = %(target_date)s
#     AND c.trip_id = %(target_trip_id)s
#     AND EXTRACT(EPOCH FROM (c.t_arrival - c.t_departure)) > 30
# )
# SELECT DISTINCT ON (sv.trip_id, sv.from_stop_id, sv.to_stop_id)
#   sv.trip_id,
#   sv.from_stop_id,
#   sv.to_stop_id,
#   sv.actual_speed_kmh,
#   se.expected_speed_kmh,
#   se.geometry_3161,
#   (sv.actual_speed_kmh - se.expected_speed_kmh) AS speed_delta_kmh
# FROM speed_per_vehicle_trip sv
# JOIN expected_speed_between_stops se
#   ON sv.route_id     = se.route_id
#  AND sv.direction_id = se.direction_id
#  AND sv.from_stop_id = se.from_stop_id
#  AND sv.to_stop_id   = se.to_stop_id
# WHERE
#   sv.actual_speed_kmh - se.expected_speed_kmh > %(km_above_expected)s
# ORDER BY
#   sv.trip_id,
#   sv.from_stop_id,
#   sv.to_stop_id,
#   speed_delta_kmh DESC;
# """
#     params = {
#         "minDateForAverage": minDateForAverage,
#         "maxDateForAverage": maxDateForAverage,
#         "target_date": target_date,
#         "target_trip_id": target_trip_id,
#         "km_above_expected": km_above_expected
#     }
#     return query, params