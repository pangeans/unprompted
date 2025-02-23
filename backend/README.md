# unprompted Backend

The backend services for the unprompted game, handling embeddings generation and game analytics.

## Features

- Generate word embeddings for semantic similarity matching
- Load and process AI-generated images
- Track game statistics and analytics
- Neon Postgres DB for storing game sessions and user performance

## Tech Stack

- Python for embedding generation
- Neon Postgres DB for data storage

## Database Schema

The database will track:
- Games (prompts, keywords, dates)
- Game sessions (player attempts)
- Individual guesses with similarity scores
- Analytics views for game statistics

## Getting Started

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Generate embeddings:
```bash
python generate_embeddings.py
```

## Analytics

The backend will provide analytics through SQL views:
- Game completion rates
- Average rounds to win
- Most challenging keywords
- Popular incorrect guesses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request