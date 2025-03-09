#!/usr/bin/env python3
"""
Schedule Game

A utility for managing and scheduling games for the Unprompted application.

This script provides functions for:
1. Uploading images to Vercel Blob Storage
2. Loading game data into PostgreSQL database
3. Loading similarity data into Redis
4. Scheduling games with a specific start time

Usage:
    python schedule_game.py --game-info GAME_FILE --start-time ISO8601_TIME
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, TypeVar, cast

import psycopg2
import redis
import dateutil.parser
import vercel_blob
from dotenv import load_dotenv

from utils import load_json_data

# Load environment variables from .env file
load_dotenv()

# Type definitions
T = TypeVar('T')
JsonDict = Dict[str, Any]
RedisClient = redis.Redis
PostgresConnection = psycopg2.extensions.connection


def connect_to_postgres() -> PostgresConnection:
    """Connect to PostgreSQL database using environment variables."""
    conn = psycopg2.connect(os.getenv('DATABASE_URL', ''))
    print("Connected to PostgreSQL database")
    return conn


def connect_to_redis() -> RedisClient:
    """Connect to Redis database using environment variables."""
    redis_client = redis.Redis.from_url(os.environ.get("REDIS_URL", ""))
    redis_client.ping()  # Test connection
    print("Connected to Redis database")
    return redis_client


def load_image(
    image_path: str, 
    game_id: Optional[str] = None,
    base_dir: str = "../frontend/public"
) -> Optional[str]:
    """
    Upload an image to Vercel Blob Storage.
    
    Args:
        image_path: Path to the image file, relative to base_dir
        game_id: Optional identifier for the game this image belongs to
        base_dir: Base directory for images
    
    Returns:
        URL of the uploaded image or None if upload fails
    """
    # Resolve the full path to the image
    full_path = Path(__file__).parent / base_dir / image_path.lstrip('/')
    
    # Check if the file exists
    if not full_path.exists():
        print(f"Warning: Image file not found: {full_path}")
        return None
    
    # Create a unique blob name using game_id if provided
    blob_name = f"game-images/{game_id or 'game'}-{Path(image_path).name}"
    
    # Upload to Vercel Blob
    print(f"Uploading image to Vercel Blob: {full_path} -> {blob_name}")
    with open(full_path, 'rb') as f:
        blob = vercel_blob.put(
            blob_name,
            f.read(),
            options={"access": "public"}
        )
        
    print(f"Image uploaded successfully. URL: {blob['url']}")
    return blob['url']


def load_game_data(
    game_file: str,
    start_time: Optional[str] = None,
    image_url: Optional[str] = None,
    base_dir: str = "../frontend/public"
) -> Optional[int]:
    """
    Load game data into PostgreSQL.
    
    Args:
        game_file: Path to the game JSON file
        start_time: ISO 8601 formatted string for when the game should start
        image_url: Optional URL of already uploaded image
        base_dir: Base directory for game files
    
    Returns:
        ID of the inserted game record, or None if operation failed
    """
    conn = connect_to_postgres()
    
    try:
        # Load game data from file
        file_path = Path(__file__).parent / base_dir / game_file.lstrip('/')
        game_data = load_json_data(str(file_path))
        if not game_data:
            print(f"Failed to load game data from {game_file}")
            return None
        
        # Extract prompt ID from filename
        prompt_id = Path(game_file).stem
        
        # Parse start time or use current time
        try:
            parsed_time = dateutil.parser.parse(start_time) if start_time else datetime.now(timezone.utc)
            # Ensure timezone awareness
            if parsed_time.tzinfo is None:
                parsed_time = parsed_time.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(f"Error parsing start time '{start_time}': {e}")
            parsed_time = datetime.now(timezone.utc)
        
        # Extract game data
        prompt_text = game_data.get('prompt', '')
        keywords = game_data.get('keywords', [])
        speech_types = game_data.get('speech_type', [])  # Get speech types from JSON
        
        # Insert into database
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO games (prompt_id, prompt_text, keywords, speech_types, date_active, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (prompt_id, prompt_text, json.dumps(keywords), json.dumps(speech_types), parsed_time, image_url)
            )
            game_id = cur.fetchone()[0]
            conn.commit()
            print(f"Inserted new game record with ID {game_id}")
            return game_id
            
    except Exception as e:
        print(f"Error loading game data: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def load_similarity_data(
    game_file: str,
    base_dir: str = "../frontend/public"
) -> bool:
    """
    Load similarity data for a game's keywords into Redis.
    
    Args:
        game_file: Path to the game JSON file
        base_dir: Base directory for game files
    
    Returns:
        True if similarity data was loaded successfully, False otherwise
    """
    try:
        redis_client = connect_to_redis()
        
        # Load game data from file
        file_path = Path(__file__).parent / base_dir / game_file.lstrip('/')
        game_data = load_json_data(str(file_path))
        if not game_data:
            print(f"Failed to load game data from {game_file}")
            return False
        
        # Extract prompt ID from filename for reference
        prompt_id = Path(game_file).stem
        
        # Extract keywords
        keywords = game_data.get('keywords', [])
        if not keywords:
            print(f"No keywords found in game data for {game_file}")
            return False
                        
        # Process each keyword
        success_count = 0
        for keyword in keywords:
            # Create Redis key for this keyword
            keyword_lower = keyword.lower()
            redis_key = f"similarity:{keyword_lower}"
            
            # Check if data already exists
            if redis_client.exists(redis_key):
                print(f"Similarity data for '{keyword}' already exists in Redis")
                success_count += 1
                continue
            
            # Look for a JSON file with similarity data
            similarity_file = Path(__file__).parent / base_dir / f"{keyword_lower}.json"
            
            # Load similarity data from file if it exists
            if similarity_file.exists():
                print(f"Loading similarity data from file for '{keyword}'")
                similarity_data = load_json_data(str(similarity_file))
                
                if not similarity_data:
                    print(f"Empty similarity data for '{keyword}'")
                    continue
                
                # Store in Redis
                print(f"Storing {len(similarity_data)} similarity entries in Redis for '{keyword}'")
                # Clear existing data
                redis_client.delete(redis_key)
                
                # Store new data
                pipeline = redis_client.pipeline()
                for word, score in similarity_data.items():
                    pipeline.hset(redis_key, word, score)
                pipeline.execute()
                
                # Add reference to game
                redis_client.sadd(f"game:{prompt_id}:keywords", keyword_lower)
                
                success_count += 1
            else:
                print(f"Cannot find similarity data for '{keyword}'")
                continue
        
        # Store a reference to this game's keywords
        redis_client.set(f"game:{prompt_id}:count", len(keywords))
        
        return success_count == len(keywords)
    
    finally:
        if 'redis_client' in locals():
            redis_client.close()


def schedule_game(
    game_file: str,
    start_time: Optional[str] = None,
    base_dir: str = "../frontend/public"
) -> bool:
    """
    Schedule a game by loading it into all databases with the specified start time.
    
    Args:
        game_file: Path to the game JSON file
        start_time: ISO 8601 formatted string for when the game should start
        base_dir: Base directory for game files
    
    Returns:
        True if all operations were successful, False otherwise
    """
    # Load game data from file
    file_path = Path(__file__).parent / base_dir / game_file.lstrip('/')
    game_data = load_json_data(str(file_path))
    if not game_data:
        print(f"Failed to load game data from {game_file}")
        return False
    
    # Extract prompt ID from filename
    prompt_id = Path(game_file).stem
    print(f"Scheduling game {prompt_id} for {start_time or 'now'}")
    
    # 1. Upload image to Vercel Blob
    image_path = game_data.get('image')
    image_url = load_image(image_path, prompt_id, base_dir)
    if not image_url:
        print("Failed to upload image to Vercel Blob")
        return False
    
    # 2. Load game data into PostgreSQL with the image URL
    game_id = load_game_data(game_file, start_time, image_url, base_dir)
    if not game_id:
        print("Failed to load game data into PostgreSQL")
        return False
    
    # 3. Load similarity data into Redis
    redis_success = load_similarity_data(game_file, base_dir)
    if not redis_success:
        print("Failed to load all similarity data into Redis")
        return False
    
    print(f"Successfully scheduled game {prompt_id} (ID: {game_id}) for {start_time or 'now'}")
    return True


def main() -> None:
    """Entry point for the script."""
    parser = argparse.ArgumentParser(description="Schedule games for the Unprompted application")
    
    # Command line arguments
    parser.add_argument("--game-info", metavar="GAME_FILE", required=True, help="Path to the game JSON file to schedule")
    parser.add_argument("--start-time", required=True, help="ISO 8601 formatted start time for scheduling the game")    
    args = parser.parse_args()
    
    # Schedule the game
    success = schedule_game(args.game_info, args.start_time)
    print(f"Game scheduling {'succeeded' if success else 'failed'}")


if __name__ == "__main__":
    main()