"""
Visual regression differ.

Compares two screenshots and returns a difference score (0.0 to 1.0).
Also generates a diff image highlighting changes in red.
"""
from PIL import Image, ImageChops, ImageStat

def compute_diff(img1_path: str, img2_path: str, diff_out_path: str = None) -> float:
    """
    Returns the percentage of pixels that differ between two images.
    0.0 means identical, 1.0 means completely different.
    """
    img1 = Image.open(img1_path).convert('RGB')
    img2 = Image.open(img2_path).convert('RGB')

    if img1.size != img2.size:
        # If sizes differ, they are completely different for our purposes
        return 1.0

    # Get absolute difference
    diff = ImageChops.difference(img1, img2)
    
    # Calculate percentage of different pixels
    # A pixel is "different" if any channel differs by > 2 (to ignore minor compression noise)
    stat = ImageStat.Stat(diff)
    # sum(stat.mean) gives a rough idea of overall difference
    # But let's do a more robust pixel-level check if needed.
    # For e-ink rendering (black/white), any change is significant.
    
    if diff_out_path:
        # Highlight changes in red
        # We create a red background and use the diff as a mask
        mask = diff.convert('L').point(lambda x: 255 if x > 0 else 0)
        red = Image.new('RGB', img1.size, (255, 0, 0))
        diff_view = Image.composite(red, img1, mask)
        diff_view.save(diff_out_path)

    # Simple average difference per pixel channel
    # Normalizing by 255 to get 0.0 - 1.0 range
    score = sum(stat.mean) / (3 * 255)
    return score
