import asyncio
import csv
import json
import random
import re
from typing import Any, Dict, List, Tuple

from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

# --- ⚙️ Configuration Anti-Détection & Performance ⚙️ ---
# Temps de pause aléatoire entre les requêtes pour limiter le débit.
SAFE_PAUSE_MIN = 10.0
SAFE_PAUSE_MAX = 15.0
# Timeout pour la navigation (90 secondes).
NAVIGATION_TIMEOUT_MS = 90000
# Nombre de requêtes concurrentes.
CONCURRENT_REQUESTS = 3

# --- 📁 Fichiers 📁 ---
LINKS_FILE_PATH = "all_letterboxd_links_clean.txt"
JSON_FILE_PATH = "movies_data_PROGRESSIVE.json"
CSV_FILE_PATH = "movies_data_PROGRESSIVE.csv"
# Limite de lecture des liens (très élevée par défaut).
SCRAPING_LIMIT = 999999

# --- 📊 Variables Globales pour le Suivi (Reprise & Progression) 📊 ---
completed_tasks_counter = 0
# Verrou pour la modification des variables globales et de la liste.
progress_lock = asyncio.Lock()


# ====================================================================
#                               FONCTIONS UTILITAIRES
# ====================================================================

def read_all_links(filepath: str, limit: int) -> List[str]:
    """Lit les N premiers liens d'un fichier texte."""
    links = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                link = line.strip()
                if link:
                    links.append(link)
                if len(links) >= limit:
                    break
    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier '{filepath}' est introuvable.")
        return []
    return links


def safe_extract(func, default: Any = None) -> Any:
    """Tente d'exécuter une fonction d'extraction et retourne une valeur par défaut."""
    try:
        return func()
    except (AttributeError, IndexError, ValueError, TypeError, 
            re.error, KeyError, StopIteration):
        return default


def parse_count(text: str) -> int:
    """Convertit une chaîne (ex: '521,151' ou '5.2K') en un entier."""
    if not text:
        return 0
    text = text.replace(",", "").strip().upper()
    match = re.search(r"(\d*\.?\d+)\s*(K|M)?", text)
    if not match:
        return 0
    value_str = match.group(1)
    suffix = match.group(2)
    try:
        value = float(value_str)
    except ValueError:
        return 0
    multiplier = 1
    if suffix == "K": 
        multiplier = 1_000
    elif suffix == "M": 
        multiplier = 1_000_000
    return int(value * multiplier)


def get_default_movie_keys() -> List[str]:
    """Retourne la liste ordonnée des clés de données de film pour le CSV/JSON."""
    default_data = extract_movie_data("", "default_url")
    return list(default_data.keys())


def write_progressive_exports(data_list: List[Dict], keys: List[str]):
    """Écrit le JSON et le CSV pour sauvegarder l'état actuel de la liste."""
    if not data_list:
        return
    # 1. Écriture du JSON
    try:
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"\n❌ ERREUR SAUVEGARDE JSON: Impossible d'écrire "
              f"{JSON_FILE_PATH}. {e}")

    # 2. Écriture du CSV
    try:
        with open(CSV_FILE_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
    except Exception as e:
        print(f"\n❌ ERREUR SAUVEGARDE CSV: Impossible d'écrire "
              f"{CSV_FILE_PATH}. {e}")


# ====================================================================
#                           FONCTIONS D'EXTRACTION
# ====================================================================

async def fetch_html(crawler: AsyncWebCrawler, url: str) -> str:
    """Récupère le HTML d'une URL avec le timeout configuré."""
    result = await crawler.arun(
        url=url,
        wait_until='load',
        timeout_ms=NAVIGATION_TIMEOUT_MS,
    )
    # Validation minimale du contenu HTML
    if not result.html or len(result.html) < 1000:
        raise ValueError("Contenu HTML vide ou trop court. Erreur de page "
                         "ou blocage probable.")
    return result.html


def extract_movie_data(html: str, url: str) -> Dict[str, Any]:
    """Analyse le HTML et extrait toutes les métadonnées du film."""
    soup = BeautifulSoup(html, "html.parser")
    # ⚠️ Initialisation avec **TOUTES** les clés nécessaires
    data: Dict[str, Any] = {
        "film_url": url, "film_name": "", "release_year": None, 
        "duration_min": None, "main_language": "", "spoken_languages": "", 
        "genres": "", "first_genre": "", "themes": "", "synopsis": "", 
        "directors": "", "cast": "", "first_actor": "", "studios": "", 
        "origin_countries": "", "release_type": "", "premiere_festival": "", 
        "where_to_watch": "", "avg_rating": 0.0, "ratings_count": 0, 
        "views_count": 0, "lists_count": 0, "likes_count": 0, 
        "fans_count": 0, "is_top_250_ranked": False
    }

    # --- Extraction de Base (Vérification de Succès) ---
    data["film_name"] = safe_extract(
        lambda: soup.select_one("h1.headline-1 span.name").text.strip(), 
        default=""
    )
    if not data["film_name"]: 
        return data

    # --- Métadonnées Simples ---
    data["release_year"] = safe_extract(
        lambda: int(soup.find("a",
                              href=lambda h: h and "/films/year/" in h).text.strip()), 
        default=None
    )
    data["duration_min"] = safe_extract(
        lambda: int(re.search(r"(\d+)\s*mins", 
                              soup.select_one("p.text-link.text-footer").get_text()).group(1)), 
        default=None
    )
    data["synopsis"] = safe_extract(
        lambda: soup.select_one("div.truncate p").text.strip(), default=""
    )

    # --- Extraction par fonction spécialisée ---
    def extract_languages() -> Tuple[str, str]:
        """Extrait la langue principale et les langues parlées."""
        main_lang, spoken_list = "", ""
        primary_lang_tag = soup.find("span",
                                     string=lambda s: s and "Primary Language" in s)
        spoken_lang_tag = soup.find("span",
                                    string=lambda s: s and "Spoken Languages" in s)

        if primary_lang_tag and spoken_lang_tag:
            main_lang_div = primary_lang_tag.find_parent("h3").find_next_sibling("div")
            spoken_lang_div = spoken_lang_tag.find_parent("h3").find_next_sibling("div")
            main_lang = main_lang_div.get_text(strip=True) if main_lang_div else ""
            spoken_langs = [a.text.strip() for a in spoken_lang_div.find_all("a")] 
            spoken_list = " | ".join(spoken_langs)
        else:
            lang_tag = soup.find("span", 
                                 string=lambda s: s and "Language" in s)
            if lang_tag:
                lang_div = lang_tag.find_parent("h3").find_next_sibling("div")
                main_lang = lang_div.get_text(strip=True) if lang_div else ""
                spoken_list = main_lang  # Fallback
                
        return main_lang, spoken_list

    data["main_language"], data["spoken_languages"] = safe_extract(
        extract_languages, default=("", "")
    )

    def extract_genres() -> Tuple[str, str]:
        """Extrait la liste des genres et le premier genre."""
        genre_div = next(
            (h3.find_next_sibling("div") for h3 in soup.find_all("h3")
             if h3.find("span") and "Genre" in h3.find("span").text), None
        )
        genres = [a.text.strip() for a in genre_div.find_all("a")] if genre_div else []
        return " | ".join(genres), genres[0] if genres else ""

    data["genres"], data["first_genre"] = safe_extract(
        extract_genres, default=("", "")
    )

    def extract_themes() -> str:
        """Extrait les thèmes et mini-thèmes."""
        theme_tags = soup.select("a.text-slug")
        themes = {
            t.get_text(strip=True) for t in theme_tags
            if ('/theme/' in t.get("href", "") or '/mini-theme/' in t.get("href", ""))
            and not t.get_text(strip=True).startswith('Show All') 
            and t.get_text(strip=True)
        }
        return " | ".join(sorted(list(themes)))

    data["themes"] = safe_extract(extract_themes, default="")

    def extract_cast_and_directors() -> Tuple[str, str, str]:
        """Extrait les réalisateurs, la liste des acteurs et le premier acteur."""
        directors = " | ".join(
            [a.text.strip() for a in soup.select("a.contributor span.prettify")]
        )
        cast = [a.text.strip() for a in soup.select("div.cast-list p a")]
        full_cast = " | ".join(cast)
        first_actor = cast[0] if cast else ""
        return directors, full_cast, first_actor

    data["directors"], data["cast"], data["first_actor"] = safe_extract(
        extract_cast_and_directors, default=("", "", "")
    )

    data["studios"] = safe_extract(
        lambda: " | ".join([a.text.strip() for a in soup.find_all("a", href=True) 
                            if "/studio/" in a["href"]]), default=""
    )

    def extract_countries() -> str:
        """Extrait le(s) pays d'origine."""
        country_tag = soup.find("span",
                                string=lambda s: s and ("Country" in s or "Countries" in s))
        if country_tag:
            country_div = country_tag.find_parent("h3").find_next_sibling("div")
            countries = [a.text.strip() for a in country_div.select("a.text-slug")]
            return " | ".join(countries)
        return ""
    data["origin_countries"] = safe_extract(extract_countries, default="")

    data["release_type"] = safe_extract(
        lambda: " | ".join([h3.text.strip() for h3 in soup.find_all("h3", 
                                                                    class_="release-table-title")]), 
        default=""
    )

    def extract_premiere() -> str:
        """Extrait le nom du festival de première."""
        premiere_section = soup.find("h3", string=lambda s: s and "Premiere" in s)
        premiere_festival_list = []
        if premiere_section:
            premiere_block = premiere_section.find_next_sibling("div",
                                                                class_="release-table -bydate")
            if premiere_block:
                for li in premiere_block.select("li.listitem"):
                    fest_tag = li.select_one("span.release-note")
                    if fest_tag and 'festival' in fest_tag.text.lower():
                        premiere_festival_list.append(fest_tag.text.strip())
        return " | ".join(premiere_festival_list)
        
    data["premiere_festival"] = safe_extract(extract_premiere, default="")

    def extract_watch_platforms() -> str:
        """Extrait où regarder le film (plateformes et options)."""
        available_section = soup.find("section", class_="services")
        platforms = []
        if available_section:
            for service in available_section.find_all("p", class_="service"):
                name_tag = service.find("span", class_="name")
                if not name_tag or not name_tag.text.strip(): continue
                locale_tag = service.find("span", class_="locale")
                options = [opt.text.strip() for opt in 
                           service.select(".options a span.extended")]
                platform_name = (f"{name_tag.text.strip()} ({locale_tag.text.strip()})" 
                                 if locale_tag else name_tag.text.strip())
                if options:
                    platforms.append(f"{platform_name}: {', '.join(options)}")
                return " | ".join(platforms)
    
    data["where_to_watch"] = safe_extract(extract_watch_platforms, default="")

    # --- Bloc d'extraction des Statistiques ---
    data["avg_rating"] = safe_extract(
        lambda: float(soup.select_one("span.average-rating a").text.strip()), 
        default=0.0
    )

    def extract_ratings_count() -> int:
        """Extrait le nombre total de notes."""
        rating_link = soup.select_one("span.average-rating a")
        if rating_link and rating_link.get("data-original-title"):
            title_text = rating_link["data-original-title"]
            match = re.search(r"based on ([\d,]+)\s*ratings", title_text)
            if match:
                return parse_count(match.group(1))
        return 0

    data["ratings_count"] = safe_extract(extract_ratings_count, default=0)
    
    def extract_statistic_from_aria(class_suffix: str) -> int:
        """Extrait les statistiques (vues, listes) à partir de l'attribut aria-label."""
        stat_div = soup.find("div", class_=f"production-statistic -{class_suffix}")
        if stat_div and stat_div.get("aria-label"):
            aria_label = stat_div["aria-label"]
            match = re.search(r"(\d{1,3}(?:,\d{3})*)", aria_label)
            if match:
                return parse_count(match.group(1))
        return 0

    data["views_count"] = safe_extract(
        lambda: extract_statistic_from_aria("watches"), default=0
    )
    data["lists_count"] = safe_extract(
        lambda: extract_statistic_from_aria("lists"), default=0
    )
    data["likes_count"] = safe_extract(
        lambda: extract_statistic_from_aria("likes"), default=0
    )
    data["fans_count"] = safe_extract(
        lambda: parse_count(soup.select_one('a[href*="/fans/"]').text.strip()), 
        default=0
    )

    top_250_link = soup.select_one(
        'a[href*="official-top-250-narrative-feature-films"]'
    )
    data["is_top_250_ranked"] = bool(top_250_link)

    return data


# ====================================================================
#                               FONCTION PRINCIPALE
# ====================================================================

async def scrape_movie(crawler: AsyncWebCrawler, link: str, all_data: List[Dict], 
                       total_links: int, keys: List[str]):
    """
    Tâche asynchrone pour scraper un seul film, mettre à jour la liste de données 
    et gérer la progression ainsi que les erreurs.
    """
    global completed_tasks_counter
    # Données d'erreur par défaut
    error_data = {"film_url": link, "film_name": "ERROR_NETWORK/PAGE", 
                  "ratings_count": 0, "fans_count": 0}

    try:
        html = await fetch_html(crawler, link)
        movie_data = extract_movie_data(html, link)

        # Logique de sauvegarde et de progression (protégée par un verrou)
        async with progress_lock:
            completed_tasks_counter += 1
            current_progress = completed_tasks_counter
    
            if movie_data.get("film_name") and movie_data.get("film_name") != "":
                all_data.append(movie_data)
                
                # Sauvegarde immédiate après le succès
                write_progressive_exports(all_data, keys) 
                
                status = "✅ Succès"
                if movie_data["avg_rating"] == 0.0 or movie_data["ratings_count"] == 0:
                    status = "⚠️ Succès (Stats Manquantes)"
                    
                print(f"{status} [{current_progress}/{total_links}]: "
                      f"{movie_data['film_name']} -> SAUVEGARDÉ!")

            else:
                all_data.append(error_data) # Ajout de la ligne d'erreur/404
                write_progressive_exports(all_data, keys)
                print(f"⚠️ Ignoré [{current_progress}/{total_links}]: Titre manquant "
                      f"(probablement 404) pour {link}. -> SAUVEGARDÉ!")

    except Exception as e:
        # Erreur critique (Timeout, réseau, etc.)
        async with progress_lock:
            completed_tasks_counter += 1
            current_progress = completed_tasks_counter
            all_data.append(error_data) # Ajout de la ligne d'erreur
            write_progressive_exports(all_data, keys)
        
        print(f"❌ ERREUR CRITIQUE [{current_progress}/{total_links}] sur {link}: "
              f"{e.__class__.__name__}. Ajout de la ligne d'erreur. -> SAUVEGARDÉ!")
    
    # Pause cruciale pour limiter le débit
    pause_time = random.uniform(SAFE_PAUSE_MIN, SAFE_PAUSE_MAX) 
    await asyncio.sleep(pause_time)


async def main():
    """Fonction principale pour lire les liens, gérer la reprise et lancer le scraping."""
    links = read_all_links(LINKS_FILE_PATH, SCRAPING_LIMIT)
    total_links = len(links)
    keys = get_default_movie_keys()  # Obtenir les clés pour le CSV

    if total_links == 0:
        print("Aucun lien trouvé. Arrêt.")
        return

    print(f"{total_links} liens trouvés. Démarrage du scraping parallèle "
          f"(max {CONCURRENT_REQUESTS} requêtes concurrentes)...")

    # --- Reprise (Tentative de chargement des données existantes) ---
    all_data: List[Dict] = []
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            all_data = json.load(f)
            global completed_tasks_counter
            completed_tasks_counter = len(all_data)
            print(f"✅ Reprise : {len(all_data)} résultats chargés depuis "
                  f"{JSON_FILE_PATH}.")

    except FileNotFoundError:
        print(f"Démarrage à zéro: Le fichier {JSON_FILE_PATH} n'existe pas encore.")
    except json.JSONDecodeError:
        print("⚠️ ERREUR : Le fichier JSON est corrompu. Démarrage à zéro.")
   
    
    #  Filtrer la liste pour reprendre après le dernier lien traité
    links_to_scrape = links[len(all_data):]
    if not links_to_scrape:
        print("Toutes les URLs ont déjà été traitées. Le scraping est terminé.")
        return
    
    print(f"Reprise du scraping au lien n°{len(all_data) + 1}. "
          f"{len(links_to_scrape)} liens restants à traiter.")
    
    # --- Démarrage du Crawler ---
    async with AsyncWebCrawler(
        browser='firefox',
        max_concurrent_requests=CONCURRENT_REQUESTS
    ) as crawler:
        tasks = [
            scrape_movie(crawler, link, all_data, total_links, keys) 
            for link in links_to_scrape
        ]
        
        await asyncio.gather(*tasks)

    print(f"\n✨ Scraping Terminé. {len(all_data)} lignes traitées sur "
          f"{total_links} liens totaux.")
    print(f"Fichiers de sortie : **{JSON_FILE_PATH}** et **{CSV_FILE_PATH}** "
          f"(progressivement mis à jour).")


# ====================================================================
#                                  RUN
# ====================================================================

if __name__ == "__main__":
    try:
        # debug=False par défaut, c'est mieux pour la performance
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Scraping interrompu manuellement. Les données sont sauvegardées.")
    except Exception as e:
        print(f"\n\n🛑 Une erreur inattendue s'est produite lors de "
              f"l'exécution principale : {e}")
              