# Unprompted: Project Architecture Overview

## About Unprompted

Unprompted is a web-based game that challenges players to guess keywords used to create AI-generated images. The game tests players' prompt engineering skills and ability to interpret AI-generated visuals.

## System Architecture

Unprompted uses a multi-tier architecture consisting of:

### 1. Frontend (Next.js)

The frontend provides the user interface for the game experience:

- **Game Interface**: Interactive components for viewing images and entering guesses
- **Score Tracking**: Real-time feedback and scoring for player guesses
- **Result Sharing**: Ability to share game results in a Wordle-like format
- **Responsive Design**: Tailwind CSS for a consistent experience across devices

### 2. Backend Services (Python)

The backend handles data processing and game management:

- **Game Scheduling**: Automated scheduling of daily game content
- **Word Similarity Processing**: Semantic analysis of player guesses
- **Data Management**: Storage and retrieval of game data and player sessions
- **Image Management**: Processing and storage of AI-generated images

### 3. Database Architecture

The project uses a multi-database approach optimized for different data requirements:

#### PostgreSQL Database
- Stores structured game data (prompts, keywords, scheduling)
- Tracks player sessions and gameplay statistics
- Enables analytics and reporting on game performance

#### Redis Database
- Provides fast, in-memory similarity data lookups
- Stores pre-computed word embeddings for real-time scoring
- Enables efficient keyword matching during gameplay

#### Vercel Blob Storage
- Stores and serves AI-generated images
- Provides CDN capabilities for fast image delivery
- Enables efficient image asset management

## Data Flow

1. **Game Data Preparation**:
   - AI images are generated and stored in Vercel Blob Storage
   - Word embeddings are pre-computed and stored in Redis
   - Game metadata (prompts, keywords) is stored in PostgreSQL

2. **Game Scheduling**:
   - The `schedule_game.py` script orchestrates deployment of new games
   - Images, similarity data, and game metadata are synchronized across databases

3. **Player Experience**:
   - Player loads the game from the Next.js frontend
   - Frontend fetches game data from the backend services
   - Player guesses are compared against keywords using similarity data
   - Results are tracked and can be shared

## Key Technologies

- **Next.js**: Frontend framework for React applications
- **Python**: Backend language for data processing and game logic
- **PostgreSQL**: Primary relational database
- **Redis**: In-memory database for fast similarity lookups
- **Vercel Blob Storage**: Cloud storage for game images
- **spaCy**: Natural language processing for word embeddings
- **Tailwind CSS**: Utility-first CSS framework

## Component Documentation

- [Frontend Documentation](frontend/README.md)
- [Backend Documentation](backend/README.md)
- [Database Setup Guide](backend/DATABASE_SETUP.md)

## Environment Configuration

The system requires proper configuration of these environment variables:

```
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@host:port/database

# Redis connection
REDIS_URL=redis://username:password@host:port

# Vercel Blob Storage
BLOB_READ_WRITE_TOKEN=your-vercel-blob-token
```