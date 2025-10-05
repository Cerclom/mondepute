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
    st.subheader("Vue d'ensemble de la base de données")
    
    #Dernière actualisation
    date_import = pd.read_sql("SELECT MAX(dateImport) AS DATE FROM vote", conn)["DATE"][0]
    date_dernier_vote = pd.read_sql("SELECT MAX(dateScrutin) AS DATE FROM vote", conn)["DATE"][0]
    
    #Affichage en tableau
    col1, col2 = st.columns(2)
    col1.metric("Dernière actualisation", str(date_import))
    col2.metric("Dernier vote", str(date_dernier_vote))


    #Nombre total de députés
    nb_deputes = pd.read_sql("SELECT COUNT(*) AS NB FROM mandat INNER JOIN depute ON mandat.deputeUID = depute.uid WHERE legislature = 17 AND typeOrgane = 'ASSEMBLEE' AND dateFin IS NULL", conn)["NB"][0]

    #Nombre de scrutins
    nb_scrutins = pd.read_sql("SELECT COUNT(distinct uid) AS NB FROM vote", conn)["NB"][0]

    #Affichage en tableau
    col3, col4 = st.columns(2)
    col3.metric("Nombre de députés", nb_deputes)
    col4.metric("Nombre de scrutins", nb_scrutins)


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


    #Type de vote
    st.subheader("Répartition des types de vote")
    type_de_vote = pd.read_sql("SELECT libelleTypeVote, COUNT(*) AS NB, ROUND(COUNT(*) * 100.0 /(SELECT COUNT(*) FROM vote),2) AS PCT FROM vote GROUP BY libelleTypeVote", conn)
    # Formater la colonne PCT pour afficher les décimales et rajouter le %
    type_de_vote["PCT"] = type_de_vote["PCT"].astype(float).map(lambda x: f"{x:.2f}%".replace(".", ","))
    #Renommer les colonnes
    type_de_vote.columns = ["Type de vote", "Nombre", "%"]
    #Ajout ligne total
    total_row = pd.DataFrame({
        "Type de vote": ["Total"],
        "Nombre": [type_de_vote["Nombre"].sum()],
        "%": ["100,00%"]
    })
    type_de_vote = pd.concat([type_de_vote, total_row], ignore_index=True)
    #Affichage tableau
    st.dataframe(type_de_vote)

with tab3:
    # Liste des législatures disponibles
    df_legislatures = pd.read_sql(
        "SELECT DISTINCT legislature FROM mandat WHERE legislature IS NOT NULL ORDER BY legislature",
        conn
    )

    # Nettoyage : suppression NaN et conversion en int
    df_legislatures["legislature"] = (
        df_legislatures["legislature"]
        .dropna()
        .astype(int)
    )

    # Sélecteur de législature
    legislature = st.selectbox(
        "Choisissez une législature :",
        sorted(df_legislatures["legislature"].tolist(), reverse=True)  # du plus récent au plus ancien
    )

    # Législature maximale
    max_legislature = df_legislatures["legislature"].max()

    # Construction de la requête selon le cas
    if legislature == max_legislature:
        # Législature actuelle → députés en cours
        query_deputes = f"""
            SELECT depute.uid, depute.civilite, depute.nom, depute.prenom
            FROM mandat
            INNER JOIN depute ON mandat.deputeUID = depute.uid
            WHERE legislature = {legislature}
            AND typeOrgane = 'ASSEMBLEE'
            AND dateFin IS NULL
            ORDER BY depute.nom
        """
    else:
        # Ancienne législature → députés dont la dateFin est la plus récente
        query_deputes = f"""
            SELECT depute.uid, depute.civilite, depute.nom, depute.prenom
            FROM mandat
            INNER JOIN depute ON mandat.deputeUID = depute.uid
            WHERE legislature = {legislature}
            AND typeOrgane = 'ASSEMBLEE'
            AND dateFin = (
                SELECT MAX(dateFin)
                FROM mandat
                WHERE legislature = {legislature}
                AND typeOrgane = 'ASSEMBLEE'
            )
            ORDER BY depute.nom
        """

    # Exécution
    df_deputes = pd.read_sql(query_deputes, conn)

    # Création du sélecteur de député
    df_deputes["nom_complet"] = df_deputes["civilite"] + " " + df_deputes["prenom"] + " " + df_deputes["nom"]

    depute_selectionne = st.selectbox(
    "Sélectionnez un député :",
    df_deputes["nom_complet"].tolist(),
    index=None,
    placeholder="Choisissez un député"
    )

    if depute_selectionne:
        depute_uid = df_deputes.loc[df_deputes["nom_complet"] == depute_selectionne, "uid"].iloc[0]
        st.write(f"Député sélectionné : {depute_selectionne}")
