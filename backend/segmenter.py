#!/usr/bin/env python3
"""
Segmenter

A utility for segmenting images and videos based on keywords using SAM2,
and generating pixelated combinations of those segments.

Usage:
    python segmenter.py --image IMAGE_PATH --keywords KEYWORD1 KEYWORD2 ...
    python segmenter.py --video VIDEO_PATH --keywords KEYWORD1 KEYWORD2 ...
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

# Check if sam2 is installed
from sam2.build_sam import build_sam2, build_sam2_video_predictor
from sam2.sam2_image_predictor import SAM2ImagePredictor

def extract_frames(video_path, output_dir):
    """Extract frames from a video file.
    
    Args:
        video_path: Path to the video file
        output_dir: Directory to save the frames
        
    Returns:
        List of frame filenames
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True, parents=True)
    
    # Open the video
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file {video_path}")
    
    frame_files = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Save frame as JPEG
        frame_file = os.path.join(output_dir, f"{frame_count:05d}.jpg")
        cv2.imwrite(frame_file, frame)
        frame_files.append(os.path.basename(frame_file))
        frame_count += 1
    
    cap.release()
    return frame_files

def write_video(output_path, frames, fps=30.0):
    """Write frames to a video file, falling back to OpenCV if FFmpeg is not available.
    
    Args:
        output_path: Path to save the video file
        frames: List of frames as numpy arrays in RGB format
        fps: Frames per second for the output video
    """
    if not frames:
        return
    
    # Get dimensions from first frame
    height, width = frames[0].shape[:2]
    

    # Try different codecs
    codecs = [
        ('avc1', '.mp4'),  # H.264 codec
        ('mp4v', '.mp4'),  # fallback MP4 codec
        ('XVID', '.avi'),  # AVI format as last resort
    ]
    
    last_error = None
    for codec, ext in codecs:
        try:
            # Update extension if needed
            out_path = str(Path(output_path).with_suffix(ext))
            
            # Create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(out_path, fourcc, fps, (width, height), isColor=True)
            
            if not out.isOpened():
                continue
            
            # Write each frame
            for frame in frames:
                # Convert RGB to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                out.write(frame_bgr)
            
            out.release()
            
            # Verify the file was written and is not empty
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                print(f"Successfully saved video with {codec} codec to {out_path}")
                return
                
        except Exception as e:
            last_error = e
            continue
    
    if last_error:
        raise RuntimeError(f"Failed to write video with any supported codec: {last_error}")
    else:
        raise RuntimeError("Failed to write video with any supported codec")

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
            # Ignore clicks on the buttons
            if event.inaxes and event.inaxes.get_label() == "main":  # Only process clicks on the main plot
                if event.xdata is not None and event.ydata is not None:
                    x, y = int(event.xdata), int(event.ydata)
                    points.append([x, y])
                    
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
                        
                        # Reset the main plot label
                        plt.gca().set_label("main")
                        
                        # Create new accept/reset buttons
                        ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
                        ax_reset = plt.axes([0.81, 0.05, 0.1, 0.075])
                        
                        button_accept = Button(ax_accept, 'Accept')
                        button_reset = Button(ax_reset, 'Reset')
                        
                        button_accept.on_clicked(on_accept)
                        button_reset.on_clicked(on_reset)
                        
                        plt.draw()
                        
                        # Store the latest mask
                        nonlocal mask
                        mask = masks[0]
        
        # Set the label for the main plot area
        plt.gca().set_label("main")
        
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
            plt.gca().set_label("main")  # Reset the main plot label
            
            # Create new accept/reset buttons after reset
            ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
            ax_reset = plt.axes([0.81, 0.05, 0.1, 0.075])
            
            button_accept = Button(ax_accept, 'Accept')
            button_reset = Button(ax_reset, 'Reset')
            
            button_accept.on_clicked(on_accept)
            button_reset.on_clicked(on_reset)
            
            plt.draw()
        
        # Connect the click event
        fig = plt.gcf()
        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        
        # Add initial accept and reset buttons
        ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
        ax_reset = plt.axes([0.81, 0.05, 0.1, 0.075])
        
        button_accept = Button(ax_accept, 'Accept')
        button_reset = Button(ax_reset, 'Reset')
        
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

class VideoSegmenter:
    def __init__(self, video_path, keywords, output_dir="masked_images", combinations_dir="blurry_combinations", frames_dir="video_frames"):
        """
        Initialize the video segmenter with a video and keywords.
        
        Args:
            video_path: Path to the video file
            keywords: List of keywords for segments
            output_dir: Directory to save masks
            combinations_dir: Directory to save pixelation combinations
            frames_dir: Directory to save extracted frames
        """
        self.video_path = Path(video_path)
        self.keywords = keywords
        self.output_dir = Path(output_dir)
        self.combinations_dir = Path(combinations_dir)
        self.frames_dir = Path(frames_dir)
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.combinations_dir.mkdir(exist_ok=True, parents=True)
        self.frames_dir.mkdir(exist_ok=True, parents=True)
        
        # Extract frames from video
        print("Extracting video frames...")
        self.frame_files = extract_frames(video_path, str(self.frames_dir))
        if not self.frame_files:
            raise ValueError(f"No frames extracted from video {video_path}")
        
        # Get video dimensions from first frame
        first_frame = cv2.imread(str(self.frames_dir / self.frame_files[0]))
        self.height, self.width = first_frame.shape[:2]
        
        # Initialize SAM2 model for video
        print("Loading SAM2 model...")
        sam2_checkpoint = "checkpoints/sam2.1_hiera_large.pt"
        model_cfg = "configs/sam2.1/sam2.1_hiera_l.yaml"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint, device=self.device)
        
        # Initialize inference state
        print("Initializing video inference state...")
        self.inference_state = self.predictor.init_state(video_path=str(self.frames_dir))
        
        # Dictionary to store masks for each keyword
        self.masks = {}
        self.video_segments = {}
        
        print(f"Loaded video: {self.video_path} with {len(self.frame_files)} frames")
        print(f"Using device: {self.device}")
        
        # Get video properties
        cap = cv2.VideoCapture(str(video_path))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
    
    def segment_video(self):
        """Process each keyword and create masks through user interaction."""
        # Reset state before processing
        self.predictor.reset_state(self.inference_state)
        
        for keyword in self.keywords:
            self._process_keyword(keyword)
        
        # Generate pixelated combinations for each frame
        self._generate_combinations()
        
        # Save metadata
        self._save_metadata()
    
    def _process_keyword(self, keyword):
        """Process a single keyword through user interaction."""
        print(f"\nProcessing keyword: {keyword}")
        
        # Always start with the first frame for consistency
        frame_idx = 0
        frame_path = str(self.frames_dir / self.frame_files[frame_idx])
        frame = cv2.imread(frame_path)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Set up the interactive plot
        plt.figure(figsize=(10, 8))
        plt.imshow(frame)
        plt.title(f"Click on the frame to mark the region for '{keyword}'. Press 'Accept' when done.")
        
        points = []
        masks = None
        
        def show_existing_masks():
            """Helper function to show existing masks from previously processed keywords"""
            # Use a different colormap for existing masks to distinguish them
            for idx, (existing_kw, segments) in enumerate(self.video_segments.items()):
                if frame_idx in segments:
                    obj_id = list(self.masks.keys()).index(existing_kw) + 1
                    if obj_id in segments[frame_idx]:
                        # Use a different alpha and color for existing masks
                        cmap = plt.get_cmap("Set3")
                        color = np.array([*cmap(idx)[:3], 0.3])  # Lower alpha
                        
                        h, w = frame.shape[:2]
                        mask = segments[frame_idx][obj_id]
                        # Apply the mask as a colored overlay
                        mask_img = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
                        plt.imshow(mask_img)
                        
                        # Add a legend to show which mask is which
                        plt.text(10, 20 + (idx * 20), f"Existing: {existing_kw}", 
                                 color=cmap(idx)[:3], fontsize=9, 
                                 bbox=dict(facecolor='white', alpha=0.7))
        
        # Show existing masks initially
        show_existing_masks()
        
        # Function to handle mouse clicks
        def onclick(event):
            if event.xdata is not None and event.ydata is not None:
                x, y = int(event.xdata), int(event.ydata)
                points.append([x, y])
                plt.plot(x, y, 'ro', markersize=8)
                plt.draw()
                
                if len(points) > 0:
                    # Convert points to numpy array
                    prompt_points = np.array(points, dtype=np.float32)
                    prompt_labels = np.ones(len(points), dtype=np.int32)
                    
                    # Get object ID based on keyword index
                    obj_id = len(self.masks) + 1
                    
                    # Add points and get prediction
                    _, obj_ids, mask_logits = self.predictor.add_new_points_or_box(
                        inference_state=self.inference_state,
                        frame_idx=frame_idx,
                        obj_id=obj_id,
                        points=prompt_points,
                        labels=prompt_labels
                    )
                    
                    # Get binary mask and squeeze extra dimensions
                    binary_mask = (mask_logits[0] > 0.0).cpu().numpy()
                    binary_mask = np.squeeze(binary_mask)  # Remove singleton dimensions
                    
                    # Display the mask overlay - clear first to avoid overlay issues
                    plt.clf()
                    plt.imshow(frame)
                    plt.title(f"Segmentation for '{keyword}'. Press 'Accept' or 'Reset'.")
                    
                    # Show existing masks first
                    show_existing_masks()
                    
                    # Show current mask with a distinct color
                    plt.imshow(binary_mask, alpha=0.6, cmap='jet')
                    plt.plot(np.array(points)[:, 0], np.array(points)[:, 1], 'ro', markersize=8)
                    
                    # Add a legend for current mask
                    plt.text(10, frame.shape[0] - 20, f"Current: {keyword}", 
                             color='yellow', fontsize=10, 
                             bbox=dict(facecolor='black', alpha=0.7))
                    
                    plt.draw()
                    
                    # Store the latest mask
                    nonlocal masks
                    masks = mask_logits
        
        # Connect the click event
        cid = plt.gcf().canvas.mpl_connect('button_press_event', onclick)
        
        # Add accept and reset buttons
        ax_accept = plt.axes([0.7, 0.05, 0.1, 0.075])
        ax_reset = plt.axes([0.81, 0.05, 0.1, 0.075])
        
        button_accept = Button(ax_accept, 'Accept')
        button_reset = Button(ax_reset, 'Reset')
        
        accepted = [False]
        
        def on_accept(event):
            if masks is not None:
                # Store reference mask - make sure to squeeze extra dimensions
                self.masks[keyword] = np.squeeze((masks[0] > 0.0).cpu().numpy())
                accepted[0] = True
                plt.close()
        
        def on_reset(event):
            nonlocal points, masks
            points = []
            masks = None
            plt.clf()
            plt.imshow(frame)
            plt.title(f"Click on the frame to mark the region for '{keyword}'. Press 'Accept' when done.")
            # Show existing masks again
            show_existing_masks()
            plt.draw()
        
        button_accept.on_clicked(on_accept)
        button_reset.on_clicked(on_reset)
        
        plt.tight_layout()
        plt.show()
        
        if accepted[0]:
            print("Propagating masks through video...")
            # Propagate masks through video
            video_segments = {}
            for out_frame_idx, out_obj_ids, out_mask_logits in self.predictor.propagate_in_video(self.inference_state):
                video_segments[out_frame_idx] = {
                    out_obj_id: np.squeeze((out_mask_logits[i] > 0.0).cpu().numpy())  # Squeeze extra dimensions
                    for i, out_obj_id in enumerate(out_obj_ids)
                }
            
            # Store video segments for this keyword
            self.video_segments[keyword] = video_segments
            print(f"Processed '{keyword}' for all frames")
        else:
            print(f"Skipped '{keyword}' - no mask was accepted")

    def _generate_combinations(self):
        """Generate all possible combinations of pixelated and non-pixelated masks and save as videos."""
        print("\nGenerating pixelated combinations...")
        
        # Create a list of all keywords for which we have masks
        keywords_with_masks = list(self.masks.keys())
        num_masks = len(keywords_with_masks)
        
        # For each possible combination (2^num_masks)
        total_combinations = 2**num_masks
        print(f"Generating {total_combinations} video combinations...")
        
        # Dictionary to store frames for each combination
        combination_frames = {}
        
        # Process each frame
        for frame_idx, frame_file in enumerate(self.frame_files):
            # Load the frame
            frame_path = str(self.frames_dir / frame_file)
            frame = cv2.imread(frame_path)
            if frame is None:
                print(f"Warning: Could not read frame {frame_path}")
                continue
                
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Generate all combinations for this frame
            for i in range(total_combinations):
                # Convert number to binary to determine which masks to pixelate
                binary = format(i, f'0{num_masks}b')
                
                # Create a copy of the frame
                result_image = frame.copy()
                
                # Record which indices are blurred
                blurred_indices = []
                
                # Apply pixelation to selected masks
                for j, digit in enumerate(binary):
                    if digit == '1':  # Pixelate this mask
                        keyword = keywords_with_masks[j]
                        # Get mask for current frame
                        obj_id = j + 1  # Object IDs start from 1
                        if frame_idx not in self.video_segments[keyword]:
                            print(f"Warning: No mask for frame {frame_idx} in keyword '{keyword}'")
                            continue
                        if obj_id not in self.video_segments[keyword][frame_idx]:
                            print(f"Warning: No object {obj_id} in frame {frame_idx} for keyword '{keyword}'")
                            continue
                            
                        mask = self.video_segments[keyword][frame_idx][obj_id]
                        
                        # Create PIL Image for pixelation
                        pil_image = Image.fromarray(result_image)
                        
                        # Apply pixelation effect
                        pixelation_factor = 20
                        small_size = (self.width // pixelation_factor, self.height // pixelation_factor)
                        
                        # Create a pixelated version of the entire image
                        small_img = pil_image.resize(small_size, Image.NEAREST)
                        pixelated_img = small_img.resize((self.width, self.height), Image.NEAREST)
                        
                        # Apply the mask
                        result_image[mask] = np.array(pixelated_img)[mask]
                        
                        # Record that this index was blurred
                        blurred_indices.append(j)
                
                # Create combination key based on which indices are blurred
                key_parts = []
                for j in range(num_masks):
                    if j in blurred_indices:
                        key_parts.append(f"{j}blur")
                    else:
                        key_parts.append(f"{j}")
                combination_key = "_".join(key_parts)
                
                # Initialize list for this combination if needed
                if combination_key not in combination_frames:
                    combination_frames[combination_key] = []
                
                # Ensure frame is uint8 and clip values
                result_image = np.clip(result_image, 0, 255).astype(np.uint8)
                combination_frames[combination_key].append(result_image)
            
            if frame_idx % 10 == 0:  # Progress update every 10 frames
                print(f"Processed combinations for frame {frame_idx}/{len(self.frame_files)}")
        
        # Save each combination as a video
        print("\nSaving video combinations...")
        for combination_key, frames in combination_frames.items():
            if not frames:
                print(f"Warning: No frames to save for combination {combination_key}")
                continue
                
            video_path = self.combinations_dir / f"{combination_key}.mp4"
            print(f"Saving {video_path}...")
            try:
                write_video(video_path, frames, fps=self.fps)
            except Exception as e:
                print(f"Error saving video {combination_key}: {e}")
        
        print("Finished generating video combinations")
    
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

def process_video(video_path: str, keywords: list[str], output_dir: str = "masked_images", 
                 combinations_dir: str = "blurry_combinations", frames_dir: str = "video_frames") -> dict[str, str]:
    """
    Process a video with the given keywords and return a mapping of combination filenames to their paths.
    
    Args:
        video_path: Path to the video file
        keywords: List of keywords for segmentation
        output_dir: Directory to save masks
        combinations_dir: Directory to save combinations
        frames_dir: Directory to save extracted frames
        
    Returns:
        Dictionary mapping combination filenames to their file paths
    """
    try:
        # Initialize video segmenter
        segmenter = VideoSegmenter(video_path, keywords, output_dir, combinations_dir, frames_dir)
        
        # Process the video
        segmenter.segment_video()
        
        # Create a mapping of combination filenames to their paths
        combinations_path = Path(combinations_dir)
        pixelation_map = {}
        
        # Look for all generated MP4 files
        for file_path in combinations_path.glob("*.mp4"):
            pixelation_map[file_path.name] = str(file_path.absolute())
        
        return pixelation_map
        
    except Exception as e:
        print(f"Error processing video: {e}")
        return {}

def main():
    """Entry point for command line usage."""
    parser = argparse.ArgumentParser(description="Segment images and videos based on keywords using SAM2")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", help="Path to the input image")
    input_group.add_argument("--video", help="Path to the input video")
    parser.add_argument("--keywords", nargs="+", required=True, help="List of keywords for segmentation")
    parser.add_argument("--output-dir", default="masked_images", help="Directory to save masks")
    parser.add_argument("--combinations-dir", default="blurry_combinations", help="Directory to save pixelated combinations")
    parser.add_argument("--frames-dir", default="video_frames", help="Directory to save extracted video frames")
    
    args = parser.parse_args()
    
    try:
        if args.image:
            pixelation_map = process_image(
                args.image, 
                args.keywords, 
                args.output_dir, 
                args.combinations_dir
            )
            print(f"Successfully generated {len(pixelation_map)} pixelated combinations")
        else:  # args.video
            pixelation_map = process_video(
                args.video,
                args.keywords,
                args.output_dir,
                args.combinations_dir,
                args.frames_dir
            )
            print(f"Successfully generated {len(pixelation_map)} pixelated frame combinations")
            
        print("\nPixelation map:")
        for filename, path in pixelation_map.items():
            print(f"{filename} -> {path}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()