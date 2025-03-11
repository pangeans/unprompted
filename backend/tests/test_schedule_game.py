import os
import json
import pytest
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
    process_game_image,
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

# Add mock data for spaCy 
MOCK_VECTOR = np.random.rand(300)  # spaCy typically uses 300-dimensional vectors

@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
        'REDIS_URL': 'redis://localhost:6379'
    }):
        yield

@pytest.fixture
def mock_game_file(tmp_path):
    """Create a temporary game config file."""
    game_file = tmp_path / "test-game.json"
    game_file.write_text(json.dumps(MOCK_GAME_DATA))
    return str(game_file)

@pytest.fixture
def mock_image_file(tmp_path):
    """Create a temporary test image file.""" 
    import numpy as np
    from PIL import Image
    
    # Create a simple test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:50, :50] = [255, 0, 0]  # Red square
    img[50:, 50:] = [0, 255, 0]  # Green square
    
    image_path = tmp_path / "test.png"
    Image.fromarray(img).save(image_path)
    return str(image_path)

@pytest.fixture
def mock_spacy_nlp():
    """Create a mock spaCy model with minimal functionality for testing."""
    mock_nlp = Mock()
    
    # Mock document with vector
    mock_doc = Mock()
    mock_doc.has_vector = True
    mock_doc.vector = MOCK_VECTOR
    
    # Mock token for word list generation
    mock_token = Mock()
    mock_token.text = "test"
    mock_token.lemma_ = "test"
    mock_token.pos_ = "NOUN"
    mock_doc.__iter__ = lambda self: iter([mock_token])
    
    # Set up vocabulary for similarity testing
    mock_word1 = Mock()
    mock_word1.text = "similar1"
    mock_word1.has_vector = True
    mock_word1.is_lower = True
    mock_word1.rank = 100
    
    mock_word2 = Mock()
    mock_word2.text = "similar2"
    mock_word2.has_vector = True
    mock_word2.is_lower = True
    mock_word2.rank = 200
    
    mock_vocab = [mock_word1, mock_word2]
    mock_nlp.vocab = mock_vocab
    
    # Set up document creation
    mock_nlp.return_value = mock_doc
    
    # Set up similarity function
    mock_doc.similarity = lambda x: 0.8 if x.has_vector else 0
    
    return mock_nlp

def test_connect_to_postgres(mock_env):
    """Test PostgreSQL connection."""
    with patch('psycopg2.connect') as mock_connect:
        mock_connect.return_value = Mock()
        conn = connect_to_postgres()
        assert conn is not None
        mock_connect.assert_called_once_with('postgresql://test:test@localhost:5432/test')

def test_connect_to_redis(mock_env):
    """Test Redis connection."""
    with patch('redis.Redis.from_url') as mock_redis:
        mock_redis.return_value = Mock()
        mock_redis.return_value.ping.return_value = True
        client = connect_to_redis()
        assert client is not None
        mock_redis.assert_called_once_with('redis://localhost:6379')

def test_upload_to_blob(mock_image_file):
    """Test blob storage upload."""
    with patch('vercel_blob.put') as mock_put:
        mock_put.return_value = {'url': 'https://example.com/test.png'}
        url = upload_to_blob(mock_image_file, 'test.png')
        assert url == 'https://example.com/test.png'
        mock_put.assert_called_once()

def test_process_game_image(mock_image_file):
    """Test game image processing."""
    with patch('schedule_game.process_image_segmentation') as mock_process:
        mock_process.return_value = {
            '0_1blur.webp': '/path/to/pixelated1.webp',
            '0blur_1.webp': '/path/to/pixelated2.webp'
        }
        with patch('schedule_game.upload_to_blob') as mock_upload:
            # Make sure we have enough return values for all calls
            mock_upload.side_effect = [
                'https://example.com/original.png',
                'https://example.com/pixelated1.webp',
                'https://example.com/pixelated2.webp'
            ]
            
            image_url, pixelation_map = process_game_image(
                mock_image_file,
                ['word1', 'word2'],
                'test-0'
            )
            
            assert image_url == 'https://example.com/original.png'
            assert len(pixelation_map) == 2
            assert pixelation_map['0_1blur.webp'] == 'https://example.com/pixelated1.webp'

def test_load_game_data(mock_game_file):
    """Test loading game data into PostgreSQL."""
    mock_conn = Mock()
    mock_cur = Mock()
    mock_cur.fetchone.return_value = (1,)
    
    # Fix mock with context manager for cursor
    mock_cm = Mock()
    mock_cm.__enter__ = Mock(return_value=mock_cur)
    mock_cm.__exit__ = Mock(return_value=None)
    mock_conn.cursor.return_value = mock_cm
    
    with patch('schedule_game.connect_to_postgres', return_value=mock_conn), \
         patch('schedule_game.load_json_data', return_value=MOCK_GAME_DATA):
        
        game_id = load_game_data(
            mock_game_file,
            'https://example.com/test.png',
            {'0_1blur.webp': 'https://example.com/pixelated.webp'},
            '2024-01-01T00:00:00Z'
        )
        
        assert game_id == 1
        mock_cur.execute.assert_called()
        mock_conn.commit.assert_called()

def test_load_similarity_data(mock_spacy_nlp):
    """Test loading similarity data into Redis with spaCy embeddings only."""
    mock_redis = Mock()
    mock_redis.pipeline.return_value = Mock()
    mock_pipeline = Mock()
    mock_redis.pipeline.return_value = mock_pipeline
    
    with patch('schedule_game.connect_to_redis', return_value=mock_redis), \
         patch('schedule_game.generate_embeddings', return_value={
                'keyword1': {'similar1': 0.8, 'similar2': 0.6},
                'keyword2': {'similar3': 0.7, 'similar4': 0.5}
            }) as mock_generate:
        
        success = load_similarity_data(['keyword1', 'keyword2'], 'test-0')
        
        assert success
        mock_generate.assert_called_once()
        mock_redis.sadd.assert_called()
        mock_pipeline.execute.assert_called()

def test_schedule_game(mock_game_file, mock_image_file):
    """Test the full game scheduling flow."""
    # Mock all dependencies
    with patch('schedule_game.process_game_image') as mock_process, \
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

def test_schedule_game_errors():
    """Test error handling in game scheduling."""
    # Test with invalid path that doesn't automatically search ../frontend/public
    with patch('schedule_game.Path.exists', return_value=False), \
         patch('schedule_game.load_json_data', return_value=None):
        
        success = schedule_game('nonexistent-absolute-path.json')
        assert not success
    
    # Test with empty game data
    with open('test.json', 'w') as f:
        json.dump({}, f)
    
    try:
        with patch('schedule_game.load_json_data', return_value={}):
            success = schedule_game('test.json')
            assert not success
    finally:
        os.unlink('test.json')