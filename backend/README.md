# Unprompted Backend

This directory contains the backend services for the Unprompted game, handling word embeddings, database management, and game scheduling.

## Components

### Core Scripts

1. **schedule_game.py**: Main script for scheduling games across all databases
   - Uploads images to Vercel Blob Storage
   - Loads game data into PostgreSQL
   - Stores similarity data in Redis
   - Usage: `python schedule_game.py --game-info GAME_FILE_PATH --start-time "YYYY-MM-DDTHH:MM:SSZ"`

2. **generate_embeddings.py**: Generates word embeddings for semantic similarity matching
   - Uses spaCy for natural language processing
   - Creates similarity data for each keyword
   - Pre-computes similarity scores for efficient game scoring

3. **load_image.py**: Utility for managing game images
   - Uploads images to Vercel Blob Storage
   - Associates images with specific game IDs
   - Returns public URLs for frontend access

4. **load_similarity_data.py**: Manages similarity data in Redis
   - Loads pre-computed similarity data into Redis database
   - Maintains keyword-to-word similarity mappings
   - Supports real-time scoring during gameplay

5. **utils.py**: Shared utilities and helper functions
   - Database connection management
   - JSON data handling
   - spaCy model loading and configuration

### Database

- **schema.sql**: PostgreSQL database schema definition
  - Games table for game metadata
  - Game sessions for player interactions
  - Analytics views for game performance metrics

## Tech Stack

- **Python 3.9+**: Core programming language
- **spaCy**: Natural language processing for word embeddings
- **PostgreSQL**: Relational database for structured game data
- **Redis**: In-memory database for fast similarity lookups
- **Vercel Blob Storage**: Cloud storage for game images

## Setup and Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_lg
   ```

4. **Set up environment variables**:
   Create a `.env` file with the following variables:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   REDIS_URL=redis://username:password@host:port
   BLOB_READ_WRITE_TOKEN=your-vercel-blob-token
   ```

5. **Initialize database schema**:
   ```bash
   psql $DATABASE_URL -f schema.sql
   ```

## Scheduling Games

To schedule a new game:

```bash
python schedule_game.py --game-info random-0.json --start-time "2023-12-31T12:00:00Z"
```

This will:
1. Upload the game image to Vercel Blob Storage
2. Load game data (prompt, keywords) into PostgreSQL
3. Store similarity data in Redis for fast lookups

## Documentation

- [Database Setup Guide](DATABASE_SETUP.md): Detailed instructions for database configuration
- [Project Overview](/OVERVIEW.md): High-level architecture explanation

## Contributing

1. Set up the development environment as described above
2. Make your changes and add appropriate tests
3. Ensure your code follows PEP 8 style guidelines
4. Submit a pull request with a clear description of your changes