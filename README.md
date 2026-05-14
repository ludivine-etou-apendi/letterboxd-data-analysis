# Letterboxd — web scraping et analyse de données cinéma

Projet **académique** (travail de groupe, groupe 9) : collecte d’URLs sur Letterboxd, nettoyage des doublons, scraping des fiches films (notes, genres, réalisateurs, etc.) sur **10 795** titres, puis analyse statistique et visualisations.

Les données présentes dans ce dépôt servent de **jeu complet** pour rejouer les analyses ou explorer le dataset sans relancer tout le scraping.

## Contexte

Ce dépôt documente un projet réalisé dans un cadre **pédagogique**. Les données issues de pages **publiques** Letterboxd sont utilisées à des fins **non commerciales** et d’apprentissage.

## Dépendances

Installer les bibliothèques Python nécessaires (Python 3.10+ recommandé) :

```bash
pip install crawl4ai beautifulsoup4 pandas matplotlib seaborn
```

## Structure du dépôt

Tout le code et les fichiers de données sont dans le dossier `letterboxd_group9/`.

| Fichier | Rôle |
| :--- | :--- |
| `letterboxd_group9/scrape_letterboxd.py` | Collecte des URLs depuis les pages populaires Letterboxd. |
| `letterboxd_group9/clean_links.py` | Lecture de `all_letterboxd_links.txt`, suppression des doublons → écriture de `all_letterboxd_links_clean.txt`. |
| `letterboxd_group9/scraperletterboxd.py` | Scraping des fiches à partir de la liste nettoyée ; export progressif en JSON et CSV. |
| `letterboxd_group9/notes_par_decennies.py` | Analyse statistique sur le CSV, moyennes par décennie, génération du box plot. |
| `letterboxd_group9/all_letterboxd_links.txt` | Liste brute des URLs collectées avant dédoublonnage. |
| `letterboxd_group9/all_letterboxd_links_clean.txt` | Liste des URLs utilisées pour le scraping détaillé (sans doublons). |
| `letterboxd_group9/movies_data_PROGRESSIVE.json` | Données agrégées au format JSON. |
| `letterboxd_group9/movies_data_PROGRESSIVE.csv` | Même jeu de données au format CSV (analyse, tableurs). |
| `letterboxd_group9/box_plot_notes_par_decennie.png` | Visualisation des notes par décennie. |

## Exécution

1. Ouvrir un terminal et se placer dans le dossier `letterboxd_group9` (chemins relatifs utilisés par les scripts).
2. **Scraping complet** des fiches (très long : plusieurs heures selon la machine et le réseau) :

```bash
python3 scraperletterboxd.py
```

3. Pour **tester** sur un nombre limité d’URLs, modifier la variable `SCRAPING_LIMIT` dans la section configuration de `scraperletterboxd.py`.
4. **Analyse** (à partir du CSV déjà présent) :

```bash
python3 notes_par_decennies.py
```

## Avertissement

Le site Letterboxd et les bibliothèques tierces peuvent évoluer : un script qui fonctionnait à une date donnée peut nécessiter des ajustements plus tard. Respecter les conditions d’utilisation de Letterboxd pour tout usage au-delà de ce cadre académique.

