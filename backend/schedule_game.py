#!/usr/bin/env python3
"""
Schedule Game

A utility for managing and scheduling games for the Unprompted application.
Handles the entire flow:
1. Load game config
2. Generate pixelated combinations using segmenter
3. Generate similarity data
4. Upload assets to Vercel Blob Storage
5. Load data into databases
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import psycopg2
import redis
import vercel_blob
import dateutil.parser
from dotenv import load_dotenv

from generate_embeddings import generate_embeddings
from utils import load_json_data

# Add segmenter to Python path
import sys
from segmenter import process_image as process_image_segmentation
from segmenter import process_video as process_video_segmentation

# Load environment variables
load_dotenv()

def connect_to_postgres() -> psycopg2.extensions.connection:
    """Connect to PostgreSQL database using environment variables."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL', ''))
    print("Connected to PostgreSQL database")
    return conn

def connect_to_redis() -> redis.Redis:
    """Connect to Redis database using environment variables."""
    redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL", ""))
    redis_client.ping()  # Test connection
    print("Connected to Redis database")
    return redis_client

def upload_to_blob(
    file_path: str | Path,
    blob_name: str,
    access: str = "public"
) -> Optional[str]:
    """
    Upload a file to Vercel Blob Storage.
    
    Args:
        file_path: Path to the file to upload
        blob_name: Name to give the blob
        access: Access level ("public" or "private")
        
    Returns:
        URL of the uploaded file or None if upload fails
    """
    try:
        print(f"Uploading to Vercel Blob: {file_path} -> {blob_name}")
        with open(file_path, 'rb') as f:
            blob = vercel_blob.put(
                blob_name,
                f.read(),
                options={"access": access}
            )
        print(f"Upload successful. URL: {blob['url']}")
        return blob['url']
    except Exception as e:
        print(f"Error uploading to blob storage: {e}")
        return None

def is_video_file(file_path: str | Path) -> bool:
    """
    Check if a file is a video based on its extension.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is a video, False otherwise
    """
    video_extensions = ['.mp4', '.gif', '.mov', '.avi', '.webm']
    return Path(file_path).suffix.lower() in video_extensions

def process_game_media(
    media_path: str | Path,
    keywords: List[str],
    prompt_id: str,
    base_dir: str = "../frontend/public"
) -> tuple[Optional[str], Optional[Dict[str, str]]]:
    """
    Process a game media file (image or video):
    1. Generate pixelated combinations
    2. Upload original and pixelated media to blob storage
    
    Returns:
        Tuple of (original media URL, pixelation map with URLs)
    """
    try:
        # Resolve the full path to the media file
        full_path = Path(base_dir) / media_path.lstrip('/')
        if not full_path.exists():
            print(f"Error: Media file not found: {full_path}")
            return None, None
            
        # Upload original media
        blob_name = f"game-images/{prompt_id}-{Path(media_path).name}"
        media_url = upload_to_blob(full_path, blob_name)
        if not media_url:
            return None, None
            
        # Generate pixelated combinations based on file type
        print("\nGenerating pixelated combinations...")
        
        try:
            if is_video_file(full_path):
                print(f"Processing video file: {full_path}")
                pixelation_map = process_video_segmentation(
                    str(full_path),
                    keywords
                )
            else:
                print(f"Processing image file: {full_path}")
                pixelation_map = process_image_segmentation(
                    str(full_path),
                    keywords
                )
        except Exception as e:
            print(f"Error during media processing: {e}")
            return None, None
            
        if not pixelation_map:
            print("Warning: Failed to generate pixelated combinations")
            return media_url, None
            
        # Upload each pixelated combination
        uploaded_map = {}
        for filename, file_path in pixelation_map.items():
            blob_name = f"game-images/{prompt_id}-pixelated-{filename}"
            if url := upload_to_blob(file_path, blob_name):
                uploaded_map[filename] = url
        
        return media_url, uploaded_map
    except Exception as e:
        print(f"Error in process_game_media: {e}")
        return None, None

def load_game_data(
    game_file: str | Path,
    image_url: str,
    pixelation_map: Optional[Dict[str, str]],
    start_time: Optional[str] = None,
) -> Optional[int]:
    """Load game data into PostgreSQL."""
    conn = connect_to_postgres()
    
    try:
        # Load game data
        game_data = load_json_data(str(game_file))
        if not game_data:
            print(f"Failed to load game data from {game_file}")
            return None
            
        # Extract prompt ID from filename
        prompt_id = Path(game_file).stem

        # Check if the media is a video
        is_video = is_video_file(game_data.get('image', ''))
        
        # Parse start time with improved timezone handling
        try:
            if start_time:
                # Parse the timestamp, preserving timezone info
                parsed_time = dateutil.parser.parse(start_time)
                # Ensure timezone is specified
                if parsed_time.tzinfo is None:
                    raise ValueError("Start time must include timezone information (e.g. 2024-01-01T15:30:00Z or 2024-01-01T10:30:00-05:00)")
            else:
                # Use current time in UTC
                parsed_time = datetime.now(timezone.utc)
            
            # Always normalize to UTC for storage
            parsed_time = parsed_time.astimezone(timezone.utc)
            
        except Exception as e:
            print(f"Error parsing start time '{start_time}': {e}")
            return None
            
        # Extract game data
        prompt_text = game_data.get('prompt', '')
        keywords = game_data.get('keywords', [])
        speech_types = game_data.get('speech_type', [])
        
        # Check for required columns
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='games'
            """)
            columns = {row[0] for row in cur.fetchall()}
            
            if 'pixelation_map' not in columns:
                print("Adding pixelation_map column to games table")
                cur.execute("ALTER TABLE games ADD COLUMN pixelation_map JSONB")
                
            if 'media_type' not in columns:
                print("Adding media_type column to games table")
                cur.execute("ALTER TABLE games ADD COLUMN media_type VARCHAR(10)")
                
            conn.commit()
        
        # Insert into database with explicit timestamp format
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO games (
                    prompt_id, prompt_text, keywords, speech_types, 
                    date_active, image_url, pixelation_map, media_type
                )
                VALUES (%s, %s, %s, %s, %s::timestamptz, %s, %s, %s)
                RETURNING id, date_active
                """,
                (
                    prompt_id, 
                    prompt_text, 
                    json.dumps(keywords), 
                    json.dumps(speech_types), 
                    parsed_time.isoformat(), 
                    image_url, 
                    json.dumps(pixelation_map) if pixelation_map else None,
                    'video' if is_video else 'image'
                )
            )
            game_id, stored_time = cur.fetchone()
            conn.commit()
            
            print(f"Inserted new game record with ID {game_id}")
            print(f"Stored activation time: {stored_time}")
            return game_id
            
    except Exception as e:
        print(f"Error loading game data: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def load_similarity_data(
    keywords: List[str],
    prompt_id: str
) -> bool:
    """Generate and load similarity data for keywords into Redis."""
    redis_client = None
    try:
        redis_client = connect_to_redis()
        
        # Generate similarity data for all keywords
        print("\nGenerating similarity data...")
        similarity_data = generate_embeddings(keywords, 5000)
        
        # Store in Redis using a single pipeline
        pipeline = redis_client.pipeline()
        
        # Store similarity data for each keyword
        for keyword, similarities in similarity_data.items():
            redis_key = f"similarity:{keyword.lower()}"
            print(f"Storing {len(similarities)} similarity entries for '{keyword}'")
            
            # Clear existing data and store new similarities
            pipeline.delete(redis_key)
            for word, score in similarities.items():
                pipeline.hset(redis_key, word, score)
                
            # Add reference to game
            pipeline.sadd(f"game:{prompt_id}:keywords", keyword.lower())
        
        # Store keyword count
        pipeline.set(f"game:{prompt_id}:count", len(keywords))
        
        # Execute all commands in a single transaction
        pipeline.execute()
        return True
            
    finally:
        if redis_client:
            redis_client.close()

def schedule_game(
    game_file: str | Path,
    start_time: Optional[str] = None,
    base_dir: str = "../frontend/public"
) -> bool:
    """
    Schedule a new game by:
    1. Loading the game config
    2. Generating pixelated combinations
    3. Generating similarity data
    4. Uploading assets to blob storage
    5. Loading everything into databases
    
    Args:
        game_file: Path to the game JSON config file
        start_time: Optional ISO 8601 formatted start time
        base_dir: Base directory for game files
    
    Returns:
        True if all operations succeeded, False otherwise
    """
    try:
        print(f"\nScheduling new game from {game_file}")
        
        # Load game config
        game_path = Path(base_dir) / game_file.lstrip('/')
        try:
            game_data = load_json_data(str(game_path))
        except FileNotFoundError:
            print(f"Error loading data from {game_path}: FileNotFoundError")
            return False
            
        if not game_data:
            print(f"Failed to load game config from {game_file}")
            return False
        
        # Extract key data
        prompt_id = Path(game_file).stem
        image_path = game_data.get('image')
        keywords = game_data.get('keywords', [])
        
        if not image_path or not keywords:
            print("Error: Game config must specify 'image' and 'keywords'")
            return False
        
        # Process the media and generate pixelated combinations
        media_url, pixelation_map = process_game_media(
            image_path,
            keywords,
            prompt_id,
            base_dir
        )
        if not media_url:
            print("Failed to process game media")
            return False
        
        # Load game data into PostgreSQL
        game_id = load_game_data(game_path, media_url, pixelation_map, start_time)
        if not game_id:
            print("Failed to load game data into PostgreSQL")
            return False
        
        # Generate and load similarity data into Redis
        redis_success = load_similarity_data(keywords, prompt_id)
        if not redis_success:
            print("Failed to load similarity data into Redis")
            return False
        
        print(f"\nSuccessfully scheduled game {prompt_id} (ID: {game_id})")
        if start_time:
            print(f"Game will become active at: {start_time}")
        else:
            print("Game is active immediately")
        
        return True
        
    except Exception as e:
        print(f"Error scheduling game: {e}")
        return False

def main():
    """Entry point for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Schedule games for the Unprompted application"
    )
    parser.add_argument(
        "game_file",
        help="Path to the game JSON config file"
    )
    parser.add_argument(
        "--start-time",
        help="ISO 8601 formatted start time (e.g. 2024-01-01T00:00:00Z)"
    )
    parser.add_argument(
        "--base-dir",
        default="game-configs",
        help="Base directory for game files"
    )
    
    args = parser.parse_args()
    
    success = schedule_game(
        args.game_file,
        args.start_time,
        args.base_dir
    )
    
    if not success:
        print("\nGame scheduling failed")
        sys.exit(1)

if __name__ == "__main__":
    main()