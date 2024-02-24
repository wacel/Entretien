import itertools
import sqlite3
import database
# on va ici génerer toute combinaisons possibles avec itertools
def generate_combinations():
    etapes = ['Etape_' + str(i) for i in range(1, 24)]
    return list(itertools.product([True, False], repeat=len(etapes)))

# On submit les business rules (gestion métiers) mentionnées en excel 1 par 1
def define_business_rules():
    return [
        ("En cours d'accrochage", "Initialisation du projet d'accrochage", "Si conditions pour Initialisation du projet d'accrochage"),
        ("En cours d'accrochage", "Accrochage technique", "Si conditions pour Accrochage technique"),
        ("En cours d'accrochage", "Validation de conformité", "Si conditions pour Validation de conformité"),
        ("En cours d'accrochage", "Mise en production", "Si conditions pour Mise en production"),
        ("En production", "OK", "Si conditions pour OK"),
        ("En production", "Adaptations spécifiques", "Si conditions pour Adaptations spécifiques"),
        ("En production", "Requalification CA", "Si conditions pour Requalification CA")
    ]

#vérification de correspondances en se connectant à la base et avec sqlite3 et des requetes db
def verify_correspondences():
    conn = sqlite3.connect('business_rules.db')
    cursor = conn.cursor()

    # Create correspondance_combinaison_regle table if not exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS correspondance_combinaison_regle 
                      (ID INTEGER PRIMARY KEY, CombinaisonID INTEGER, RegleID INTEGER)''')

    # Select all combinations and rules
    cursor.execute('''SELECT ID, * FROM Combinaisons''')
    combinaisons = cursor.fetchall()
    cursor.execute('''SELECT rowid, * FROM Regles''')
    regles = cursor.fetchall()

    # Verify correspondences and insert into correspondance_combinaison_regle if valid
    for combinaison in combinaisons:
        for regle in regles:
            if validate_correspondence(combinaison[1:], regle[1:]):
                cursor.execute('''INSERT INTO correspondance_combinaison_regle (CombinaisonID, RegleID) VALUES (?, ?)''', (combinaison[0], regle[0]))

    # Commit and close connection
    conn.commit()
    conn.close()

    print("Correspondences have been verified and inserted successfully.")

# Validation de correspondance avec un simple boucle et un simple if
def validate_correspondence(combinaison, regle):
    for i in range(len(combinaison)):
        if combinaison[i] != regle[i] and regle[i] != 'True':
            return False
    return True

# Identifier les combinaisons qui ne sont pas dans un statut ou sous-statut on les récupere avec select et apres on teste
def identifier_combinaisons_non_attribuees():
    conn = sqlite3.connect('business_rules.db')
    cursor = conn.cursor()

    # Sélectionner toutes les combinaisons
    cursor.execute('''SELECT ID FROM Combinaisons''')
    combinaisons = set([row[0] for row in cursor.fetchall()])

    # Sélectionner les combinaisons attribuées à un statut ou sous-statut
    cursor.execute('''SELECT DISTINCT CombinaisonID FROM correspondance_combinaison_regle''')
    combinaisons_attribuees = set([row[0] for row in cursor.fetchall()])

    # Identifier les combinaisons non attribuées
    combinaisons_non_attribuees = combinaisons - combinaisons_attribuees

    conn.close()

    return combinaisons_non_attribuees

# meme chose mais pour multiples
def identifier_combinaisons_multiples():
    conn = sqlite3.connect('business_rules.db')
    cursor = conn.cursor()

    # Sélectionner les combinaisons et le nombre de statuts/sous-statuts auxquels elles sont attribuées
    cursor.execute('''SELECT CombinaisonID, COUNT(*) FROM correspondance_combinaison_regle GROUP BY CombinaisonID''')
    combinaisons_multiples = [row[0] for row in cursor.fetchall() if row[1] > 1]

    conn.close()

    return combinaisons_multiples

# meme chose pour exxactes
def identifier_correspondance_exacte_statut_sous_statuts():
    conn = sqlite3.connect('business_rules.db')
    cursor = conn.cursor()

    # Sélectionner les identifiants de tous les statuts
    cursor.execute('''SELECT DISTINCT Statut FROM Regles WHERE Statut <> ''')
    statuts = [row[0] for row in cursor.fetchall()]

    # Vérifier la correspondance exacte pour chaque statut
    correspondance_exacte_statut_sous_statuts = []
    for statut in statuts:
        cursor.execute('''SELECT DISTINCT CombinaisonID FROM correspondance_combinaison_regle 
                          WHERE CombinaisonID IN (
                              SELECT CombinaisonID FROM correspondance_combinaison_regle 
                              WHERE RegleID IN (SELECT rowid FROM Regles WHERE Statut = ?)
                          )''', (statut,))
        combinaisons_statut = set([row[0] for row in cursor.fetchall()])

        cursor.execute('''SELECT DISTINCT CombinaisonID FROM correspondance_combinaison_regle 
                          WHERE RegleID IN (
                              SELECT rowid FROM Regles 
                              WHERE Statut = ? AND SousStatut <> ''
                          )''', (statut,))
        combinaisons_sous_statuts = set([row[0] for row in cursor.fetchall()])

        if combinaisons_statut == combinaisons_sous_statuts:
            correspondance_exacte_statut_sous_statuts.append(statut)

    conn.close()

    return correspondance_exacte_statut_sous_statuts

if __name__ == "__main__":
    etapes = ['Etape_' + str(i) for i in range(1, 24)]
    database.create_database(etapes)
    verify_correspondences()

    # 1. Identifier les combinaisons qui ne sont pas dans un statut ou sous-statut
    combinaisons_non_attribuees = identifier_combinaisons_non_attribuees()
    print("Combinaisons non attribuées à un statut ou sous-statut :", combinaisons_non_attribuees)

    # 2. Identifier les combinaisons qui sont dans plusieurs statuts ou sous-statuts
    combinaisons_multiples = identifier_combinaisons_multiples()
    print("Combinaisons attribuées à plusieurs statuts ou sous-statuts :", combinaisons_multiples)

    # 3. Identifier s'il y a une correspondance exacte entre les combinaisons d'un statut et de l'ensemble de ses sous-statuts
    correspondance_exacte_statut_sous_statuts = identifier_correspondance_exacte_statut_sous_statuts()
    print("Correspondance exacte entre les combinaisons d'un statut et de ses sous-statuts pour les statuts suivants :", correspondance_exacte_statut_sous_statuts)
