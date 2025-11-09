# groupe_9_github.txt
# Projet Web Scraping & Analyse de Films (Letterboxd) - Groupe 9

Ce projet Python vise à scraper des données détaillées (Note, Genre, Réalisateurs etc.) sur 10 795 films depuis la plateforme Letterboxd, puis à effectuer une analyse statistique sur les données collectées.

---

# Structure et Description des Fichiers

| Fichier | Type | Description |
| :--- | :--- | :--- |
| `scrape_letterboxd.py` | Code | Script pour la collecte initiale des URLs des films à partir des pages populaires de Letterboxd. |
| `clean_links.py` | Code | Script de nettoyage qui lit la liste brute des liens et supprime les doublons pour créer le fichier `all_letterboxd_links_clean.txt`. |
| `scraperletterboxd.py` | Code | Script principal de scraping qui utilise les liens propres (`all_letterboxd_links_clean.txt`) pour visiter chaque page de film et extraire les données détaillées (notes, genres, etc.). |
| `notespardécennies.py` | Code | Script d'analyse statistique qui lit le fichier CSV, calcule les moyennes par décennie et génère le graphique (box plot). |
| `all_letterboxd_links_clean.txt` | Données | Liste finale et propre des 10 795 URLs de films utilisées pour le scraping détaillé. |
| `movies_data_PROGRESSIVE.csv` | Données | Jeu de données complet et propre au format CSV, utilisé pour l'analyse statistique. |
| `movies_data_PROGRESSIVE.json` | Données | Ensemble des données brutes des 10 795 films collectées par le scraper, au format JSON. |
| `box_plot_notes_par_decennie.png` | Résultat | Visualisation graphique (Box Plot) des notes distribuées par décennie. |

---

# Exécution du Code (Important)

Pour executer le scraping tapez "python3 scraperletterboxd.py" ⚠️ ATTENTION : L'étape de scraping des 10 795 films individuels (scraperletterboxd.py) nous a pris plus de 16 heures.

Pour exécuter le script sur un échantillon de liens au lieu de la totalité (pour des tests), vous devez modifier la variable SCRAPING_LIMIT dans la section Configuration du code. Vous pouvez y renseigner le nombre d'URLs que vous souhaitez traiter.


