#!/usr/bin/env python3
"""
Database loader script for Unprompted game.
This script loads game data from random-i.json files into three databases:
1. Vercel Blob Storage for images
2. PostgreSQL (Neon) database for game data
3. Redis database for similarity data

Usage:
    python load_database.py [--files_dir DIR] [--db_only] [--redis_only] [--blob_only]

Arguments:
    --files_dir: Directory containing game files (default: "../frontend/public")
    --db_only: Only load data into PostgreSQL
    --redis_only: Only load data into Redis
    --blob_only: Only upload images to Vercel Blob
"""
import os
import glob
import argparse
import psycopg2
import redis
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from vercel_blob import put, put_buffer  # Vercel Blob SDK

from utils import (
    load_spacy_model,
    generate_embeddings_for_keyword,
    load_json_data,
    save_similarity_data
)

# Load environment variables from .env file
load_dotenv()

def connect_to_postgres() -> Optional[psycopg2.extensions.connection]:
    """
    Connect to PostgreSQL database.
    
    Returns:
        Connection object or None if connection fails.
    """
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        print("Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def connect_to_redis() -> Optional[redis.Redis]:
    """
    Connect to Redis database.
    
    Returns:
        Redis client object or None if connection fails.
    """
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        print("Connected to Redis database")
        return redis_client
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return None

def create_postgres_tables(conn: psycopg2.extensions.connection) -> bool:
    """
    Create necessary tables in PostgreSQL if they don't exist.
    
    Args:
        conn: PostgreSQL connection object.
        
    Returns:
        True if tables were created successfully, False otherwise.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                image_url TEXT NOT NULL,
                prompt TEXT NOT NULL,
                keywords TEXT[] NOT NULL,
                speech_types TEXT[] NOT NULL,
                start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
        return False

def insert_game_into_postgres(
    conn: psycopg2.extensions.connection,
    image_url: str,
    prompt: str,
    keywords: List[str],
    speech_types: List[str]
) -> Optional[int]:
    """
    Insert game data into PostgreSQL.
    
    Args:
        conn: PostgreSQL connection object.
        image_url: URL of the game image.
        prompt: Game prompt text.
        keywords: List of keywords for the game.
        speech_types: List of speech types for the game.
        
    Returns:
        The ID of the inserted game or None if insertion fails.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO games (image_url, prompt, keywords, speech_types, start_date)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (image_url, prompt, keywords, speech_types, datetime.now())
            )
            game_id = cur.fetchone()[0]
            conn.commit()
            return game_id
    except Exception as e:
        print(f"Error inserting game data: {e}")
        conn.rollback()
        return None

def upload_image_to_blob(local_image_path: str, base_dir: str = "../frontend/public") -> Optional[str]:
    """
    Upload image to Vercel Blob and return URL.
    
    Args:
        local_image_path: Path to the image file, relative to base_dir.
        base_dir: Base directory for images.
        
    Returns:
        URL of the uploaded image or None if upload fails.
    """
    try:
        # Resolve the full path to the image
        full_path = os.path.join(os.path.dirname(__file__), base_dir, local_image_path.lstrip('/'))
        
        # Check if the file exists
        if not os.path.exists(full_path):
            print(f"Warning: Image file not found: {full_path}")
            return None
        
        # Upload to Vercel Blob
        with open(full_path, 'rb') as f:
            blob = put_buffer(
                f.read(),
                f"game-images/{os.path.basename(local_image_path)}",
                options={"access": "public"}
            )
        return blob.url
    
    except Exception as e:
        print(f"Error uploading image to Vercel Blob: {e}")
        return None

def store_similarity_data_in_redis(
    redis_client: redis.Redis,
    keyword: str,
    similarity_data: Dict[str, float]
) -> bool:
    """
    Store similarity data for a keyword in Redis.
    
    Args:
        redis_client: Redis client object.
        keyword: The keyword for which to store similarity data.
        similarity_data: Dictionary mapping words to similarity scores.
        
    Returns:
        True if data was stored successfully, False otherwise.
    """
    try:
        # Clear existing data for this keyword
        redis_client.delete(f"similarity:{keyword}")
        
        # Store new similarity data
        for word, score in similarity_data.items():
            redis_client.hset(f"similarity:{keyword}", word, score)
        
        return True
    except Exception as e:
        print(f"Error storing similarity data in Redis for keyword '{keyword}': {e}")
        return False

def process_keyword_similarity(
    keyword: str,
    similarity_file: Optional[str],
    redis_client: redis.Redis,
    nlp: Optional[Any] = None,
    generate_if_missing: bool = True
) -> bool:
    """
    Process similarity data for a keyword and store it in Redis.
    
    Args:
        keyword: The keyword to process.
        similarity_file: Path to a file containing similarity data, or None.
        redis_client: Redis client object.
        nlp: Loaded spaCy model, or None if not needed.
        generate_if_missing: Whether to generate similarity data if file is missing.
        
    Returns:
        True if processing was successful, False otherwise.
    """
    try:
        similarity_data = {}
        
        # Load similarity data from file if it exists
        if similarity_file and os.path.exists(similarity_file):
            print(f"Loading similarity data from file: {similarity_file}")
            similarity_data = load_json_data(similarity_file)
        elif generate_if_missing and nlp:
            # Generate similarity data using spaCy
            print(f"Generating similarity data for '{keyword}' using spaCy")
            similarity_data = generate_embeddings_for_keyword(keyword, nlp)
        else:
            print(f"No similarity data found or generated for '{keyword}'")
            return False
        
        if not similarity_data:
            print(f"Empty similarity data for '{keyword}'")
            return False
        
        # Store similarity data in Redis
        print(f"Storing {len(similarity_data)} similarity entries in Redis for '{keyword}'")
        success = store_similarity_data_in_redis(redis_client, keyword, similarity_data)
        
        return success
    except Exception as e:
        print(f"Error processing similarity data for '{keyword}': {e}")
        return False

def process_game_file(
    game_file: str,
    conn: Optional[psycopg2.extensions.connection] = None,
    redis_client: Optional[redis.Redis] = None,
    upload_images: bool = True,
    process_similarity: bool = True
) -> bool:
    """
    Process a single game file, loading data into databases.
    
    Args:
        game_file: Path to the game file to process.
        conn: PostgreSQL connection or None if not using database.
        redis_client: Redis client or None if not using Redis.
        upload_images: Whether to upload images to Vercel Blob.
        process_similarity: Whether to process similarity data.
        
    Returns:
        True if processing was successful, False otherwise.
    """
    try:
        print(f"\nProcessing {game_file}")
        
        # Load game data
        game_data = load_json_data(game_file)
        if not game_data:
            return False
        
        # Extract game index from filename
        game_index = int(os.path.basename(game_file).replace("random-", "").replace(".json", ""))
        
        # Set up variables
        image_url = None
        game_id = None
        
        # 1. Upload image to Vercel Blob if requested
        if upload_images:
            image_path = game_data.get('image')
            if not image_path:
                print("No image path found in game data.")
            else:
                print(f"Uploading image: {image_path}")
                image_url = upload_image_to_blob(image_path)
                
                if image_url:
                    print(f"Image uploaded. URL: {image_url}")
                else:
                    print("Failed to upload image.")
        
        # 2. Insert game data into PostgreSQL if connection provided
        if conn:
            # If we don't have an image URL but need one for the database
            if not image_url and game_data.get('image'):
                # Just use the local path - this is a fallback
                image_url = game_data.get('image')
            
            prompt = game_data.get('prompt', '')
            keywords = game_data.get('keywords', [])
            speech_types = game_data.get('speech_type', [])
            
            print(f"Inserting game data into PostgreSQL: {prompt[:30]}...")
            game_id = insert_game_into_postgres(conn, image_url, prompt, keywords, speech_types)
            
            if game_id:
                print(f"Game inserted with ID: {game_id}")
            else:
                print("Failed to insert game data.")
        
        # 3. Process similarity data for each keyword if Redis client provided
        if redis_client and process_similarity:
            keywords = game_data.get('keywords', [])
            similarity_files = game_data.get('similarity_files', [])
            
            print("Processing similarity data for keywords:")
            
            # Load spaCy model for generating embeddings if needed
            nlp = None
            if any(i >= len(similarity_files) for i in range(len(keywords))):
                nlp = load_spacy_model()
                if not nlp:
                    print("Failed to load spaCy model for generating missing embeddings.")
            
            # Process each keyword
            for i, keyword in enumerate(keywords):
                print(f"  Processing keyword: {keyword}")
                
                # Check if we have a similarity file for this keyword
                similarity_file = None
                if i < len(similarity_files):
                    similarity_file = os.path.join(
                        os.path.dirname(__file__), 
                        "../frontend/public", 
                        similarity_files[i].lstrip('/')
                    )
                
                # Process the keyword
                success = process_keyword_similarity(keyword, similarity_file, redis_client, nlp)
                
                if success:
                    print(f"  Successfully processed similarity data for '{keyword}'")
                else:
                    print(f"  Failed to process similarity data for '{keyword}'")
        
        return True
    except Exception as e:
        print(f"Error processing {game_file}: {e}")
        return False

def find_game_files(files_dir: str) -> List[str]:
    """
    Find all random-*.json game files in the specified directory.
    
    Args:
        files_dir: Directory to search for game files.
        
    Returns:
        List of paths to game files.
    """
    base_path = os.path.join(os.path.dirname(__file__), files_dir)
    game_files = glob.glob(os.path.join(base_path, "random-*.json"))
    
    if not game_files:
        print(f"No game files found in {base_path}")
    else:
        print(f"Found {len(game_files)} game files in {base_path}")
        
    return game_files

def load_databases(
    files_dir: str = "../frontend/public",
    db_only: bool = False,
    redis_only: bool = False,
    blob_only: bool = False
) -> None:
    """
    Load data into databases from game files.
    
    Args:
        files_dir: Directory containing game files.
        db_only: Only load data into PostgreSQL.
        redis_only: Only load data into Redis.
        blob_only: Only upload images to Vercel Blob.
    """
    # Determine which operations to perform
    use_postgres = not redis_only and not blob_only
    use_redis = not db_only and not blob_only
    upload_images = not db_only and not redis_only
    
    # Connect to databases as needed
    conn = connect_to_postgres() if use_postgres else None
    redis_client = connect_to_redis() if use_redis else None
    
    # Create tables if using PostgreSQL
    if conn:
        if not create_postgres_tables(conn):
            print("Failed to create tables. Exiting.")
            if conn:
                conn.close()
            return
    
    # Find game files
    game_files = find_game_files(files_dir)
    if not game_files:
        if conn:
            conn.close()
        return
    
    # Process each game file
    success_count = 0
    for game_file in game_files:
        if process_game_file(
            game_file,
            conn=conn,
            redis_client=redis_client,
            upload_images=upload_images,
            process_similarity=use_redis
        ):
            success_count += 1
    
    print(f"\nSuccessfully processed {success_count} of {len(game_files)} game files")
    
    # Clean up connections
    if conn:
        conn.close()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Load game data into databases")
    parser.add_argument("--files_dir", default="../frontend/public", 
                      help="Directory containing game files")
    parser.add_argument("--db_only", action="store_true",
                      help="Only load data into PostgreSQL")
    parser.add_argument("--redis_only", action="store_true",
                      help="Only load data into Redis")
    parser.add_argument("--blob_only", action="store_true",
                      help="Only upload images to Vercel Blob")
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_arguments()
    load_databases(
        files_dir=args.files_dir,
        db_only=args.db_only,
        redis_only=args.redis_only,
        blob_only=args.blob_only
    )

if __name__ == "__main__":
    main()