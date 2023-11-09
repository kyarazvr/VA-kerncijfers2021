#!/usr/bin/env python
# coding: utf-8

# In[ ]:

#pip install cbsodata
#pip install streamlit-folium

import requests
import pandas as pd
import cbsodata
import geopandas as gpd
import branca
import plotly.express as px
#import matplot
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from sklearn import linear_model
import seaborn as sns  
import matplotlib.pyplot as plt  
import folium
import folium.plugins
from folium.features import GeoJsonPopup
import statsmodels.api as sm 


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
    CBS2021['Gemeentenaam_1'] = CBS2021['Gemeentenaam_1'].str.strip()

    gemeente_data2021 = CBS2021[CBS2021['SoortRegio_2'] == 'Gemeente']
    buurten_data2021 = CBS2021[CBS2021['SoortRegio_2'] == 'Buurt']
    amsterdam_gemeente_list = ['Aalsmeer', 'Amstelveen', 'Amsterdam', 'Beemster', 'Diemen', 'Edam-Volendam', 'Haarlemmermeer', 'Landsmeer', 'Oostzaan', 'Ouder-Amstel', 'Purmerend', 'Uithoorn', 'Waterland', 'Wormerland', 'Zaanstad', 'Zeevang']
    amsterdam_data2021 = CBS2021[CBS2021['Gemeentenaam_1'].isin(amsterdam_gemeente_list)]
    #elektriciteit
    amsterdam_e= amsterdam_data2021[['ID',
                                 'WijkenEnBuurten',
                                 'Gemeentenaam_1',
                                 'SoortRegio_2',
                                 'AantalInwoners_5',
                                 'GemiddeldElektriciteitsverbruikTotaal_47',
                                'Bevolkingsdichtheid_33',
                                'GemiddeldeWOZWaardeVanWoningen_35',
                                'Appartement_48',
                                'Tussenwoning_49',
                                'Hoekwoning_50',
                                'TweeOnderEenKapWoning_51',
                                'VrijstaandeWoning_52',
                                'Huurwoning_53',
                                'EigenWoning_54',
                                 'HuishoudensTotaal_28']]

    id_vars = ['ID',
           'WijkenEnBuurten',
           'Gemeentenaam_1',
           'SoortRegio_2',
           'AantalInwoners_5',
           'GemiddeldElektriciteitsverbruikTotaal_47',
           'Bevolkingsdichtheid_33',
           'GemiddeldeWOZWaardeVanWoningen_35',
          'HuishoudensTotaal_28'] 
    value_vars = ['Appartement_48', 'Tussenwoning_49', 'Hoekwoning_50', 'TweeOnderEenKapWoning_51', 'VrijstaandeWoning_52', 'Huurwoning_53', 'EigenWoning_54']

    amsterdam_e_mvr = pd.melt(amsterdam_e, id_vars=id_vars, value_vars=value_vars, var_name='Type_woning', value_name='Count')
    amsterdam_e_mvr_1 = amsterdam_e_mvr.dropna()

    #gas
    amsterdam_g= amsterdam_data2021[['ID',
                                 'WijkenEnBuurten',
                                 'Gemeentenaam_1',
                                 'SoortRegio_2',
                                 'AantalInwoners_5',
                                 'GemiddeldElektriciteitsverbruikTotaal_47',
                                'Bevolkingsdichtheid_33',
                                'GemiddeldeWOZWaardeVanWoningen_35',                                 
                                 'GemiddeldAardgasverbruikTotaal_55',
                                 'Appartement_56',
                                 'Tussenwoning_57',
                                 'Hoekwoning_58',
                                 'TweeOnderEenKapWoning_59',
                                 'VrijstaandeWoning_60',
                                 'Huurwoning_61',
                                 'EigenWoning_62',
                                'HuishoudensTotaal_28']]

    id_vars = ['ID',
           'WijkenEnBuurten',
           'Gemeentenaam_1',
           'SoortRegio_2',
           'AantalInwoners_5',
           'GemiddeldAardgasverbruikTotaal_55',
           'Bevolkingsdichtheid_33',
           'GemiddeldeWOZWaardeVanWoningen_35',
          'HuishoudensTotaal_28'] 
    value_vars = ['Appartement_56', 'Tussenwoning_57', 'Hoekwoning_58', 'TweeOnderEenKapWoning_59', 'VrijstaandeWoning_60', 'Huurwoning_61', 'EigenWoning_62']

    amsterdam_g_mvr = pd.melt(amsterdam_g, id_vars=id_vars, value_vars=value_vars, var_name='Type_woning', value_name='Count')
    amsterdam_g_mvr_1 = amsterdam_g_mvr.dropna()

    return gdf, CBS2021, gemeente_data2021, buurten_data2021, amsterdam_data2021, amsterdam_e_mvr,amsterdam_e_mvr_1, amsterdam_g_mvr, amsterdam_g_mvr_1

@st.cache_data
def prepare_geojson(CBS2021):
    # Filter en converteer het DataFrame voor elk regio type naar GeoJSON
    gemeente_gdf = CBS2021[CBS2021['SoortRegio_2'] == 'Gemeente']
    gemeente_geo_json = gemeente_gdf.to_json()
    
    wijk_gdf = CBS2021[CBS2021['SoortRegio_2'] == 'Wijk']
    wijk_geo_json = wijk_gdf.to_json()
    
    buurt_gdf = CBS2021[CBS2021['SoortRegio_2'] == 'Buurt']
    buurt_geo_json = buurt_gdf.to_json()

    #gemeente_geo_json, wijk_geo_json, buurt_geo_json = prepare_geojson(CBS2021)
    
    return gemeente_geo_json, wijk_geo_json, buurt_geo_json


@st.cache_data
def get_geojson_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Fout bij het ophalen van de data: {response.status_code}")

gdf, CBS2021, gemeente_data2021, buurten_data2021, amsterdam_data2021, amsterdam_e_mvr,amsterdam_e_mvr_1, amsterdam_g_mvr, amsterdam_g_mvr_1 = load_data()
geojson_data = get_geojson_data("https://api.data.amsterdam.nl/v1/aardgasvrijezones/buurt/?_format=geojson")

Ams_gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
Ams_gdf['centroid'] = Ams_gdf['geometry'].centroid
Ams_gdf['centroid_x'] = Ams_gdf['centroid'].x
Ams_gdf['centroid_y'] = Ams_gdf['centroid'].y
Ams_gdf = Ams_gdf[Ams_gdf['toelichting'].str.contains('All electric:|Al \(bijna\) volledig op het warmtenet', na=False)]

#-----------------------------------------------------------------------------------#
# st.title("Kerncijfers 2021 analyse voor elektriciteits- en gasverbruik")

page = st.sidebar.selectbox("Kies een Pagina",['Gasverbruik Analyse', 'Elektriciteitsverbruik Analyse'])

if page == 'Gasverbruik Analyse':
    st.title("Data analyse voor het gasverbruik in Nederland in 2021")

    st.write("""In 2021 onderging Nederland een grondige analyse
              van het elektriciteits- en gasverbruik. Kerncijfers
              onthulden gedetailleerde inzichten in het gasverbruik,
              waarbij data-analyse een cruciale rol speelde.
              De resultaten bieden waardevolle informatie voor het begrijpen
              van energieconsumptiepatronen en het bevorderen van duurzame energiepraktijken.""")
    
    tab1, tab2,tab3 = st.tabs(["Regio", "Kaart van NL", "Statische analyse Amsterdam"])

    with tab1:
    # #Boxplot en Histogram Elektriciteit

    # #Boxpot

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

    # with tab2:
     
    #     #Folium Map Aardgasverbruik

    #     # Bepaal het centrum van je kaart
    #     center = [52.0907, 5.1214]

    #     # Maak een Folium kaartobject
    #     m = folium.Map(location=center, tiles='cartodb positron', zoom_start=7)

    #     # Functie om popup toe te voegen aan een laag
    #     def add_choropleth(geo_json_data, name, columns, fill_color, legend_name):
    #         layer = folium.Choropleth(
    #             geo_data=geo_json_data,
    #             name=name,
    #             data=CBS2021,
    #             columns=columns,
    #             key_on='properties.Codering_3',
    #             fill_color=fill_color,
    #             fill_opacity=0.7,
    #             line_opacity=0.2,
    #             legend_name=legend_name,
    #             highlight=True,
    #             overlay=True,
    #             show=(name == 'Gemeenten')  # Alleen de 'Gemeenten' laag standaard tonen
    #         )

    #         # Maak een pop-up voor de laag en voeg deze toe
    #         popup = GeoJsonPopup(
    #             fields=['statnaam', columns[1]],
    #             aliases=['Locatie: ', 'Gem. Aardgasverbruik: '],
    #             localize=True,
    #             labels=True,
    #             style="background-color: white;"
    #         )
            
    #         # Voeg de pop-up toe aan de geojson laag van de Choropleth
    #         layer.geojson.add_child(popup)
            
    #         # Voeg de Choropleth laag toe aan de kaart
    #         layer.add_to(m)

    #     gemeente_geo_json, wijk_geo_json, buurt_geo_json = prepare_geojson(CBS2021)

    #     # Voeg de GeoJSON van gemeenten toe aan de kaart met tooltips
    #     add_choropleth(gemeente_geo_json, 'Gemeenten', ['Codering_3', 'GemiddeldAardgasverbruikTotaal_55'], 'YlOrRd', 'Gemiddeld Aardgasverbruik per Gemeente in 2021')

    #     # Voeg de GeoJSON van wijken toe aan de kaart met tooltips
    #     add_choropleth(wijk_geo_json, 'Wijken', ['Codering_3', 'GemiddeldAardgasverbruikTotaal_55'], 'BuGn', 'Gemiddeld Aardgasverbruik per Wijk in 2021')

    #     # Voeg de GeoJSON van buurten toe aan de kaart met tooltips
    #     add_choropleth(buurt_geo_json, 'Buurten', ['Codering_3', 'GemiddeldAardgasverbruikTotaal_55'], 'YlGnBu', 'Gemiddeld Aardgasverbruik per Buurt in 2021')


    #     # Maak een FeatureGroup voor de markers
    #     markers_layer = folium.FeatureGroup(name='Gasvrij', show=False)


    #     # Loop door de rijen in je GeoDataFrame
    #     for idx, row in Ams_gdf.iterrows():
    #         # Voeg een marker toe aan de markers_layer
    #         folium.Marker(
    #             location=[row['centroid_y'], row['centroid_x']],  # Gebruik de x- en y-coördinaten
    #             tooltip=str(row['toelichting']),  # Zet de inhoud van 'Toelichting' om naar een string en gebruik als tooltip
    #             popup=folium.Popup(str(row['toelichting']), max_width=450),  # Voeg eventueel een popup toe
    #             show=False
    #         ).add_to(markers_layer)

    #     # Voeg de markers_layer toe aan de kaart
    #     markers_layer.add_to(m)

    #     # Volledig scherm
    #     folium.plugins.Fullscreen(
    #         position="topright",
    #         title="Volledig scherm",
    #         title_cancel="Sluiten",
    #         force_separate_button=True,
    #     ).add_to(m)

    #     # Voeg een laag controle toe om de choropleth aan of uit te zetten
    #     folium.LayerControl().add_to(m)

    #     # Toon de kaart
    #     st_folium(m, width=725, height=600)

    with tab3:
        st.subheader("Residuenplot voor de gebruikte variabelen")
        keuze = st.selectbox("Kies een variabele",['WOZ waarde','huishoudengrootte'])

        if keuze =='WOZ waarde':

            fig, ax = plt.subplots()
            sns.residplot(data=amsterdam_g_mvr_1, x="GemiddeldAardgasverbruikTotaal_55", y="GemiddeldeWOZWaardeVanWoningen_35", ax=ax)
            plt.title('Residuenplot')
            plt.xlabel('Gemiddelde gasverbruik')
            plt.ylabel('Gemiddelde WOZ Waarde')

            st.pyplot(fig)

        if keuze == 'huishoudengrootte':
            amsterdam_g_mvr_12 = amsterdam_g_mvr_1[amsterdam_g_mvr_1['HuishoudensTotaal_28']< 50000]
            fig, ax = plt.subplots()
            sns.residplot(data=amsterdam_g_mvr_12, x="GemiddeldAardgasverbruikTotaal_55", y="HuishoudensTotaal_28", ax=ax)
            plt.title('Residuenplot')
            plt.xlabel('Gemiddelde gasverbruik')
            plt.ylabel('Huishoudensgrootte')

            st.pyplot(fig)

        #Meervoudige regressie gas
        X = amsterdam_g_mvr_1[['Count',
                'GemiddeldeWOZWaardeVanWoningen_35',
                'HuishoudensTotaal_28']]  
        
        X = sm.add_constant(X)

        y = amsterdam_g_mvr_1['GemiddeldAardgasverbruikTotaal_55']

        mlr_model = sm.OLS(y, X).fit()

        predicted_values = mlr_model.predict(X)

        scatter_fig = px.scatter(amsterdam_e_mvr_1, x=y, y=predicted_values, title='Meervoudige regressie voor Gasverbruik',
                                labels={'x': 'Actuele waardes', 'y': 'voorspelde waardes'},
                                trendline= 'ols',trendline_color_override='red')

        # Show the plot
        st.plotly_chart(scatter_fig)

# #-----------------------------------------------------------------------------------#

if page == 'Elektriciteitsverbruik Analyse':
    st.title("Data analyse voor het elektriciteitsverbruik in Nederland in 2021")

    tab1, tab2,tab3 = st.tabs(["Regio", "Kaart van NL", "Statische analyse Amsterdam"])
    #Boxplot en Histogram Elektriciteit
    with tab1:
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

    # with tab2:
        # #Folium Map Elektriciteit

        # # Bepaal het centrum van je kaart
        # center = [52.0907, 5.1214]

        # # Maak een Folium kaartobject
        # m = folium.Map(location=center, tiles='cartodb positron', zoom_start=7)

        # # Functie om popup toe te voegen aan een laag
        # def add_choropleth(geo_json_data, name, columns, fill_color, legend_name):
        #     layer = folium.Choropleth(
        #         geo_data=geo_json_data,
        #         name=name,
        #         data=CBS2021,
        #         columns=columns,
        #         key_on='properties.Codering_3',
        #         fill_color=fill_color,
        #         fill_opacity=0.7,
        #         line_opacity=0.2,
        #         legend_name=legend_name,
        #         highlight=True,
        #         overlay=True,
        #         show=(name == 'Gemeenten')  # Alleen de 'Gemeenten' laag standaard tonen
        #     )

        #     # Maak een pop-up voor de laag en voeg deze toe
        #     popup = GeoJsonPopup(
        #         fields=['statnaam', columns[1]],
        #         aliases=['Locatie: ', 'Gem. Elektriciteitsverbruik: '],
        #         localize=True,
        #         labels=True,
        #         style="background-color: white;"
        #     )
            
        #     # Voeg de pop-up toe aan de geojson laag van de Choropleth
        #     layer.geojson.add_child(popup)
            
        #     # Voeg de Choropleth laag toe aan de kaart
        #     layer.add_to(m)

        # # Voeg de GeoJSON van gemeenten toe aan de kaart met tooltips
        # add_choropleth(gemeente_geo_json, 'Gemeenten', ['Codering_3', 'GemiddeldElektriciteitsverbruikTotaal_47'], 'YlOrRd', 'Gemiddeld Elektriciteitsverbruik per Gemeente in 2021')

        # # Voeg de GeoJSON van wijken toe aan de kaart met tooltips
        # add_choropleth(wijk_geo_json, 'Wijken', ['Codering_3', 'GemiddeldElektriciteitsverbruikTotaal_47'], 'BuGn', 'Gemiddeld Elektriciteitsverbruik per Wijk in 2021')

        # # Voeg de GeoJSON van buurten toe aan de kaart met tooltips
        # add_choropleth(buurt_geo_json, 'Buurten', ['Codering_3', 'GemiddeldElektriciteitsverbruikTotaal_47'], 'YlGnBu', 'Gemiddeld Elektriciteitsverbruik per Buurt in 2021')

        # # Volledig scherm
        # folium.plugins.Fullscreen(
        #     position="topright",
        #     title="Volledig scherm",
        #     title_cancel="Sluiten",
        #     force_separate_button=True,
        # ).add_to(m)

        # # Voeg een laag controle toe om de choropleth aan of uit te zetten
        # folium.LayerControl().add_to(m)

        # # Toon de kaart
        # st_folium(m, width=725, height=600)

# #-----------------------------------------------------------------------------------#
    with tab3:
        st.subheader("Residuenplot voor de gebruikte variabelen")
        keuze = st.selectbox("Kies een variabele",['WOZ waarde','huishoudengrootte'])

        if keuze =='WOZ waarde':

            fig, ax = plt.subplots()
            sns.residplot(data=amsterdam_e_mvr_1, x="GemiddeldElektriciteitsverbruikTotaal_47", y="GemiddeldeWOZWaardeVanWoningen_35", ax=ax)
            plt.title('Residuenplot')
            plt.xlabel('Gemiddelde elektriciteitsverbruik')
            plt.ylabel('Gemiddelde WOZ Waarde')

            st.pyplot(fig)

        if keuze == 'huishoudengrootte':
            amsterdam_e_mvr_12 = amsterdam_e_mvr_1[amsterdam_e_mvr_1['HuishoudensTotaal_28']<100000]
            fig, ax = plt.subplots()
            sns.residplot(data=amsterdam_e_mvr_12, x="GemiddeldElektriciteitsverbruikTotaal_47", y="HuishoudensTotaal_28", ax=ax)
            plt.title('Residuenplot')
            plt.xlabel('Gemiddelde elektriciteitsverbruik')
            plt.ylabel('Huishoudensgrootte')

            st.pyplot(fig)
        st.subheader("")
        st.subheader('Voorspelling elektriciteitsgebruik')
                # Define the independent variables (features) for MLR
        X = amsterdam_e_mvr_1[['Bevolkingsdichtheid_33',
                'GemiddeldeWOZWaardeVanWoningen_35',
                'HuishoudensTotaal_28']]  # Add more columns as needed

        # Add a constant (intercept) to the independent variables
        X = sm.add_constant(X)

        # Define the dependent variable
        y = amsterdam_e_mvr_1['GemiddeldElektriciteitsverbruikTotaal_47']

        # Fit the MLR model
        mlr_model = sm.OLS(y, X).fit()

        # Get the predicted values
        predicted_values = mlr_model.predict(X)

        # Create a scatter plot with the actual and predicted values
        scatter_fig = px.scatter(amsterdam_e_mvr_1, x=y, y=predicted_values, title='actuele vs voorspelde',
                                labels={'x': 'actuele elektriciteitsverbruik(kWh)', 'y': 'Voorspelde elektriciteitsverbruik'},
                                trendline= 'ols',trendline_color_override='red')

        # Show the plot
        st.plotly_chart(scatter_fig)

