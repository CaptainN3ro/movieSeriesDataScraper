from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

AUTH_KEY = os.environ.get("AUTH_KEY", "Basic YourSecretKeyHere")
TMDB_TOKEN = os.environ.get("TMDB_TOKEN", "")

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

TMDB_HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json",
}


def search_movie(query):
    resp = requests.get(
        f"{TMDB_BASE}/search/movie",
        headers=TMDB_HEADERS,
        params={"query": query, "language": "de-DE", "page": 1},
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def search_tv(query):
    resp = requests.get(
        f"{TMDB_BASE}/search/tv",
        headers=TMDB_HEADERS,
        params={"query": query, "language": "de-DE", "page": 1},
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def get_watch_providers(tmdb_id, media_type, country="DE"):
    resp = requests.get(
        f"{TMDB_BASE}/{media_type}/{tmdb_id}/watch/providers",
        headers=TMDB_HEADERS,
    )
    resp.raise_for_status()
    de_data = resp.json().get("results", {}).get(country, {})

    for ptype, label in [("flatrate", "Stream"), ("buy", "Kauf"), ("rent", "Leihen")]:
        providers = de_data.get(ptype, [])
        if providers:
            name = providers[0].get("provider_name", "")
            for platform in ["Netflix", "Amazon", "Disney", "Sky", "Apple", "RTL", "Joyn"]:
                if platform.lower() in name.lower():
                    return platform, label
            return name, label
    return None, None


def get_movie_details(tmdb_id):
    resp = requests.get(
        f"{TMDB_BASE}/movie/{tmdb_id}",
        headers=TMDB_HEADERS,
        params={"language": "de-DE"},
    )
    resp.raise_for_status()
    d = resp.json()
    platform, avail_type = get_watch_providers(tmdb_id, "movie")

    return {
        "movie_name": d.get("title"),
        "image_url": f"{TMDB_IMG}{d['poster_path']}" if d.get("poster_path") else None,
        "movie_year": d.get("release_date", "")[:4],
        "description": d.get("overview"),
        "genres": [g["name"] for g in d.get("genres", [])],
        "available_platform": platform,
        "available_type": avail_type,
        "season_count": None,
        "movie_type": "Film",
    }


def get_series_details(tmdb_id):
    resp = requests.get(
        f"{TMDB_BASE}/tv/{tmdb_id}",
        headers=TMDB_HEADERS,
        params={"language": "de-DE"},
    )
    resp.raise_for_status()
    d = resp.json()
    platform, avail_type = get_watch_providers(tmdb_id, "tv")

    return {
        "movie_name": d.get("name"),
        "image_url": f"{TMDB_IMG}{d['poster_path']}" if d.get("poster_path") else None,
        "movie_year": d.get("first_air_date", "")[:4],
        "description": d.get("overview"),
        "genres": [g["name"] for g in d.get("genres", [])],
        "available_platform": platform,
        "available_type": avail_type,
        "season_count": d.get("number_of_seasons"),
        "movie_type": "Serie",
    }


@app.route("/movie", methods=["GET"])
def movie():
    auth_header = request.headers.get("Authorization")
    if auth_header != AUTH_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query parameter ?q="}), 400

    # Erst Film suchen, dann Serie — nimm was zuerst einen Treffer liefert
    movie_result = search_movie(query)
    tv_result = search_tv(query)

    # Wenn beide Treffer, nimm den mit höherem popularity-Wert
    if movie_result and tv_result:
        if tv_result.get("popularity", 0) > movie_result.get("popularity", 0):
            details = get_series_details(tv_result["id"])
        else:
            details = get_movie_details(movie_result["id"])
    elif movie_result:
        details = get_movie_details(movie_result["id"])
    elif tv_result:
        details = get_series_details(tv_result["id"])
    else:
        return jsonify({"error": "Movie not found"}), 404

    return jsonify(details)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)