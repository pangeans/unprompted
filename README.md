# Unprompted

A web-based game that challenges players to guess the keywords used in AI-generated image prompts. Test your prompt engineering skills and see how well you can decode AI-generated images!

![Unprompted Game](frontend/public/random-0.webp)

## How to Play

1. You'll be shown an AI-generated image
2. Try to guess the keywords used in the prompt that generated the image
3. The game progresses through 5 rounds:
   - **Rounds 1-2**: Guess the main keywords
   - **Rounds 3-4**: Additional connector words appear (and, but, with, etc.)
   - **Round 5**: Multiple choice options for final guesses
4. Words turn green when correctly guessed and red when incorrect
5. Share your results with friends, Wordle-style!

## Project Architecture

Unprompted uses a multi-tier architecture:

- **Frontend**: Next.js web application with React components and Tailwind CSS
- **Backend**: Python services for database management and word similarity processing
- **Databases**: PostgreSQL, Redis, and Vercel Blob Storage

## Documentation

- [Project Overview](OVERVIEW.md) - High-level architecture and design
- [Frontend Documentation](frontend/README.md) - Next.js application structure and components
- [Backend Documentation](backend/README.md) - Python services for database and game management
- [Database Setup Guide](backend/DATABASE_SETUP.md) - Instructions for setting up the database components

## Development Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

To schedule a game:

```bash
python schedule_game.py --game-info GAME_FILE_PATH --start-time "YYYY-MM-DDTHH:MM:SSZ"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
