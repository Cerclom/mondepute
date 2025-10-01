import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# Connexion à la base SQLite
conn = sqlite3.connect("sql/mondepute.sqlite")

st.title("Tableau de bord de l'assemblée nationale (legislature 17)")

# ------------------------
# Création des onglets
# ------------------------
tab1, tab2, tab3 = st.tabs(["Informations générales", "Scrutins", "Députés"])

# ------------------------
# Onglet 1 : Vue d'ensemble
# ------------------------

with tab1:
    st.subheader("Vue d'ensemble")

    #Nombre total de députés
    nb_deputes = pd.read_sql("SELECT COUNT(distinct uid) AS NB FROM depute", conn)["NB"][0]

    #Nombre de scrutins
    nb_scrutins = pd.read_sql("SELECT COUNT(distinct uid) AS NB FROM vote", conn)["NB"][0]

    #Affichage en tableau
    col1, col2 = st.columns(2)
    col1.metric("Nombre de députés", nb_deputes)
    col2.metric("Nombre de scrutins", nb_scrutins)

    #Proportion de refus et d'adoption
    #Récupération des données avec Pandas :
    graph_pie = pd.read_sql("SELECT codesort, COUNT(*) AS NB FROM vote GROUP BY codesort", conn)
    # Remplacer les valeurs pour avoir des majuscules
    graph_pie["codesort"] = graph_pie["codesort"].replace({
        "adopté": "Adopté",
        "rejeté": "Rejeté"
    })
    #Affichage du graphique avec Streamlit:
    fig = px.pie(
        graph_pie, 
        values="NB",
        names="codesort",
        title ="Proportion de scrutins adoptés et rejetés",
        color= "codesort",
        color_discrete_map={"Adopté":"green", "Rejeté":"red"}
    )
    fig.update_traces(
        hovertemplate="%{value}"  # n'affiche que le nombre
    )
    #Affichage dans Streamlit
    st.plotly_chart(fig)
