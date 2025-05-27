import base64
import random
import numpy as np
from PIL import Image, ImageDraw
from typing import List
from settings import EMOTICON_POSES, IMAGE_GENERATE_PROMPT


def create_prompt(style_prompt: str, poses: List[str]) -> str:
    pose_text = ", ".join(poses)
    return IMAGE_GENERATE_PROMPT.format(
        pose_text=pose_text,
        style_prompt=style_prompt
    )


# Crop using dynamically detected split lines
def detect_cut_lines_by_variance(image: Image.Image, axis=0, brightness_thresh=0.93, var_thresh=0.002, min_block_size=10, num_cuts=2) -> List[int]:
    img_gray = image.convert("L")
    img_np = np.array(img_gray)

    if axis == 0:
        values = img_np.mean(axis=1) / 255.0
        variances = img_np.var(axis=1) / (255.0**2)
    else:
        values = img_np.mean(axis=0) / 255.0
        variances = img_np.var(axis=0) / (255.0**2)

    white_mask = (values > brightness_thresh) & (variances < var_thresh)
    white_blocks = []
    start = None
    for i, is_white in enumerate(white_mask):
        if is_white and start is None:
            start = i
        elif not is_white and start is not None:
            if i - start >= min_block_size:
                white_blocks.append((start, i))
            start = None
    if start is not None and len(white_mask) - start >= min_block_size:
        white_blocks.append((start, len(white_mask)))

    white_blocks.sort(key=lambda x: x[1] - x[0], reverse=True)
    centers = [((s + e) // 2) for s, e in white_blocks[:num_cuts]]
    return sorted(centers)


def split_by_detected_lines(img: Image.Image) -> List[Image.Image]:
    x_lines = detect_cut_lines_by_variance(img, axis=1, num_cuts=2)
    y_lines = detect_cut_lines_by_variance(img, axis=0, num_cuts=2)

    if len(x_lines) < 2:
        x_lines = [img.width // 3, 2 * img.width // 3]
    if len(y_lines) < 2:
        y_lines = [img.height // 3, 2 * img.height // 3]

    coords_x = [0] + x_lines + [img.width]
    coords_y = [0] + y_lines + [img.height]

    # debug_img = img.copy()
    # draw = ImageDraw.Draw(debug_img)
    # for x in x_lines:
    #     draw.line([(x, 0), (x, img.height)], fill="red", width=2)
    # for y in y_lines:
    #     draw.line([(0, y), (img.width, y)], fill="blue", width=2)
    # st.image(debug_img, caption="Detected Grid Lines (Red: vertical, Blue: horizontal)")

    cropped_images = []
    for i in range(3):
        for j in range(3):
            x1, x2 = coords_x[j], coords_x[j + 1]
            y1, y2 = coords_y[i], coords_y[i + 1]
            crop = img.crop((x1, y1, x2, y2))
            crop = pad_to_square(crop, size=max(x2 - x1, y2 - y1))
            cropped_images.append(crop)
    return cropped_images


def pad_to_square(im: Image.Image, size: int = 256) -> Image.Image:
    new_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    im_w, im_h = im.size
    offset = ((size - im_w) // 2, (size - im_h) // 2)
    new_im.paste(im, offset)
    return new_im


# Encode image as base64
def encode_image_to_base64(file) -> str:
    return base64.b64encode(file.read()).decode("utf-8")


def get_random_action_poses(n: int = 9) -> List[str]:
    return random.sample(EMOTICON_POSES, n)
