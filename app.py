import io
import zipfile
import openai
import streamlit as st
from PIL import Image, ImageDraw
from utils import *

# Streamlit UI setup
st.set_page_config(page_title="gpticon - AI Character Emoticons", layout="wide")

st.title("🧸 gpticon - GPT-powered Character Emoticons")
st.caption("Upload your selfie, pick a vibe, and get a 3x3 grid of action emoticons!")

image_file = st.file_uploader("📷 Upload your selfie (reference image)", type=["jpg", "jpeg", "png"])
if image_file:
    image_bytes = image_file.read()
    uploaded_image = Image.open(io.BytesIO(image_bytes))
    st.image(uploaded_image, caption="Uploaded Image Preview", width=200)


with st.sidebar:
    api_key = st.text_input("🔑 Enter your OpenAI API Key", type="password")
    style_choice = st.selectbox("🎨 Choose a style", list(DEFAULT_STYLES.keys()))

style_prompt = DEFAULT_STYLES[style_choice]

# Main button
if st.button("✨ Generate Emoticons"):
    if not api_key or not image_file:
        st.warning("Please upload a photo and enter your API key.")
    else:
        with st.spinner("🎨 Generating character emoticon grid... This may take up to 1–2 minutes. Please stay tuned!"):
            client = openai.OpenAI(api_key=api_key)
            poses = get_random_action_poses()
            prompt = create_prompt(style_prompt, poses)
            b64_image = base64.b64encode(image_bytes).decode("utf-8")

            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": f"data:image/png;base64,{b64_image}"}
                        ]
                    }
                ],
                tools=[{"type": "image_generation"}]
            )

            image_data = [output.result for output in response.output if output.type == "image_generation_call"]

            if not image_data:
                st.error("Image generation failed.")
            else:
                image_bytes = base64.b64decode(image_data[0])
                img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                cropped_images = split_by_detected_lines(img)

                left_col, right_col = st.columns([1, 1])  # 또는 [1, 1.2] 등 비율 조정 가능

                with left_col:
                    st.image(img, caption="3x3 Emoticon Grid", width=400)

                with right_col:
                    st.markdown("### Poses in this grid:")
                    for i, pose in enumerate(poses, 1):
                        st.markdown(f"**{i:02d}.** {pose}")

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zipf:
                    grid_io = io.BytesIO()
                    img.save(grid_io, format="PNG")
                    zipf.writestr("gpticon_grid.png", grid_io.getvalue())
                    for i, cimg in enumerate(cropped_images):
                        img_io = io.BytesIO()
                        cimg.save(img_io, format="PNG")
                        zipf.writestr(f"gpticon_{i + 1:02d}.png", img_io.getvalue())

                st.download_button(
                    label="📦 Download Emoticons (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="gpticon_emoticons.zip",
                    mime="application/zip",
                    key="download_button"
                )
