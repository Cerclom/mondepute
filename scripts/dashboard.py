import streamlit as st
import sqlite3
import pandas as pd

# Connexion à la base SQLite
conn = sqlite3.connect("sql/mondepute.sqlite")

st.title("MonDepute - Tableau de bord")

# Liste des tables disponibles
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
st.sidebar.write("Tables disponibles :", tables)

# Choix de la table à afficher
table_name = st.sidebar.selectbox("Choisir une table :", tables['name'])

# Affichage de la table
if table_name:
    df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 1000", conn)  # limitation pour ne pas tout charger
    st.write(df)
