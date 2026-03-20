from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import os

app = Flask(__name__)

AUTH_KEY = os.environ.get("AUTH_KEY", "Basic YourSecretKeyHere")


def get_first_movie_href(search_query):
    encoded_query = urllib.parse.quote_plus(search_query)
    url = f"https://www.themoviedb.org/search?query={encoded_query}"

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results_div = soup.find("div", class_=["search_results", "movie"])
    if not results_div:
        return None

    first_card = results_div.find("div", class_="card v4 tight")
    if not first_card:
        return None

    link_tag = first_card.find("a", class_="result")
    if link_tag and link_tag.get("href"):
        href = link_tag["href"]
        full_url = urllib.parse.urljoin("https://www.themoviedb.org", href)
        return full_url

    return None


def scrape_movie_details(movie_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(movie_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Movie name
    title_tag = soup.select_one("div.title h2 a")
    movie_name = title_tag.get_text(strip=True) if title_tag else None

    # Image URL
    img_tag = soup.select_one("img.poster.w-full")
    image_url = img_tag["src"] if img_tag and img_tag.get("src") else None

    # Movie year
    movie_tag = soup.select_one("div.title h2 span")
    movie_year = movie_tag.get_text(strip=True).replace("(", "").replace(")", "") if movie_tag else None

    # Description
    overview_tag = soup.select_one("div.overview p")
    overview = overview_tag.get_text(strip=True) if overview_tag else None

    # Streaming availability
    available_platform = None
    available_type = None
    provider_img = soup.select_one("div.button div.provider img")
    if provider_img and provider_img.get("alt"):
        alt_text = provider_img["alt"]

        for platform in ["Amazon", "Netflix", "Sky", "Disney"]:
            if platform.lower() in alt_text.lower():
                available_platform = platform
                break

        if "stream" in alt_text.lower():
            available_type = "Stream"
        elif "kauf" in alt_text.lower():
            available_type = "Kauf"
            available_platform = "Amazon"

    # Determine type (Film or Serie) and count seasons if applicable
    season_section = soup.select_one("section.panel.season")
    if season_section:
        movie_type = "Serie"

        last_season_tag = season_section.select_one("div.season.card h2 a")
        if last_season_tag:
            match = re.search(r"(\d+)", last_season_tag.get_text(strip=True))
            season_count = int(match.group(1)) if match else None
        else:
            season_count = None
    else:
        season_count = None
        movie_type = "Film"

    # Genres
    genres = [a.get_text(strip=True) for a in soup.select("div.facts span.genres a")]

    return {
        "movie_name": movie_name,
        "image_url": image_url,
        "movie_year": movie_year,
        "description": overview,
        "genres": genres,
        "available_platform": available_platform,
        "available_type": available_type,
        "season_count": season_count,
        "movie_type": movie_type,
    }


@app.route("/movie", methods=["GET"])
def movie():
    auth_header = request.headers.get("Authorization")
    if auth_header != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter ?q="}), 400

    movie_url = get_first_movie_href(query)
    if not movie_url:
        return jsonify({"error": "Movie not found"}), 404

    details = scrape_movie_details(movie_url)
    return jsonify(details)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
