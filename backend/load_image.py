#!/usr/bin/env python3
"""
Image loader script for Unprompted game.

This script provides a dedicated function for uploading images to Vercel Blob Storage.
It can be used independently or imported by other modules.

Usage:
    # Upload a single image
    python load_image.py --image path/to/image.webp --game-id random-0
    
    # Upload all images from all game files
    python load_image.py --all
"""
import os
import argparse
import json
from dotenv import load_dotenv
from typing import Optional, Dict, List
from vercel_blob import put, put_buffer  # Vercel Blob SDK

# Load environment variables from .env file
load_dotenv()

def load_json_data(file_path: str) -> Optional[Dict]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Loaded data or None if loading fails.
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return None

def upload_image(
    image_path: str, 
    game_id: Optional[str] = None,
    base_dir: str = "../frontend/public"
) -> Optional[str]:
    """
    Upload an image to Vercel Blob Storage.
    
    Args:
        image_path: Path to the image file, relative to base_dir.
        game_id: Optional identifier for the game this image belongs to.
        base_dir: Base directory for images.
    
    Returns:
        URL of the uploaded image or None if upload fails.
    """
    try:
        # Resolve the full path to the image
        full_path = os.path.join(os.path.dirname(__file__), base_dir, image_path.lstrip('/'))
        
        # Check if the file exists
        if not os.path.exists(full_path):
            print(f"Warning: Image file not found: {full_path}")
            return None
        
        # Create a unique blob name using game_id if provided
        blob_name = f"game-images/{game_id or 'game'}-{os.path.basename(image_path)}"
        
        # Upload to Vercel Blob
        print(f"Uploading image to Vercel Blob: {full_path} -> {blob_name}")
        with open(full_path, 'rb') as f:
            blob = put_buffer(
                f.read(),
                blob_name,
                options={"access": "public"}
            )
        print(f"Image uploaded successfully. URL: {blob.url}")
        return blob.url
    
    except Exception as e:
        print(f"Error uploading image to Vercel Blob: {e}")
        return None

def find_game_files(files_dir: str = "../frontend/public") -> List[str]:
    """
    Find all random-*.json game files in the specified directory.
    
    Args:
        files_dir: Directory to search for game files.
    
    Returns:
        List of paths to game files.
    """
    import glob
    
    base_path = os.path.join(os.path.dirname(__file__), files_dir)
    game_files = glob.glob(os.path.join(base_path, "random-*.json"))
    
    if not game_files:
        print(f"No game files found in {base_path}")
    else:
        print(f"Found {len(game_files)} game files in {base_path}")
    
    # Sort by index number
    game_files.sort(key=lambda f: int(os.path.basename(f).replace("random-", "").replace(".json", "")))
    
    return game_files

def upload_all_game_images(files_dir: str = "../frontend/public") -> Dict[str, str]:
    """
    Upload all images from all game files.
    
    Args:
        files_dir: Directory containing game files.
    
    Returns:
        Dictionary mapping game IDs to image URLs.
    """
    results = {}
    game_files = find_game_files(files_dir)
    
    for game_file in game_files:
        game_id = os.path.basename(game_file).replace(".json", "")
        print(f"\nProcessing {game_id}")
        
        # Load game data
        game_data = load_json_data(game_file)
        if not game_data or not game_data.get('image'):
            print(f"No image found in {game_file}")
            continue
        
        # Upload image
        image_url = upload_image(game_data['image'], game_id, files_dir)
        if image_url:
            results[game_id] = image_url
            print(f"Successfully uploaded image for {game_id}")
        else:
            print(f"Failed to upload image for {game_id}")
    
    return results

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Upload images to Vercel Blob Storage")
    
    # Operation modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Path to the image file to upload")
    group.add_argument("--all", action="store_true", help="Upload all images from all game files")
    
    # Optional arguments
    parser.add_argument("--game-id", help="Identifier for the game this image belongs to")
    parser.add_argument("--files-dir", default="../frontend/public", help="Directory containing game files")
    
    args = parser.parse_args()
    
    if args.all:
        results = upload_all_game_images(args.files_dir)
        print(f"\nUploaded {len(results)} images")
        
        # Print summary
        if results:
            print("\nResults:")
            for game_id, url in results.items():
                print(f"  {game_id}: {url}")
    else:
        # Upload a single image
        if not args.game_id:
            print("Warning: No game ID provided, using generic name")
        
        url = upload_image(args.image, args.game_id, args.files_dir)
        if url:
            print(f"Image uploaded successfully: {url}")
            return 0
        else:
            print("Failed to upload image")
            return 1

if __name__ == "__main__":
    main()