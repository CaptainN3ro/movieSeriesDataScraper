# movieSeriesDataScraper

A lightweight REST API that scrapes movie and series metadata from [The Movie Database (TMDb)](https://www.themoviedb.org/). Given a search query, it returns structured data including title, year, description, genres, poster image, streaming availability, and more.

## Features

- Search movies and series by name
- Returns poster image URL, description, genres, release year
- Detects streaming platform availability (Netflix, Amazon, Sky, Disney+)
- Distinguishes between films and series (including season count)
- Auth-protected endpoint
- Docker-ready with health check

## API

### `GET /movie?q=<query>`

Returns metadata for the best matching result.

**Headers:**

| Header          | Value                  |
|-----------------|------------------------|
| `Authorization` | Your configured `AUTH_KEY` |

**Query Parameters:**

| Parameter | Description         |
|-----------|---------------------|
| `q`       | Search term (required) |

**Example Request:**

```bash
curl -H "Authorization: Basic YourSecretKeyHere" \
  "http://localhost:2000/movie?q=Inception"
```

**Example Response:**

```json
{
  "movie_name": "Inception",
  "image_url": "https://image.tmdb.org/...",
  "movie_year": "2010",
  "description": "Cobb, a skilled thief...",
  "genres": ["Action", "Science Fiction", "Adventure"],
  "available_platform": "Netflix",
  "available_type": "Stream",
  "season_count": null,
  "movie_type": "Film"
}
```

### `GET /health`

Returns `200 OK` if the service is running. No authentication required.

## Getting Started

### With Docker Compose (recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/CaptainN3ro/movieSeriesDataScraper.git
   cd movieSeriesDataScraper
   ```

2. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env and set a secure AUTH_KEY
   # Insert also your tmdb access token TMDB_TOKEN (free for private use)
   ```

3. Start the service:
   ```bash
   docker compose up -d
   ```

4. Test it:
   ```bash
   curl -H "Authorization: Basic YourSecretKeyHere" \
     "http://localhost:2000/movie?q=Breaking+Bad"
   ```

### With Docker (manual)

```bash
docker build -t movie-scraper .
docker run -p 2000:2000 -e AUTH_KEY="Basic YourKey" movie-scraper
```

### Local Development

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

export AUTH_KEY="Basic YourKey"
export FLASK_DEBUG=true
python app.py
```

## Configuration

All configuration is done via environment variables:

| Variable      | Default                   | Description                        |
|---------------|---------------------------|------------------------------------|
| `AUTH_KEY`    | `Basic YourSecretKeyHere` | Authorization header value         |
| `TMDB_TOKEN`  | ``                        | Your tmdb api token                |
| `PORT`        | `2000`                    | Port the server listens on         |
| `FLASK_DEBUG` | `false`                   | Enable Flask debug mode            |

> **Security note:** Always change the default `AUTH_KEY` before deploying to a public environment.

## Error Responses

| Status | Meaning                          |
|--------|----------------------------------|
| `400`  | Missing `?q=` parameter         |
| `401`  | Invalid or missing Authorization |
| `404`  | No matching movie/series found   |

## License

MIT
