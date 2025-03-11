#!/usr/bin/env python3
"""
Segmenter

A utility for segmenting images based on keywords using SAM2,
and generating pixelated combinations of those segments.

Usage:
    python segmenter.py --image IMAGE_PATH --keywords KEYWORD1 KEYWORD2 ...
"""

import argparse
import os
import sys
import json
from pathlib import Path
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from PIL import Image, ImageFilter
import torch

# Check if sam2 is installed, if not guide the user to install it
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

class Segmenter:
    def __init__(self, image_path, keywords, output_dir="masked_images", combinations_dir="blurry_combinations"):
        """
        Initialize the segmenter with an image and keywords.
        
        Args:
            image_path: Path to the image file
            keywords: List of keywords for segments
            output_dir: Directory to save masks
            combinations_dir: Directory to save pixelation combinations
        """
        self.image_path = Path(image_path)
        self.keywords = keywords
        self.output_dir = Path(output_dir)
        self.combinations_dir = Path(combinations_dir)
        
        # Create output directories if they don't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.combinations_dir.mkdir(exist_ok=True, parents=True)
        
        # Load the image
        self.image = cv2.imread(str(self.image_path))
        if self.image is None:
            raise ValueError(f"Could not load image from {image_path}")
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        
        # Store dimensions of the image
        self.height, self.width = self.image.shape[:2]
        
        # Dictionary to store masks for each keyword
        self.masks = {}
        
        # Initialize SAM2 model
        print("Loading SAM2 model...")
        sam2_checkpoint = "checkpoints/sam2.1_hiera_large.pt"
        model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.sam2_model = build_sam2(model_cfg, sam2_checkpoint, device=self.device)
        self.predictor = SAM2ImagePredictor(self.sam2_model)
        self.predictor.set_image(self.image)
        
        print(f"Loaded image: {self.image_path} with keywords: {keywords}")
        print(f"Using device: {self.device}")
        
    def segment_image(self):
        """Process each keyword and create masks through user interaction."""
        for keyword in self.keywords:
            self._process_keyword(keyword)
            
        # Generate pixelated combinations
        self._generate_combinations()
        
        # Save metadata
        self._save_metadata()
    
    def _process_keyword(self, keyword):
        """Process a single keyword through user interaction."""
        print(f"\nProcessing keyword: {keyword}")
        
        # Set up the interactive plot
        plt.figure(figsize=(10, 8))
        plt.imshow(self.image)
        plt.title(f"Click on the image to mark the region for '{keyword}'. Press 'Accept' when done.")
        
        # Initialize the points and mask
        points = []
        mask = None
        
        # Function to handle mouse clicks
        def onclick(event):
            if event.xdata is not None and event.ydata is not None:
                x, y = int(event.xdata), int(event.ydata)
                points.append([x, y])
                plt.plot(x, y, 'ro', markersize=8)
                plt.draw()
                
                # Update the mask prediction
                if len(points) > 0:
                    prompt_points = np.array(points)
                    masks, _, _ = self.predictor.predict(
                        point_coords=prompt_points,
                        point_labels=np.ones(len(prompt_points)),
                        multimask_output=False
                    )
                    # Display the mask overlay
                    plt.clf()
                    plt.imshow(self.image)
                    plt.title(f"Segmentation for '{keyword}'. Press 'Accept' or 'Reset'.")
                    plt.imshow(masks[0], alpha=0.5, cmap='jet')
                    plt.plot(np.array(points)[:, 0], np.array(points)[:, 1], 'ro', markersize=8)
                    plt.draw()
                    
                    # Store the latest mask
                    nonlocal mask
                    mask = masks[0]
        
        # Connect the click event
        cid = plt.gcf().canvas.mpl_connect('button_press_event', onclick)
        
        # Add accept and reset buttons
        ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
        ax_reset = plt.axes([0.81, 0.05, 0.1, 0.075])
        
        button_accept = Button(ax_accept, 'Accept')
        button_reset = Button(ax_reset, 'Reset')
        
        accepted = [False]
        
        def on_accept(event):
            if mask is not None:
                self.masks[keyword] = mask
                accepted[0] = True
                plt.close()
        
        def on_reset(event):
            nonlocal points, mask
            points = []
            mask = None
            plt.clf()
            plt.imshow(self.image)
            plt.title(f"Click on the image to mark the region for '{keyword}'. Press 'Accept' when done.")
            plt.draw()
        
        button_accept.on_clicked(on_accept)
        button_reset.on_clicked(on_reset)
        
        plt.tight_layout()
        plt.show()
        
        if accepted[0]:
            # Save the mask
            mask_path = self.output_dir / f"{keyword}_mask.npy"
            np.save(mask_path, self.masks[keyword])
            print(f"Saved mask for '{keyword}' to {mask_path}")
        else:
            print(f"Skipped '{keyword}' - no mask was accepted")
    
    def _generate_combinations(self):
        """Generate all possible combinations of pixelated and non-pixelated masks."""
        print("\nGenerating pixelated combinations...")
        
        # Create a list of all keywords for which we have masks
        keywords_with_masks = list(self.masks.keys())
        num_masks = len(keywords_with_masks)
        
        # For each possible combination (2^num_masks)
        total_combinations = 2**num_masks
        print(f"Generating {total_combinations} combinations...")
        
        for i in range(total_combinations):
            # Convert number to binary to determine which masks to pixelate
            binary = format(i, f'0{num_masks}b')
            
            # Create a copy of the original image
            result_image = self.image.copy().astype(np.uint8)  # Ensure uint8 data type
            
            # Record which indices are blurred
            blurred_indices = []
            
            # Apply pixelation to selected masks
            for j, digit in enumerate(binary):
                if digit == '1':  # Pixelate this mask
                    keyword = keywords_with_masks[j]
                    mask = self.masks[keyword].astype(bool)  # Convert to boolean mask for indexing
                    
                    # Create PIL Image for pixelation
                    pil_image = Image.fromarray(result_image)
                    
                    # Create a copy of the image for the masked region
                    masked_region = result_image.copy()
                    
                    # Apply pixelation effect (resize down and up to pixelate)
                    pixelation_factor = 20  # Lower number = more pixelation
                    small_size = (self.width // pixelation_factor, self.height // pixelation_factor)
                    
                    # Create PIL image of masked area only
                    mask_image = Image.fromarray(np.uint8(mask * 255))  # Convert mask to uint8
                    
                    # Create a pixelated version of the entire image
                    small_img = pil_image.resize(small_size, Image.NEAREST)
                    pixelated_img = small_img.resize((self.width, self.height), Image.NEAREST)
                    
                    # Convert back to numpy arrays
                    pixelated_array = np.array(pixelated_img)
                    
                    # Apply the mask: replace pixels in result_image with pixelated pixels where mask is True
                    result_image[mask] = pixelated_array[mask]
                    
                    # Record that this index was blurred
                    blurred_indices.append(j)
            
            # Create filename based on which indices are blurred
            filename_parts = []
            for j in range(num_masks):
                if j in blurred_indices:
                    filename_parts.append(f"{j}blur")
                else:
                    filename_parts.append(f"{j}")
            
            filename = "_".join(filename_parts) + ".webp"
            output_path = self.combinations_dir / filename
            
            # Ensure result_image is the right type for PIL
            result_image = np.clip(result_image, 0, 255).astype(np.uint8)
            
            # Save the result
            try:
                Image.fromarray(result_image).save(output_path, format="WEBP", quality=90)
                print(f"Saved combination: {filename}")
            except Exception as e:
                print(f"Error saving {filename}: {e}")
                # Fallback to PNG if WEBP fails
                try:
                    fallback_path = self.combinations_dir / f"{filename.replace('.webp', '.png')}"
                    Image.fromarray(result_image).save(fallback_path, format="PNG")
                    print(f"Saved as PNG instead: {fallback_path.name}")
                except Exception as e2:
                    print(f"Failed to save image: {e2}")
    
    def _save_metadata(self):
        """Save metadata linking keywords to mask indices."""
        metadata = {}
        for i, keyword in enumerate(self.masks.keys()):
            metadata[i] = keyword
        
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved metadata to {metadata_path}")
        
        # Also save reverse mapping
        mask_keywords = {keyword: i for i, keyword in metadata.items()}
        keywords_path = self.output_dir / "keywords.json"
        with open(keywords_path, "w") as f:
            json.dump(mask_keywords, f, indent=2)
        
        print(f"Saved keyword mapping to {keywords_path}")

def process_image(image_path: str, keywords: list[str], output_dir: str = "masked_images", combinations_dir: str = "blurry_combinations") -> dict[str, str]:
    """
    Process an image with the given keywords and return a mapping of combination filenames to their paths.
    
    Args:
        image_path: Path to the image file
        keywords: List of keywords for segmentation
        output_dir: Directory to save masks
        combinations_dir: Directory to save combinations
        
    Returns:
        Dictionary mapping combination filenames to their file paths
    """
    try:
        # Initialize segmenter
        segmenter = Segmenter(image_path, keywords, output_dir, combinations_dir)
        
        # Process the image
        segmenter.segment_image()
        
        # Create a mapping of combination filenames to their paths
        combinations_path = Path(combinations_dir)
        pixelation_map = {}
        
        # Only look for .webp files that were generated
        for file_path in combinations_path.glob("*.webp"):
            pixelation_map[file_path.name] = str(file_path.absolute())
        
        return pixelation_map
        
    except Exception as e:
        print(f"Error processing image: {e}")
        return {}

def main():
    """Entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Segment images based on keywords using SAM2")
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument("--keywords", nargs="+", required=True, help="List of keywords for segmentation")
    parser.add_argument("--output-dir", default="masked_images", help="Directory to save masks")
    parser.add_argument("--combinations-dir", default="blurry_combinations", help="Directory to save pixelated combinations")
    
    args = parser.parse_args()
    
    try:
        pixelation_map = process_image(
            args.image, 
            args.keywords, 
            args.output_dir, 
            args.combinations_dir
        )
        print(f"Successfully generated {len(pixelation_map)} pixelated combinations")
        print("\nPixelation map:")
        for filename, path in pixelation_map.items():
            print(f"{filename} -> {path}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()