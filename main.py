
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import os

WIDTH = 512
HEIGHT = 168
CHANNELS = 3
# Speed of the scrolling noise.
SCROLL_SPEED = 1


def create_text_mask(font_path, text, font_size, offset):
    """Creates a 2D boolean mask from a text string."""
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)

    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Font not found at {font_path}. Please ensure the font file exists.")
        # Create a dummy font if not found, to avoid crashing.
        font = ImageFont.load_default()

    # Create a temporary image to draw the text on
    img = Image.new('L', (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(img)

    # Get text bounding box to position it correctly
    left, top, right, bottom = font.getbbox(text)

    # We use the offset directly. Pillow's draw.text uses top-left corner.
    position = (offset[0], offset[1])

    draw.text(position, text, font=font, fill=255)

    # Convert the image to a numpy array and create the boolean mask
    text_layer = np.array(img)
    mask[text_layer > 128] = True

    return mask


def generate_next_frame(previous_frame, text_mask):
    """
    Generates the next frame by shifting pixels from the previous frame.
    Text moves up, background moves down, without artifacts at the boundary.
    """
    new_frame = np.zeros((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)

    for y in range(HEIGHT):
        for x in range(WIDTH):
            is_text_pixel = text_mask[y, x]

            if is_text_pixel:
                # Text scrolls UP
                source_y = y + SCROLL_SPEED

                # If source is out of bounds OR source is not a text pixel, generate new noise.
                if source_y >= HEIGHT or not text_mask[source_y, x]:
                    new_color = 255 if random.random() < 0.5 else 0
                    new_frame[y, x, :] = new_color
                else:
                    # Otherwise, copy from the source pixel in the previous frame.
                    new_frame[y, x, :] = previous_frame[source_y, x, 0]
            else:
                # Background scrolls DOWN
                source_y = y - SCROLL_SPEED

                # If source is out of bounds OR source is a text pixel, generate new noise.
                if source_y < 0 or text_mask[source_y, x]:
                    new_color = 255 if random.random() < 0.5 else 0
                    new_frame[y, x, :] = new_color
                else:
                    # Otherwise, copy from the source pixel in the previous frame.
                    new_frame[y, x, :] = previous_frame[source_y, x, 0]

    return new_frame

def main():
    # Define video properties
    output_path = "captcha.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Codec
    fps = 30
    num_frames = 300

    # Initialize video writer
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (WIDTH, HEIGHT))

    if not video_writer.isOpened():
        print("Error: Could not open video writer.")
        return

    # --- State Initialization ---
    font_path = os.path.join("resources", "Roboto-SemiBold.ttf")
    text_mask = create_text_mask(font_path, "ZZYSS", 140, (40, 10))

    # Create the very first frame with completely random noise.
    previous_frame = np.zeros((HEIGHT, WIDTH, CHANNELS), dtype=np.uint8)
    random_noise = np.random.choice([0, 255], size=(HEIGHT, WIDTH), p=[0.5, 0.5]).astype(np.uint8)
    for i in range(CHANNELS):
        previous_frame[:, :, i] = random_noise

    # Encode the first random frame.
    video_writer.write(previous_frame)

    # --- Main Loop for Subsequent Frames ---
    # Generate all other frames based on the state of the previous one.
    for i in range(1, num_frames):
        print(f"Processing frame {i}/{num_frames}", end='\r')
        current_frame = generate_next_frame(previous_frame, text_mask)
        
        video_writer.write(current_frame)

        # Update the state for the next iteration.
        previous_frame = current_frame

    # Release the video writer
    video_writer.release()
    print(f"\nVideo generated: {output_path}")

if __name__ == "__main__":
    main()
