"""
normalize_dataset.py — Gym Membership System
Cleans up and normalizes all face images in the dataset folder.

What it does:
1. Renames all files to clean sequential numbers (0.jpg, 1.jpg, 2.jpg...)
2. Resizes all face crops to 224x224 (optimal for VGG-Face)
3. Normalizes brightness/contrast for consistent quality
4. Removes corrupt or unreadable images
5. Clears DeepFace cache so it rebuilds with clean data

Run: venv\Scripts\python.exe normalize_dataset.py
"""

import os
import cv2
import numpy as np
import shutil

DATASET_PATH = "dataset"
TARGET_SIZE = (224, 224)  # VGG-Face input size
CACHE_FILE = os.path.join(
    DATASET_PATH,
    "ds_model_vggface_detector_opencv_aligned_normalization_base_expand_0.pkl"
)


def normalize_image(img):
    """Resize and normalize a face image for optimal recognition."""
    # Resize to consistent dimensions
    img = cv2.resize(img, TARGET_SIZE, interpolation=cv2.INTER_LANCZOS4)

    # Convert to LAB color space for better contrast normalization
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    # Merge back
    lab = cv2.merge([l, a, b])
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    return img


def process_folder(folder_path, folder_name):
    """Process all images in a member's folder."""
    print(f"\n  Processing: {folder_name}")

    # Get all image files (any extension, any naming)
    files = []
    for f in os.listdir(folder_path):
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            files.append(os.path.join(folder_path, f))

    if not files:
        print(f"    ⚠ No images found, skipping")
        return 0

    print(f"    Found {len(files)} images")

    # Read all valid images
    valid_images = []
    corrupt_count = 0
    for filepath in files:
        img = cv2.imread(filepath)
        if img is None or img.size == 0:
            corrupt_count += 1
            continue
        # Skip very small images (likely noise, not faces)
        h, w = img.shape[:2]
        if h < 30 or w < 30:
            corrupt_count += 1
            continue
        valid_images.append(img)

    if corrupt_count > 0:
        print(f"    Removed {corrupt_count} corrupt/tiny images")

    if not valid_images:
        print(f"    ⚠ No valid images after filtering")
        return 0

    # Delete all old files
    for f in os.listdir(folder_path):
        filepath = os.path.join(folder_path, f)
        if os.path.isfile(filepath):
            os.remove(filepath)

    # Normalize and save with clean sequential names
    saved = 0
    for i, img in enumerate(valid_images):
        try:
            normalized = normalize_image(img)
            output_path = os.path.join(folder_path, f"{i}.jpg")
            cv2.imwrite(output_path, normalized, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved += 1
        except Exception as e:
            print(f"    ⚠ Error processing image {i}: {e}")

    print(f"    ✓ Saved {saved} normalized images (224x224, CLAHE enhanced)")
    return saved


def main():
    print("=" * 55)
    print("  DATASET NORMALIZER — Gym Membership System")
    print("=" * 55)
    print(f"\n  Dataset path: {os.path.abspath(DATASET_PATH)}")
    print(f"  Target size:  {TARGET_SIZE[0]}x{TARGET_SIZE[1]}")
    print(f"  Enhancement:  CLAHE contrast normalization")

    if not os.path.exists(DATASET_PATH):
        print("\n  ✗ Dataset folder not found!")
        return

    # Process each member folder
    total_images = 0
    folders_processed = 0

    for folder_name in sorted(os.listdir(DATASET_PATH)):
        folder_path = os.path.join(DATASET_PATH, folder_name)
        if not os.path.isdir(folder_path):
            continue
        count = process_folder(folder_path, folder_name)
        total_images += count
        folders_processed += 1

    # Clear DeepFace cache
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print(f"\n  ✓ DeepFace cache cleared")

    # Also remove any .pkl files in dataset root
    for f in os.listdir(DATASET_PATH):
        if f.endswith('.pkl'):
            os.remove(os.path.join(DATASET_PATH, f))

    print(f"\n{'=' * 55}")
    print(f"  Done! {folders_processed} members, {total_images} total images")
    print(f"  Restart the app for changes to take effect.")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()
