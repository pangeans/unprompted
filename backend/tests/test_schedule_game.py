import os
import json
import pytest
import redis
import psycopg2
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, ANY
import numpy as np

# Add parent directory to Python path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from schedule_game import (
    connect_to_postgres,
    connect_to_redis,
    upload_to_blob,
    process_game_media,
    load_game_data,
    load_similarity_data,
    schedule_game
)

# Test data
MOCK_GAME_DATA = {
    "image": "test.png",
    "prompt": "A test prompt with [keyword1] and [keyword2]",
    "keywords": ["keyword1", "keyword2"],
    "speech_type": ["noun", "verb"]
}

# Test vectors
MOCK_VECTOR = np.random.rand(300)

@pytest.fixture(autouse=True)
def mock_env():
    """Set up mock environment variables for all tests."""
    original_environ = dict(os.environ)
    os.environ.update({
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'REDIS_URL': 'redis://localhost:6379',
        'BLOB_READ_WRITE_TOKEN': 'test-token'
    })
    yield
    os.environ.clear()
    os.environ.update(original_environ)

@pytest.fixture
def mock_game_file(tmp_path):
    """Create a temporary game config file."""
    game_file = tmp_path / "test-game.json"
    game_file.write_text(json.dumps(MOCK_GAME_DATA))
    yield str(game_file)
    if game_file.exists():
        game_file.unlink()

@pytest.fixture
def mock_image_file(tmp_path):
    """Create a temporary test image file.""" 
    import numpy as np
    from PIL import Image
    
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:50, :50] = [255, 0, 0]
    img[50:, 50:] = [0, 255, 0]
    
    image_path = tmp_path / "test.png"
    Image.fromarray(img).save(image_path)
    yield str(image_path)
    if image_path.exists():
        image_path.unlink()

@pytest.fixture
def mock_db():
    """Mock database connection and cursor."""
    mock_conn = Mock()
    mock_cur = Mock()
    mock_cur.fetchone.return_value = (1,)
    mock_cur.fetchall.return_value = [('id',), ('prompt_id',)]  # Mock column names
    
    # Properly mock the cursor context manager
    mock_cm = Mock()
    mock_cm.__enter__ = Mock(return_value=mock_cur)
    mock_cm.__exit__ = Mock(return_value=None)
    mock_conn.cursor.return_value = mock_cm
    
    return mock_conn, mock_cur

@pytest.fixture
def mock_redis_client():
    """Mock Redis client with pipeline support."""
    mock_client = Mock()
    mock_pipeline = Mock()
    # Properly mock the pipeline context manager
    mock_client.pipeline = Mock(return_value=mock_pipeline)
    mock_pipeline.hset = Mock()
    mock_pipeline.execute = Mock()
    mock_pipeline.delete = Mock()
    return mock_client, mock_pipeline

@pytest.fixture
def mock_spacy_nlp():
    """Create a mock spaCy model with minimal functionality."""
    mock_nlp = Mock()
    
    # Mock document with vector
    mock_doc = Mock()
    mock_doc.has_vector = True
    mock_doc.vector = MOCK_VECTOR
    mock_doc.similarity = lambda x: 0.8 if x.has_vector else 0
    
    # Mock token
    mock_token = Mock()
    mock_token.text = "test"
    mock_token.lemma_ = "test"
    mock_token.pos_ = "NOUN"
    mock_doc.__iter__ = lambda self: iter([mock_token])
    
    # Set up vocabulary
    mock_words = [
        Mock(text=f"similar{i}", has_vector=True, is_lower=True, rank=100+i)
        for i in range(1, 4)
    ]
    mock_nlp.vocab = mock_words
    mock_nlp.return_value = mock_doc
    
    return mock_nlp

def test_connect_to_postgres(mock_env):
    """Test PostgreSQL connection with error cases."""
    with patch('psycopg2.connect') as mock_connect:
        # Test successful connection
        mock_connect.return_value = Mock()
        conn = connect_to_postgres()
        assert conn is not None
        mock_connect.assert_called_with('postgresql://test:test@localhost:5432/test')
        
        # Test connection failure
        mock_connect.side_effect = Exception("Connection failed")
        with pytest.raises(Exception):
            connect_to_postgres()

def test_connect_to_redis(mock_env):
    """Test Redis connection with ping check."""
    with patch('redis.Redis.from_url') as mock_redis:
        # Test successful connection
        client = Mock()
        client.ping.return_value = True
        mock_redis.return_value = client
        redis_client = connect_to_redis()
        assert redis_client is not None
        client.ping.assert_called_once()
        
        # Test failed ping - should raise RuntimeError
        client.ping.side_effect = redis.ConnectionError("Connection failed")
        with pytest.raises(redis.ConnectionError):
            connect_to_redis()

def test_upload_to_blob(mock_image_file):
    """Test blob storage upload with various scenarios."""
    with patch('vercel_blob.put') as mock_put:
        # Test successful upload
        mock_put.return_value = {'url': 'https://example.com/test.png'}
        url = upload_to_blob(mock_image_file, 'test.png')
        assert url == 'https://example.com/test.png'
        mock_put.assert_called_once()
        
        # Test upload failure - should return None
        mock_put.side_effect = Exception("Upload failed")
        assert upload_to_blob(mock_image_file, 'test.png') is None
        
        # Test invalid file - should return None
        assert upload_to_blob('nonexistent.png', 'test.png') is None

def test_process_game_media(mock_image_file, tmp_path):
    """Test game media processing with various inputs."""
    with patch('schedule_game.process_image_segmentation') as mock_process, \
         patch('schedule_game.upload_to_blob') as mock_upload:
        
        # Test successful processing
        mock_process.return_value = {
            '0_1blur.webp': '/path/to/pixelated1.webp',
            '0blur_1.webp': '/path/to/pixelated2.webp'
        }
        mock_upload.side_effect = [
            'https://example.com/original.png',
            'https://example.com/pixelated1.webp',
            'https://example.com/pixelated2.webp'
        ] * 3  # Multiply the list to handle multiple calls
        
        image_url, pixelation_map = process_game_media(
            Path(mock_image_file).name,  # Just the filename
            ['word1', 'word2'],
            'test-0',
            base_dir=str(tmp_path)  # Use temp dir as base
        )
        
        assert image_url == 'https://example.com/original.png'
        assert len(pixelation_map) == 2
        assert all(url.startswith('https://') for url in pixelation_map.values())
        
        # Test processing failure - should return None, None
        mock_process.side_effect = Exception("Processing failed")
        result = process_game_media(
            Path(mock_image_file).name,
            ['word1'],
            'test-1',
            base_dir=str(tmp_path)
        )
        assert result == (None, None)
        
        # Test video processing
        video_path = tmp_path / "test.mp4"
        video_path.write_bytes(b'dummy video')  # Create dummy video file
        
        with patch('schedule_game.is_video_file', return_value=True), \
             patch('schedule_game.process_video_segmentation') as mock_video_process:
            mock_video_process.return_value = {
                'frame1.webp': '/path/to/frame1.webp',
                'frame2.webp': '/path/to/frame2.webp'
            }
            mock_upload.side_effect = [
                'https://example.com/original.mp4',
                'https://example.com/frame1.webp',
                'https://example.com/frame2.webp'
            ]
            
            video_url, frame_map = process_game_media(
                video_path.name,
                ['word1', 'word2'],
                'test-2',
                base_dir=str(tmp_path)
            )
            
            assert video_url == 'https://example.com/original.mp4'
            assert len(frame_map) == 2

def test_load_game_data(mock_game_file, mock_db):
    """Test loading game data into PostgreSQL."""
    mock_conn, mock_cur = mock_db
    
    with patch('schedule_game.connect_to_postgres', return_value=mock_conn), \
         patch('schedule_game.load_json_data', return_value=MOCK_GAME_DATA):
        # Test successful load
        game_id = load_game_data(
            mock_game_file,
            'https://example.com/test.png',
            {'0_1blur.webp': 'https://example.com/pixelated.webp'},
            '2024-01-01T00:00:00Z'
        )
        assert game_id == 1
        mock_cur.execute.assert_called()
        mock_conn.commit.assert_called()
        
        # Test database error
        mock_cur.execute.side_effect = psycopg2.Error("Database error")
        assert load_game_data(
            mock_game_file,
            'https://example.com/test.png',
            {},
            '2024-01-01T00:00:00Z'
        ) is None

def test_load_similarity_data(mock_spacy_nlp, mock_redis_client):
    """Test loading similarity data into Redis."""
    mock_client, mock_pipeline = mock_redis_client
    
    with patch('schedule_game.connect_to_redis', return_value=mock_client), \
         patch('schedule_game.generate_embeddings', return_value={
            'keyword1': {'similar1': 0.8, 'similar2': 0.6},
            'keyword2': {'similar3': 0.7, 'similar4': 0.5}
         }):
        
        # Test successful load
        success = load_similarity_data(['keyword1', 'keyword2'], 'test-0')
        assert success
        mock_pipeline.execute.assert_called()
        
        # Test Redis error
        mock_pipeline.execute.side_effect = Exception("Redis error")
        with pytest.raises(Exception):
            load_similarity_data(['keyword1'], 'test-1')

def test_schedule_game_full_flow(mock_game_file, mock_image_file):
    """Test the complete game scheduling flow."""
    with patch('schedule_game.process_game_media') as mock_process, \
         patch('schedule_game.load_game_data') as mock_load_game, \
         patch('schedule_game.load_similarity_data') as mock_load_sim, \
         patch('schedule_game.load_json_data', return_value=MOCK_GAME_DATA):
        
        mock_process.return_value = (
            'https://example.com/test.png',
            {'0_1blur.webp': 'https://example.com/pixelated.webp'}
        )
        mock_load_game.return_value = 1
        mock_load_sim.return_value = True
        
        success = schedule_game(mock_game_file)
        assert success
        
        mock_process.assert_called_once()
        mock_load_game.assert_called_once()
        mock_load_sim.assert_called_once()

def test_schedule_game_error_cases():
    """Test various error scenarios in game scheduling."""
    # Test nonexistent file
    with patch('schedule_game.load_json_data', side_effect=FileNotFoundError):
        success = schedule_game('nonexistent.json')
        assert not success
    
    # Test invalid game data
    with patch('schedule_game.load_json_data', return_value={}):
        success = schedule_game('test.json')
        assert not success
    
    # Test processing error
    with patch('schedule_game.load_json_data', return_value=MOCK_GAME_DATA), \
         patch('schedule_game.process_game_media', side_effect=Exception("Processing failed")):
        success = schedule_game('test.json')
        assert not success