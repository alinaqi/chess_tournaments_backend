# Chess Tournament Crawler

A Python application that periodically crawls and analyzes chess tournament information from Schachinter.net.

## Features

- Regular crawling of chess tournament information from Schachinter.net
- Extraction of tournament details including name, date, location, and category
- AI-powered analysis of tournament data using Anthropic Claude
- REST API for accessing tournament data
- Modern HTML/JavaScript frontend for exploring tournament data
- Filtering and search capabilities for tournaments
- Database storage of tournament information
- Scheduled crawling at configurable intervals

## Tech Stack

- Python 3.8+
- FastAPI for REST API
- Jinja2 for HTML templating
- HTML, CSS (with Tailwind CSS), and JavaScript for frontend
- BeautifulSoup and Requests for web scraping
- Anthropic Claude for AI analysis
- Supabase for database storage
- Pydantic for data validation
- Schedule for task scheduling

## Project Structure

```
chess-tournaments/
├── src/
│   ├── app/
│   │   ├── models/
│   │   │   └── tournament.py
│   │   ├── services/
│   │   │   ├── analyzer.py
│   │   │   ├── crawler.py
│   │   │   ├── database.py
│   │   │   └── scraper.py
│   │   └── utils/
│   │       └── logging_config.py
│   ├── api.py
│   └── main.py
├── tests/
│   └── ...
├── .env
├── .env.example
└── requirements.txt
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/chess-tournaments.git
   cd chess-tournaments
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the example environment file and configure it:
   ```
   cp .env.example .env
   ```

## Configuration

Edit the `.env` file to configure the application:

```
# Crawler Configuration
CRAWL_INTERVAL=24  # In hours
TARGET_URL=https://www.schachinter.net/
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key

# Logging
LOG_LEVEL=INFO
```

## Usage

### Running the Crawler

To start the crawler with scheduled execution:

```
python src/main.py
```

To run the crawler once without scheduling:

```
python src/main.py --once
```

To specify a custom crawl interval:

```
python src/main.py --interval 12
```

### Running the API Server

To start the REST API server:

```
uvicorn src.api:app --reload
```

The API will be available at http://localhost:8000.

## API Endpoints

- `GET /tournaments` - Get all tournaments
- `GET /tournaments/{id}` - Get a specific tournament
- `POST /tournaments` - Create a new tournament
- `PUT /tournaments/{id}` - Update a tournament
- `DELETE /tournaments/{id}` - Delete a tournament

## Database Schema

### Tournaments Table

| Column          | Type      | Description                                |
|-----------------|-----------|-------------------------------------------|
| id              | UUID      | Primary key                               |
| name            | String    | Tournament name                           |
| month           | String    | Month of the tournament                   |
| year            | Integer   | Year of the tournament                    |
| start_date      | Date      | Start date (if available)                 |
| end_date        | Date      | End date (if available)                   |
| city            | String    | City where the tournament is held         |
| country         | String    | Country where the tournament is held      |
| is_international| Boolean   | Whether it's an international tournament  |
| tournament_type | String    | Type of tournament                        |
| category        | String    | Category of the tournament                |
| analysis        | Text      | AI-generated analysis                     |
| created_at      | Timestamp | Record creation timestamp                 |
| updated_at      | Timestamp | Record update timestamp                   |

## Testing

Run the tests with pytest:

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 