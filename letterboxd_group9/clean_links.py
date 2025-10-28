# ---------------------------------------------------
# Objectif : créer un nouveau fichier avec les liens des films sans doublons
# ---------------------------------------------------

# Étape 1 : Lecture du fichier original
with open("all_letterboxd_links.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]  # on supprime les lignes vides

# Étape 2 : Suppression des doublons
unique_links = sorted(set(lines))  # un set garde uniquement les valeurs uniques

# Étape 3 : Création d’un nouveau fichier propre
with open("all_letterboxd_links_clean.txt", "w", encoding="utf-8") as f:
    for link in unique_links:
        f.write(link + "\n")

# Étape 4 : Résumé
print("🧹 Nettoyage terminé avec succès !")
print(f"Total initial : {len(lines)} liens")
print(f"Total unique  : {len(unique_links)} liens")
print(f"Doublons supprimés : {len(lines) - len(unique_links)}")
print("📁 Nouveau fichier créé : all_letterboxd_links_clean.txt")