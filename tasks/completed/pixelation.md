# Pixelation Mechanic Implementation

## Overview
For a given game, each image should have a set of subimages with a combination of pixelated and unpixelated segmented masks. \
Each segmented mask should be linked to a keyword. This link should be established before we schedule games in a basic application (see segmenter, described below). \
Once we have a group of masks and keywords, segmenter generates all possible combinations of pixelated and unpixelated masks. \
backend/schedule_game.py should now upload all combinations to the blob storage, and add a column to the Neon DB with a list of all possible image_urls along with a key they can be looked up by.
The frontend app should now start with the image with all masks pixelated, then update according to the correct guesses.
At the end of the game, reveal to unpixelated image.

## segmenter.py
Unique libraries: sam2 (https://github.com/facebookresearch/sam2) used for segmenting images based on prompts.
### Algorithm (input: image, keywords)
1. Display the image
2. For each keyword:
    i. Ask user to add point to image
    ii. Run segmentation
    iii. Prompt user to accept the mask
    iv. If accepted go to v, else got to i. (give user the option to reset)
    v. Save mask for the keyword
3. Generate all possible combinations of the image where the masks are either pixelated or not (save as image_0_1p_2_3_4.webp, etc...)

## backend
Update schedule_game.py to upload the new combinations:
- Add them to the vercel_blob storage
- Generate the SQL command to add a column with JSON data {"image_0_1p_2_3_4.webp": image_url }
- Update the load_database function with the JSON pixelated image data

## frontend
Update the frontend application to start with the pixelated image (image_0p_1p_2p_3p_4p.webp) and update it when you guess a keyword.