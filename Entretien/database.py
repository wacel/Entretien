import sqlite3
from main import generate_combinations
from main import define_business_rules

# Create SQLite database and insert data into respective tables
def create_database(etapes):
    conn = sqlite3.connect('business_rules.db')
    cursor = conn.cursor()

    # Create Combinaisons table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Combinaisons (ID INTEGER PRIMARY KEY, {})'''.format(", ".join(etapes)))

    # Insert combinations into Combinaisons table
    for i, combinaison in enumerate(generate_combinations()):
        cursor.execute('''INSERT INTO Combinaisons ({}) VALUES ({})'''.format(", ".join(etapes), ", ".join(map(str, combinaison))))

    # Create Regles table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Regles (Statut TEXT, SousStatut TEXT, Regle TEXT)''')

    # Insert business rules into Regles table
    for regle in define_business_rules():
        cursor.execute('''INSERT INTO Regles (Statut, SousStatut, Regle) VALUES (?, ?, ?)''', regle)

    # Commit and close connection
    conn.commit()
    conn.close()

    print("Data has been inserted successfully.")

# Verify correspondences between combinations and business rules