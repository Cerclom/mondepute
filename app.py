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

with tab2:
    st.subheader("Analyse des scrutins")
    query_type_vote_nb_taux = """
        SELECT 
            libelleTypeVote,
            COUNT(*) AS NB_total,
            SUM(CASE WHEN codesort = 'adopté' THEN 1 ELSE 0 END) AS NB_adopte,
            ROUND(
                100 * SUM(CASE WHEN codesort = 'adopté' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS TA
        FROM vote
        GROUP BY libelleTypeVote
        ORDER BY NB_total DESC;
    """
    type_vote_nb_taux = pd.read_sql(query_type_vote_nb_taux, conn)
    # --- S'assurer que TA est bien numérique ---
    type_vote_nb_taux["TA"] = pd.to_numeric(type_vote_nb_taux["TA"], errors="coerce")
    # --- Graphique Plotly ---
    fig = px.bar(
        type_vote_nb_taux,
        x="libelleTypeVote",
        y="TA",
        text="TA",
        color="TA",
        color_continuous_scale="Viridis",
        title="Taux d’adoption par type de vote (%)"
    )

    # --- Mise en forme ---
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(
        xaxis_title="Type de vote",
        yaxis_title="Taux d’adoption (%)",
        coloraxis_showscale=False,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
    )
    fig.update_yaxes(range=[0, 100])

    # --- Affichage Streamlit ---
    st.plotly_chart(fig, use_container_width=True)

    #Affichage en tableau
    col3, col4 = st.columns(2)
    col3.metric("Nombre de députés", nb_deputes)
    col4.metric("Nombre de scrutins", nb_scrutins)


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



        # --- Récupération des informations générales ---
        query_infos = f"""
            SELECT civilite, prenom, nom, dateNaissance, villeNaissance, dateDeces
            FROM depute
            WHERE uid = '{depute_uid}'
        """
        df_infos = pd.read_sql(query_infos, conn)

        # --- Présentation ---
        if not df_infos.empty:
            infos = df_infos.iloc[0]

            st.subheader("Informations générales")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Nom :** {infos['civilite']} {infos['prenom']} {infos['nom']}")
                st.markdown(f"**Date de naissance :** {infos['dateNaissance']}")
                st.markdown(f"**Ville de naissance :** {infos['villeNaissance']}")

            with col2:
                if pd.notna(infos["dateDeces"]):
                    st.markdown(f"**Décédé le :** {infos['dateDeces']}")
                else:
                    st.markdown("**Statut :** Vivant")

    # Récupération des votes pour le député
    query_votes = f"""
        SELECT votedepute.decision AS decision_depute, vote.codesort AS decision_assemblee
        FROM votedepute
        INNER JOIN vote ON votedepute.vote = vote.uid
        WHERE votedepute.depute = '{depute_uid}'
        AND vote.legislature = {legislature}
    """
    df_votes = pd.read_sql(query_votes, conn)

    # Nombre total de scrutins pour la législature
    query_total_scrutins = f"""
        SELECT COUNT(*) AS total_scrutins
        FROM vote
        WHERE legislature = {legislature}
    """
    total_scrutins = pd.read_sql(query_total_scrutins, conn)["total_scrutins"].iloc[0]

    # KPI 1 : Nombre de votes exprimés
    nb_votes = df_votes.shape[0]

    # KPI 2 : Taux de participation (en %)
    # Ici on considère qu'un vote est "exprimé" si la colonne decision_depute n'est pas NaN
    votes_exprimes = df_votes["decision_depute"].notna().sum()
    taux_participation = (nb_votes / total_scrutins * 100) if total_scrutins > 0 else 0

    # KPI 3 : Taux d'accord avec l'Assemblée
    accord = df_votes[
        ((df_votes["decision_depute"] == "pour") & (df_votes["decision_assemblee"] == "adopté")) |
        ((df_votes["decision_depute"] == "contre") & (df_votes["decision_assemblee"] == "rejeté"))
    ]
    taux_accord = (len(accord) / nb_votes * 100) if nb_votes > 0 else 0

    # Affichage dans Streamlit
    st.subheader("📊 KPI du député")
    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre de votes exprimés", nb_votes)
    col2.metric("Taux de participation", f"{taux_participation:.1f}%")
    col3.metric("Taux d'accord avec l'Assemblée", f"{taux_accord:.1f}%")

    # Requête des votes du député sélectionné
    query_votes = f"""
        SELECT decision
        FROM votedepute
        INNER JOIN vote ON votedepute.vote = vote.uid
        WHERE votedepute.depute = '{depute_uid}'
        AND vote.legislature = {legislature}
    """
    df_votes = pd.read_sql(query_votes, conn)

    # Nettoyage et regroupement
    df_votes = df_votes.dropna(subset=["decision"])
    df_decision = df_votes["decision"].value_counts().reset_index()
    df_decision.columns = ["Décision", "Nombre"]

    # Création du camembert
    fig = px.pie(
        df_decision,
        values="Nombre",
        names="Décision",
        title="Répartition des votes du député",
        hole=0.3,  # pour un effet donut
        color="Décision",
            color_discrete_map={
        "pour": "#2ECC71",        # vert
        "contre": "#E74C3C",      # rouge
        "abstention": "#F1C40F",  # jaune
        "nonVotant": "#95A5A6",   # gris
        "nonVoté": "#BDC3C7",     # gris clair (si tu as cette catégorie)
        "absent": "#7F8C8D"       # optionnel
    }
    )

    fig.update_traces(textinfo="percent+label")

    # Affichage Streamlit
    st.plotly_chart(fig, use_container_width=True)
