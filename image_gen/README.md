# Image Generation Application

This is a GUI application that allows the user to point at an image and use the segment anything library (https://github.com/facebookresearch/segment-anything) to interactively segment certain parts from an image for a given set of keywords.

Inputs:
- keywords: ["word_0", "word_1", "word_2", "word_3", "word_4"]
- image_dir: "random-0.webp"

Algorithm:
1. Load the image
2. For each keyword:
    i.   Prompt the user to set prompt points
    ii.  Run the SAM model to generate a segmented section
    iii. Show the segmentation visually
    iv.  Ask the user if they like it, if not got back to i.
    v.   If they like it, extract the segmented area and add to a dict of segmented areas per keyword
3. Generated both blurred and non-blurry images of each segment
4. Generate all possible combinations of blurry and non-blurry segments into images
    Examples (5 keywords should generate 25 images): 
        0blur_1_2_3_4.webp
        0_1blur_2_3_4.webp
        ...
        0blur_1blur_2blur_3blur_4blur.webp