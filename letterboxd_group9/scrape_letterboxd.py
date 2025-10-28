# ---------------------------------------------------
# Étape 1 : imports
# ---------------------------------------------------

import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup


# ---------------------------------------------------
# Étape 2 : fonction pour récupérer le HTML rendu
# ---------------------------------------------------

def crawl_get(url: str):
    async def _run():
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return result
    return asyncio.run(_run())


# ---------------------------------------------------
# # Étape 3 : Scraper les 150 premières pages
# ---------------------------------------------------

# TOTAL_PAGES = 150
# FILMS_PER_PAGE = 72  # nombre attendu de films par page
# all_links = []
# page_counts = {}

# for page in range(1, TOTAL_PAGES + 1):
#     print(f"--- Page {page} ---")
    
#     # Récupère le HTML
#     response = crawl_get(f"https://letterboxd.com/films/popular/page/{page}/")
#     soup = BeautifulSoup(response.html, "html.parser")
    
#     # Trouve les films
#     films = soup.find_all("li", class_="posteritem")
#     page_counts[page] = len(films)
#     print(f"Page {page}: {len(films)} films trouvés")
    
#     # Récupère les liens
#     for film in films:
#         a_tag = film.find("a", class_="frame")
#         if a_tag and a_tag.get("href"):
#             link = a_tag["href"]
#         else:
#             div_tag = film.find("div", class_="react-component")
#             if div_tag and div_tag.get("data-target-link"):
#                 link = div_tag["data-target-link"]
#             else:
#                 continue
#         all_links.append("https://letterboxd.com" + link)


# ---------------------------------------------------
# # Étape 4 : Sauvegarde tous les liens dans un fichier
# ---------------------------------------------------

# with open("all_letterboxd_links.txt", "w", encoding="utf-8") as f:
#     for link in all_links:
#         f.write(link + "\n")


# ---------------------------------------------------
# ÉTAPE 5 : Vérification et ajout des liens manquants
# ---------------------------------------------------

# Lire les liens déjà existants
with open("all_letterboxd_links.txt", "r", encoding="utf-8") as f:
    all_links = set(f.read().splitlines())

TOTAL_PAGES = 150
added_total = 0  # Compteur global

# Parcours des pages pour vérifier les manquants
for page in range(1, TOTAL_PAGES + 1):
    print(f"--- Vérification page {page} ---")
    response = crawl_get(f"https://letterboxd.com/films/popular/page/{page}/")
    soup = BeautifulSoup(response.html, "html.parser")
    films = soup.find_all("li", class_="posteritem")

    missing_links = []
    for film in films:
        a_tag = film.find("a", class_="frame")
        if a_tag and a_tag.get("href"):
            link = a_tag["href"]
        else:
            div_tag = film.find("div", class_="react-component")
            if div_tag and div_tag.get("data-target-link"):
                link = div_tag["data-target-link"]
            else:
                continue
        full_link = "https://letterboxd.com" + link
        if full_link not in all_links:
            all_links.add(full_link)
            missing_links.append(full_link)

    added_total += len(missing_links)
    print(f"Page {page}: {len(missing_links)} nouveaux films ajoutés")

    # Ajout immédiat des nouveaux liens (sécurisé)
    if missing_links:
        with open("all_letterboxd_links.txt", "a", encoding="utf-8") as f:
            for link in missing_links:
                f.write(link + "\n")

print(f"\n✅ Mise à jour terminée.")
print(f"➕ {added_total} nouveaux liens ajoutés")
print(f"📦 Total unique final : {len(all_links)} liens")
