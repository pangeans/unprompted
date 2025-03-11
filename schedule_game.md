# Schedule Game Updates

## Overview
I want to streamline the game setup and scheduling flow.
Currently:
0. Create an image using online AI generator tools -> save it in frontend/public/
1. Choose 5 keywords from the prompt that generated the image and run backend/generate_embeddings.py to generate a bunch of similarity jsons
2. Create a game config json (like random-0.json): this includes the image location, the prompt, keywords, speech types, similarity_file locations
3. Run segmenter.py with the image and keywords as inputs -> saves pixelated files in segmenter/blurry_combinations
4. Run backend/schedule_game.py and load the databases with everything

New version:
0. Create an image using online AI generator tools -> save it in frontend/public/ (no changes here)
1. Create a game config json (like random-0.json): this includes the image location, the prompt, keywords, speech types
2. Run the new schedule_game.py:
    i. Kicks off the segmenter.py script (maybe as a function or something) and generate the pixelated combinations
    ii. Run backend/generate_embedding.py to generate the similarity data (maybe as dicts and not jsons this time)
    iii. Run the original schedule game functions to load the database

## Notes
- Write clean and minimally viable code, with minimal error handling. 
- I want the code to be readable, easy to understand and easy to test (later). 
- Please consolidate or split up files and folder hierarchies as needed between the backend and segmenter folders.
- Write a markdown file that explains how to schedule the game (update existing ones)