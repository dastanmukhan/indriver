import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium


file_path = r"C:\Users\User\PycharmProjects\Indrive\geo_locations_with_time_clean.csv"


df = pd.read_csv(file_path)


df["time"] = pd.to_datetime(df["time"], format="%I:%M %p", errors="coerce")
df = df.dropna(subset=["time"])


df["hour"] = df["time"].dt.hour
df["am_pm"] = df["time"].dt.strftime("%p")  # "AM" или "PM"


st.title("🚖 Интерактивная тепловая карта спроса по времени")
st.markdown("Выберите час, чтобы увидеть, где больше всего заказов и сколько такси нужно направить в каждую зону.")


selected_hour = st.slider("Выберите час (0-23):", 0, 23, 6)


filtered_df = df[df["hour"] == selected_hour]

st.write(f"📊 Найдено заказов в {selected_hour}:00 — {len(filtered_df)}")


CENTER_LAT, CENTER_LNG = 51.090015, 71.425791


m = folium.Map(location=[CENTER_LAT, CENTER_LNG], zoom_start=14, tiles="CartoDB positron")


if not filtered_df.empty:
    heat_data = [[row["lat"], row["lng"]] for _, row in filtered_df.iterrows()]
    HeatMap(
        heat_data,
        radius=20,
        blur=15,
        min_opacity=0.2,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}
    ).add_to(m)

    
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in filtered_df.iterrows():
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=f"Заказ ID: {row['randomized_id']}<br>Время: {row['time'].strftime('%I:%M %p')}"
        ).add_to(marker_cluster)


zones = {
    "A": {"lat_min": 51.089566, "lat_max": 51.105639, "lng_min": 71.400425, "lng_max": 71.418365, "color": "red"},
    "B": {"lat_min": 51.089547, "lat_max": 51.105174, "lng_min": 71.418554, "lng_max": 71.439704, "color": "blue"},
    "C": {"lat_min": 51.076980, "lat_max": 51.089712, "lng_min": 71.418166, "lng_max": 71.439743, "color": "green"},
    "D": {"lat_min": 51.074928, "lat_max": 51.089762, "lng_min": 71.398917, "lng_max": 71.418188, "color": "orange"}
}


def count_orders_by_zone(df, zones):
    zone_counts = {}
    for zone_name, bounds in zones.items():
        zone_df = df[
            (df["lat"] >= bounds["lat_min"]) & (df["lat"] <= bounds["lat_max"]) &
            (df["lng"] >= bounds["lng_min"]) & (df["lng"] <= bounds["lng_max"])
        ]
        zone_counts[zone_name] = len(zone_df)
    return zone_counts


zone_order_counts = count_orders_by_zone(filtered_df, zones)


for zone_name, bounds in zones.items():
    count = zone_order_counts[zone_name]
    folium.Rectangle(
        bounds=[[bounds["lat_min"], bounds["lng_min"]],
                [bounds["lat_max"], bounds["lng_max"]]],
        color=bounds["color"],
        weight=0.5,
        fill=True,
        fill_opacity=0.1, 
        tooltip=f"Зона {zone_name} — заказов: {count}"
    ).add_to(m)

  
    center_lat = (bounds["lat_min"] + bounds["lat_max"]) / 2
    center_lng = (bounds["lng_min"] + bounds["lng_max"]) / 2
    folium.map.Marker(
        [center_lat, center_lng],
        icon=folium.DivIcon(
            html=f"""<div style="font-size:16px; font-weight:bold; color:{bounds['color']};">{zone_name}</div>"""
        )
    ).add_to(m)



st.subheader("🚨 Рекомендации для водителей")
for zone, count in zone_order_counts.items():
    if count > 0:
        recommended_cars = max(1, count // 3)  
        st.markdown(f"Зона **{zone}**: заказов {count}, рекомендуется **{recommended_cars} такси**")


st_folium(m, width=900, height=600)

