import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ===================================================================
# 💡 ÉTAPE 1 : Configuration
# ===================================================================

# 1. Nom exact du fichier CSV
NOM_FICHIER_CSV = 'movies_data_PROGRESSIVE.csv' 

# 2. Nom EXACT de la colonne contenant l'année de sortie
NOM_COLONNE_ANNEE = 'release_year'  # Exemple. Si c'est 'Annee_Sortie', mettez 'Annee_Sortie'

# 3. Nom EXACT de la colonne contenant la note du film
NOM_COLONNE_NOTE = 'avg_rating'  # Exemple. Si c'est 'Note_Globale', mettez 'Note_Globale'

# ===================================================================

# Chargement du fichier
try:
    df = pd.read_csv(NOM_FICHIER_CSV)
    print(f"✅ Fichier CSV '{NOM_FICHIER_CSV}' chargé avec succès !")
    
    # Vérification des colonnes
    if NOM_COLONNE_ANNEE not in df.columns or NOM_COLONNE_NOTE not in df.columns:
        print("❌ ERREUR : Les noms de colonnes (Année ou Note) sont incorrects.")
        print("Vérifiez la casse et l'orthographe dans les variables ci-dessus.")
        print(f"Colonnes disponibles dans le CSV: {list(df.columns)}")
        exit()

except FileNotFoundError:
    print(f"❌ ERREUR : Le fichier n'a pas été trouvé : {NOM_FICHIER_CSV}")
    print("Assurez-vous que ce script et le CSV sont dans le même dossier 'letterboxd_v2'.")
    exit()


# ===================================================================
# 💡 ÉTAPE 2 : Préparation des Données (Création de la Décennie)
# ===================================================================

# Calcule la décennie (ex: 1997 devient '1990s')
# La double barre // est l'opérateur de division entière
df['decade'] = (df[NOM_COLONNE_ANNEE] // 10) * 10
df['decade'] = df['decade'].astype(str) + 's' 

# Trie par décennie pour un affichage propre sur le Box Plot
df = df.sort_values(by='decade')

print("\nPréparation des données terminée. Colonne 'decade' créée.")


# ===================================================================
# 💡 ÉTAPE 3 : Création et Sauvegarde du Box Plot
# ===================================================================

plt.figure(figsize=(14, 7))

# Box Plot (Boîte à moustaches) avec Seaborn
# x=Décennie, y=Note. showmeans=True pour la moyenne
sns.boxplot(x='decade', y=NOM_COLONNE_NOTE, data=df,
            showmeans=True,  
            meanprops={"marker":"D", "markerfacecolor": "red", "markeredgecolor":"black", "markersize": "8"}, 
            medianprops={"color":"blue", "linewidth": 2} 
           ) 

plt.title('Distribution des Notes de Films par Décennie', fontsize=18)
plt.xlabel('Décennie de Sortie', fontsize=14)
plt.ylabel(f'Note du Film ({NOM_COLONNE_NOTE})', fontsize=14)
plt.xticks(rotation=45) 
plt.grid(axis='y', linestyle='--')

# Sauvegarde de l'image
plt.tight_layout() 
plt.savefig('box_plot_notes_par_decennie.png') 
print("\n✅ Graphique Box Plot créé et sauvegardé sous 'box_plot_notes_par_decennie.png'.")


# ===================================================================
# 💡 ÉTAPE 4 : Réponse Finale Numérique
# ===================================================================

# Calcule la note moyenne par décennie et trie du meilleur au moins bon
moyennes_decennie = df.groupby('decade')[NOM_COLONNE_NOTE].mean().sort_values(ascending=False)

print("\n============================================================")
print("Classement des Décennies par Note Moyenne :")
# to_string() permet d'afficher le tableau des moyennes de manière claire
print(moyennes_decennie.to_string())

# Affiche la décennie gagnante
meilleure_decennie = moyennes_decennie.index[0]
meilleure_note = moyennes_decennie.iloc[0]

print(f"\n🏆 **RÉPONSE FINALE :** La décennie qui a produit les films les mieux notés (selon la moyenne) est la **{meilleure_decennie}** avec une note moyenne de **{meilleure_note:.2f}**.")
print("============================================================")
