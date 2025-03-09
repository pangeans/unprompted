# Database Architecture for Unprompted

This guide explains the database architecture for the Unprompted application and provides instructions for scheduling games.

## Multi-Database Architecture Overview

Unprompted uses a multi-database architecture, with each database optimized for specific data storage needs:

1. **PostgreSQL**: Primary relational database for game data, including prompts, keywords, and scheduling information
2. **Redis**: In-memory database for fast access to word similarity data
3. **Vercel Blob Storage**: Cloud storage for game images

## Environment Setup

Create a `.env` file in the backend directory with the following configurations:

```
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@host:port/database

# Redis connection
REDIS_URL=redis://username:password@host:port

# Vercel Blob Storage
BLOB_READ_WRITE_TOKEN=your-vercel-blob-token
```

## Prerequisites

1. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Download the required spaCy model:
   ```bash
   python -m spacy download en_core_web_lg
   ```

## Database Components

### 1. PostgreSQL Database

PostgreSQL stores the core game data, including:

- **Game metadata**: Prompt text, keywords, and scheduling information
- **Game status**: Active/inactive state, start and end times

#### Schema Structure

The main tables in the PostgreSQL database include:

- **games**: Stores the primary game data
  - `id`: Unique identifier (auto-generated)
  - `prompt_id`: String identifier matching the game filename (e.g., "random-0")
  - `prompt_text`: The text of the creative prompt
  - `keywords`: Array of keywords stored as JSON
  - `date_active`: Timestamp when the game becomes active
  - `image_url`: URL to the game's image in Vercel Blob Storage

### 2. Redis Database

Redis provides fast access to word similarity data for game keywords:

- **Similarity data**: Maps words to their similarity scores for each keyword
- **Game references**: Links between games and their keywords

#### Data Structure

- **`similarity:{keyword}`**: Hash mapping words to similarity scores
- **`game:{prompt_id}:keywords`**: Set of keywords for a specific game
- **`game:{prompt_id}:count`**: Number of keywords in a game

### 3. Vercel Blob Storage

Vercel Blob Storage hosts the images associated with each game prompt:

- **Storage structure**: Images are stored with consistent naming: `game-images/{prompt_id}-{filename}`
- **Access**: Images are publicly accessible via their URLs

## Scheduling Games

The `schedule_game.py` script manages the process of scheduling a new game across all three databases.

### How to Schedule a Game

Use the following command to schedule a game:

```bash
python schedule_game.py --game-info GAME_FILE_PATH --start-time ISO8601_TIME
```

Example:
```bash
python schedule_game.py --game-info random-0.json --start-time "2023-12-31T12:00:00Z"
```

### What Happens During Scheduling

When you schedule a game, the `schedule_game.py` script performs these operations:

1. **Image Upload**: 
   - Locates the game image specified in the game JSON file
   - Uploads the image to Vercel Blob Storage with a standardized name
   - Returns a public URL for the image

2. **Game Data Loading**:
   - Extracts game metadata from the JSON file (prompt text, keywords)
   - Inserts a new record into the PostgreSQL `games` table
   - Sets the scheduled start time for the game

3. **Similarity Data Loading**:
   - For each keyword in the game:
     - Checks if similarity data already exists in Redis
     - If not, loads similarity data from corresponding JSON files
     - Stores word-similarity mappings in Redis for fast lookup

## Game File Format

Game files are stored as JSON in the `frontend/public` directory and follow this structure:

```json
{
  "prompt": "Create a story about...",
  "keywords": ["word1", "word2", "word3"],
  "image": "path/to/image.webp"
}
```

- `prompt`: The creative prompt shown to players
- `keywords`: Array of target words players need to guess
- `image`: Path to the associated image (relative to `frontend/public`)

## Troubleshooting

### Database Connection Issues

1. **PostgreSQL**:
   - Verify your DATABASE_URL in the .env file
   - Ensure network connectivity to your PostgreSQL instance
   - Check that your IP address is allowed in the database firewall settings

2. **Redis**:
   - Verify your REDIS_URL in the .env file
   - Ensure the Redis server is running and accessible

3. **Vercel Blob Storage**:
   - Verify your BLOB_READ_WRITE_TOKEN is valid
   - Check that you have sufficient permissions to upload blobs

### Game Scheduling Issues

- **Missing Game File**: Ensure the game JSON file exists in the frontend/public directory
- **Invalid JSON Format**: Validate the JSON syntax of your game file
- **Missing Image**: Ensure the referenced image exists at the specified path
- **Invalid Start Time**: Ensure the start time is in valid ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)

## Maintenance

### Monitoring Database Health

Regularly check the status of your database connections:

```bash
# PostgreSQL
psql $DATABASE_URL -c "SELECT version();"

# Redis
redis-cli -u $REDIS_URL ping
```

### Backing Up Data

It's recommended to set up regular backups for both PostgreSQL and Redis data:

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Redis backup (if using Redis Cloud, backups may be handled by the service)
redis-cli -u $REDIS_URL --rdb backup_$(date +%Y%m%d).rdb
```