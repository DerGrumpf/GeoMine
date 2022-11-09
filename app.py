from flask import Flask
import folium
from folium.plugins import MiniMap
import json
from model import Tag

app = Flask(__name__)

main_server = Tag(
    ip="130.61.111.142",
    isp="Oracle Cloud",
    city="60310 Frankfurt am Main",
    country="Germany, DE",
    coordinates=(
      50.10490,
      8.62950
    ),
    hops=1,
    is_alive=True
  )

tooltip = "Klicke für mehr Infos"


def get_map():
    map = folium.Map(
        location=[51, 11],
        tiles='https://{s}.tile.openstreetmap.de/{z}/{x}/{y}.png',
        attr='Servers & Routers',
        zoom_start=6,
        zoom_control=True,
        prefer_canvas=True,
        control_scale=True,
        no_touch=True
        )
    MiniMap().add_to(map)
    return map

def get_server_marker(tag):
    popup = folium.Popup(
            html='''
            <strong>{}</strong><br>
            {}<br>
            <small>{} {}</small>
            '''.format(tag.ip, tag.isp, tag.city, tag.country)
            )

    icon = folium.Icon(
            icon='fa-solid fa-database',
            prefix='fa',
            color='blue',
            )

    server = folium.Marker(
            location=tag.coordinates,
            popup=popup,
            icon=icon,
            tooltip=tooltip
            )

    return server

def get_client_marker(tag):
    popup = folium.Popup(
            html='''
            <strong>{}</strong><br>
            {}<br>
            <small>{} {}</small>
            '''.format(tag.ip, tag.isp, tag.city, tag.country)
            )

    icon = folium.Icon(
            icon='fa-solid fa-desktop',
            prefix='fa',
            color='green' if tag.is_alive else 'red',
            )

    client = folium.Marker(
            location=tag.coordinates,
            popup=popup,
            icon=icon,
            tooltip=tooltip
            )

    return client

def get_router_marker(tag):
    popup = folium.Popup(
            html='''
            <strong>{}</strong><br>
            {}<br>
            <small>{} {}</small>
            '''.format(tag.ip, tag.isp, tag.city, tag.country)
            )

    icon = folium.Icon(
                icon="fa-solid fa-server",
                prefix='fa',
                color='purple',
                )

    router = folium.Marker(
            location=tag.coordinates,
            popup=popup,
            icon=icon,
            tooltip=tooltip
            )

    return router

def get_client_data():
    with open('ips.json', 'r') as f:
        data = json.load(f)
        for d in data:
            yield Tag.from_dict(d)

plz = {d.plz for d in get_client_data()}

@app.route('/')
def index():
    map = get_map()
    clients = folium.FeatureGroup('Clients')
    servers = folium.FeatureGroup('Servers')

    get_server_marker(main_server).add_to(servers)

    for d in get_client_data():
        get_client_marker(d).add_to(clients)

        group = folium.FeatureGroup(d.ip, show=False)
        coords = list()
        for t in d.trace[1:-1]:
            get_router_marker(t).add_to(group)
            coords.append(t.coordinates)
        if coords:
            coords.insert(0, main_server.coordinates)
            coords.append(d.coordinates)
            line = folium.PolyLine(coords)
            line.add_to(group)
        group.add_to(map)

    clients.add_to(map)
    servers.add_to(map)
    folium.LayerControl(collapsed=False).add_to(map)
    return map._repr_html_()

if __name__ == '__main__':
    #app.run(debug=True)
    
    import sys, pprint
    print(plz)

    with open('postleitzahlen.topojson', 'r') as f:
        data = json.load(f)
        geos = data['objects']['postleitzahlen']['geometries']
        for g in geos:
            p = g['properties']['postcode']
            if p in plz:
                print(g)


