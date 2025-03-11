# Database Setup

## Prerequisites
- PostgreSQL
- Redis
- Python 3.11+
- OpenAI API Key
- Vercel Blob Storage configured

## Environment Variables
Create a `.env` file in the backend directory with:
```
DATABASE_URL=postgresql://user:password@localhost:5432/unprompted
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_openai_api_key
```

## Database Schema

### PostgreSQL
```sql
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    prompt_id TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    keywords JSONB NOT NULL,
    speech_types JSONB,
    date_active TIMESTAMP WITH TIME ZONE NOT NULL,
    image_url TEXT NOT NULL,
    pixelation_map JSONB
);

CREATE INDEX idx_games_date_active ON games(date_active);
```

### Redis Data Structure
- `similarity:{keyword}` - Hash storing word similarities for each keyword
- `game:{prompt_id}:keywords` - Set containing all keywords for a game
- `game:{prompt_id}:count` - String storing the number of keywords for a game

## Scheduling a New Game

1. Create a game config JSON file in `frontend/public/` with the following structure:
```json
{
    "image": "path/to/image.png",
    "prompt": "The full prompt text with [keywords] marked",
    "keywords": ["keyword1", "keyword2", ...],
    "speech_type": ["noun", "verb", ...] // Optional
}
```

2. Run the schedule_game.py script:
```bash
python schedule_game.py random-0.json --start-time "2024-01-01T00:00:00Z"
```

The script will:
- Load the game config
- Generate pixelated combinations using SAM2 segmentation
- Generate similarity data using GPT embeddings
- Upload assets to Vercel Blob Storage
- Load all data into PostgreSQL and Redis

## Notes
- The script assumes that images are in `frontend/public/`
- Pixelated combinations are generated for each keyword combination
- Speech types are optional but recommended for gameplay hints
- If no start time is provided, the game becomes active immediately