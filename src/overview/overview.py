import folium
from folium import plugins
m = folium.Map([41.97, 2.81])

minimap = plugins.MiniMap(toggle_display=True)
m.add_child(minimap)

folium.TileLayer("cartodbpositron").add_to(m)
folium.TileLayer("openstreetmap").add_to(m)
folium.TileLayer("Stamen Terrain").add_to(m)
folium.LayerControl(collapsed=False, position="topleft").add_to(m)

plugins.Geocoder().add_to(m)
plugins.LocateControl().add_to(m)

plugins.Fullscreen(
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
).add_to(m)

m.save("index.html")
