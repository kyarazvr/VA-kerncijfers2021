#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#pip install streamlit-folium

import requests
import pandas as pd
import cbsodata
import geopandas as gpd
import branca
import plotly.express as px
import folium
import folium.plugins
from folium.features import GeoJsonPopup


import streamlit as st
from streamlit_folium import st_folium


# In[ ]:


#Streamlit data laden
@st.cache_data
def load_data():
    gdf = gpd.read_file('cbsgebiedsindelingen2021.gpkg', layer='gemeente_gegeneraliseerd_2021')
    gdf2 = gpd.read_file('cbsgebiedsindelingen2021.gpkg', layer='buurt_gegeneraliseerd_2021')
    gdf3 = gpd.read_file('cbsgebiedsindelingen2021.gpkg', layer='wijk_gegeneraliseerd_2021')
    gdf = pd.concat([gdf, gdf2, gdf3], ignore_index=True)
    gdf = gdf.to_crs(epsg=4326)
    CBS2021 = pd.DataFrame(cbsodata.get_data('85039NED'))
    CBS2021 = CBS2021[CBS2021['SoortRegio_2'] != 'Land']
    CBS2021['Codering_3'] = CBS2021['Codering_3'].str.strip()
    CBS2021['SoortRegio_2'] = CBS2021['SoortRegio_2'].str.strip()
    return gdf, CBS2021

@st.cache_data
def get_geojson_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Fout bij het ophalen van de data: {response.status_code}")

gdf, CBS2021 = load_data()
geojson_data = get_geojson_data("https://api.data.amsterdam.nl/v1/aardgasvrijezones/buurt/?_format=geojson")

Ams_gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
Ams_gdf['centroid'] = Ams_gdf['geometry'].centroid
Ams_gdf['centroid_x'] = Ams_gdf['centroid'].x
Ams_gdf['centroid_y'] = Ams_gdf['centroid'].y
Ams_gdf = Ams_gdf[Ams_gdf['toelichting'].str.contains('All electric:|Al \(bijna\) volledig op het warmtenet', na=False)]

#-----------------------------------------------------------------------------------#

#Boxplot en Histogram Elektriciteit

#Boxpot

fig = px.box(
    CBS2021, 
    x="GemiddeldAardgasverbruikTotaal_55", 
    y="SoortRegio_2",
    labels={
        "GemiddeldAardgasverbruikTotaal_55": "Gemiddeld Aardgasverbruik Totaal",
        "SoortRegio_2": "Soort Regio"
    },
    title="Boxplot van het Gemiddeld Aardgasverbruik per Soort Regio"
)

fig.update_layout(
    xaxis_title="Gemiddeld Aardgasverbruik Totaal (m³)",
    yaxis_title="Soort Regio",
)

st.plotly_chart(fig)

#Histogram

# Dropdown menu voor de keuze van de soort regio
regio_keuze = st.selectbox(
    'Kies een regio type:',
    options=['Gemeente', 'Wijk', 'Buurt'],
    index=0  # Standaard geselecteerde optie
)

# Filter de DataFrame op basis van de geselecteerde regio
gefilterde_data = CBS2021[CBS2021['SoortRegio_2'] == regio_keuze]

# Maak een histogram van de gefilterde data voor GemiddeldAardgasverbruikTotaal_55
fig = px.histogram(
    gefilterde_data, 
    x="GemiddeldAardgasverbruikTotaal_55",
    labels={'GemiddeldAardgasverbruikTotaal_55': 'Gemiddeld Aardgasverbruik Totaal'},
    title=f'Histogram van Gemiddeld Aardgasverbruik per {regio_keuze}'
)

# Update layout gebaseerd op de gekozen regio
fig.update_layout(
    xaxis_title='Gemiddeld Aardgasverbruik Totaal (m³)',
    yaxis_title=f'Aantal {regio_keuze}'
)

# Toon de plot in Streamlit
st.plotly_chart(fig)


#Folium Map Aardgasverbruik

# Bepaal het centrum van je kaart
center = [52.0907, 5.1214]

# Maak een Folium kaartobject
m = folium.Map(location=center, tiles='cartodb positron', zoom_start=7)

# Functie om popup toe te voegen aan een laag
def add_choropleth(geo_json_data, name, columns, fill_color, legend_name):
    layer = folium.Choropleth(
        geo_data=geo_json_data,
        name=name,
        data=CBS2021,
        columns=columns,
        key_on='properties.Codering_3',
        fill_color=fill_color,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name,
        highlight=True,
        overlay=True,
        show=(name == 'Gemeenten')  # Alleen de 'Gemeenten' laag standaard tonen
    )

    # Maak een pop-up voor de laag en voeg deze toe
    popup = GeoJsonPopup(
        fields=['statnaam', columns[1]],
        aliases=['Locatie: ', 'Gem. Aardgasverbruik: '],
        localize=True,
        labels=True,
        style="background-color: white;"
    )
    
    # Voeg de pop-up toe aan de geojson laag van de Choropleth
    layer.geojson.add_child(popup)
    
    # Voeg de Choropleth laag toe aan de kaart
    layer.add_to(m)

# Voeg de GeoJSON van gemeenten toe aan de kaart met tooltips
add_choropleth(gemeente_geo_json, 'Gemeenten', ['Codering_3', 'GemiddeldAardgasverbruikTotaal_55'], 'YlOrRd', 'Gemiddeld Aardgasverbruik per Gemeente in 2021')

# Voeg de GeoJSON van wijken toe aan de kaart met tooltips
add_choropleth(wijk_geo_json, 'Wijken', ['Codering_3', 'GemiddeldAardgasverbruikTotaal_55'], 'BuGn', 'Gemiddeld Aardgasverbruik per Wijk in 2021')

# Voeg de GeoJSON van buurten toe aan de kaart met tooltips
add_choropleth(buurt_geo_json, 'Buurten', ['Codering_3', 'GemiddeldAardgasverbruikTotaal_55'], 'YlGnBu', 'Gemiddeld Aardgasverbruik per Buurt in 2021')


# Maak een FeatureGroup voor de markers
markers_layer = folium.FeatureGroup(name='Gasvrij', show=False)


# Loop door de rijen in je GeoDataFrame
for idx, row in Ams_gdf.iterrows():
    # Voeg een marker toe aan de markers_layer
    folium.Marker(
        location=[row['centroid_y'], row['centroid_x']],  # Gebruik de x- en y-coördinaten
        tooltip=str(row['toelichting']),  # Zet de inhoud van 'Toelichting' om naar een string en gebruik als tooltip
        popup=folium.Popup(str(row['toelichting']), max_width=450),  # Voeg eventueel een popup toe
        show=False
    ).add_to(markers_layer)

# Voeg de markers_layer toe aan de kaart
markers_layer.add_to(m)

# Volledig scherm
folium.plugins.Fullscreen(
    position="topright",
    title="Volledig scherm",
    title_cancel="Sluiten",
    force_separate_button=True,
).add_to(m)

# Voeg een laag controle toe om de choropleth aan of uit te zetten
folium.LayerControl().add_to(m)

# Toon de kaart
st_folium(m, width=725, height=600)

#-----------------------------------------------------------------------------------#

#Boxplot en Histogram Elektriciteit

#Boxplot
fig = px.box(
    CBS2021, 
    x="GemiddeldElektriciteitsverbruikTotaal_47", 
    y="SoortRegio_2",
    labels={
        "GemiddeldElektriciteitsverbruikTotaal_47": "Gemiddeld Elektriciteitsverbruik Totaal",
        "SoortRegio_2": "Soort Regio"
    },
    title="Boxplot van het Gemiddeld Elektriciteitsverbruik per Soort Regio"
)

fig.update_layout(
    xaxis_title="Gemiddeld Elektriciteitsverbruik Totaal (kWh)",
    yaxis_title="Soort Regio",
)

fig.show()
st.plotly_chart(fig)


#Histogram
# Dropdown menu voor de keuze van de soort regio
regio_keuze = st.selectbox(
    'Kies een regio type:',
    options=['Gemeente', 'Wijk', 'Buurt'],
    index=0  # Standaard geselecteerde optie (0 is de eerste optie)
)

# Filter de DataFrame op basis van de geselecteerde regio
gefilterde_data = CBS2021[CBS2021['SoortRegio_2'] == regio_keuze]

# Maak een histogram van de gefilterde data
fig = px.histogram(
    gefilterde_data, 
    x="GemiddeldElektriciteitsverbruikTotaal_47",
    labels={'GemiddeldElektriciteitsverbruikTotaal_47': 'Gemiddeld Elektriciteitsverbruik Totaal'},
    title=f'Histogram van Gemiddeld Elektriciteitsverbruik per {regio_keuze}'
)

# Update layout gebaseerd op de gekozen regio
fig.update_layout(
    xaxis_title='Gemiddeld Elektriciteitsverbruik Totaal (kWh)',
    yaxis_title=f'Aantal {regio_keuze}'
)

# Toon de plot in Streamlit
st.plotly_chart(fig)


#Folium Map Elektriciteit

# Bepaal het centrum van je kaart
center = [52.0907, 5.1214]

# Maak een Folium kaartobject
m = folium.Map(location=center, tiles='cartodb positron', zoom_start=7)

# Functie om popup toe te voegen aan een laag
def add_choropleth(geo_json_data, name, columns, fill_color, legend_name):
    layer = folium.Choropleth(
        geo_data=geo_json_data,
        name=name,
        data=CBS2021,
        columns=columns,
        key_on='properties.Codering_3',
        fill_color=fill_color,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name,
        highlight=True,
        overlay=True,
        show=(name == 'Gemeenten')  # Alleen de 'Gemeenten' laag standaard tonen
    )

    # Maak een pop-up voor de laag en voeg deze toe
    popup = GeoJsonPopup(
        fields=['statnaam', columns[1]],
        aliases=['Locatie: ', 'Gem. Elektriciteitsverbruik: '],
        localize=True,
        labels=True,
        style="background-color: white;"
    )
    
    # Voeg de pop-up toe aan de geojson laag van de Choropleth
    layer.geojson.add_child(popup)
    
    # Voeg de Choropleth laag toe aan de kaart
    layer.add_to(m)

# Voeg de GeoJSON van gemeenten toe aan de kaart met tooltips
add_choropleth(gemeente_geo_json, 'Gemeenten', ['Codering_3', 'GemiddeldElektriciteitsverbruikTotaal_47'], 'YlOrRd', 'Gemiddeld Elektriciteitsverbruik per Gemeente in 2021')

# Voeg de GeoJSON van wijken toe aan de kaart met tooltips
add_choropleth(wijk_geo_json, 'Wijken', ['Codering_3', 'GemiddeldElektriciteitsverbruikTotaal_47'], 'BuGn', 'Gemiddeld Elektriciteitsverbruik per Wijk in 2021')

# Voeg de GeoJSON van buurten toe aan de kaart met tooltips
add_choropleth(buurt_geo_json, 'Buurten', ['Codering_3', 'GemiddeldElektriciteitsverbruikTotaal_47'], 'YlGnBu', 'Gemiddeld Elektriciteitsverbruik per Buurt in 2021')

# Volledig scherm
folium.plugins.Fullscreen(
    position="topright",
    title="Volledig scherm",
    title_cancel="Sluiten",
    force_separate_button=True,
).add_to(m)

# Voeg een laag controle toe om de choropleth aan of uit te zetten
folium.LayerControl().add_to(m)

# Toon de kaart
st_folium(m, width=725, height=600)

#-----------------------------------------------------------------------------------#

