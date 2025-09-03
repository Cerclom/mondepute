import pymysql
import sqlite3
import pandas as pd

# -----------------------------
# Connexion MySQL
# -----------------------------
mysql_conn = pymysql.connect(
    host='localhost',
    user='root',       # remplace par ton user MySQL
    password='9903',    # remplace par ton mot de passe
    database='mondepute'
)

# Connexion SQLite
sqlite_conn = sqlite3.connect('mondepute.sqlite')

# Liste des tables à migrer
tables = ['circonscription', 'depute', 'mandat', 'vote', 'votedepute']

# Fonction pour migrer une table
def migrate_table(table_name, chunksize=None):
    print(f"Migration de la table {table_name}...")
    query = f"SELECT * FROM {table_name}"
    
    if chunksize:  # pour les très grosses tables
        for chunk in pd.read_sql(query, mysql_conn, chunksize=chunksize):
            chunk.to_sql(table_name, sqlite_conn, if_exists='append', index=False)
    else:
        df = pd.read_sql(query, mysql_conn)
        df.to_sql(table_name, sqlite_conn, if_exists='replace', index=False)
    print(f"Table {table_name} migrée avec succès !")

# Migration table par table
for table in tables:
    if table == 'votedepute':
        migrate_table(table, chunksize=100000)  # 100 000 lignes par batch
    else:
        migrate_table(table)

# Fermeture des connexions
mysql_conn.close()
sqlite_conn.close()
print("Toutes les tables ont été migrées avec succès dans mondepute.sqlite !")
