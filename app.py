import streamlit as st
import os
from io import BytesIO
import pytesseract
from PIL import Image
from appdirs import system
from dask_expr.diagnostics import analyze
from fontTools.ttLib.tables.ttProgram import instructions
from markdown import markdown
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
from streamlit import image

from constant import SYSTEM_PROMPT1, INSTRUCTIONS1, INSTRUCTIONS2

load_dotenv()

MAX_IMAGE_WIDTH = 300

def resize_image_for_display(image_file):
    if isinstance(image_file, str):
        img = Image.open(image_file)
    else:
        img = Image.open(image_file)
        image_file.seek(0)  # Corrected this line to reset the file pointer.
    aspect_ratio = img.height / img.width
    new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
    img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()




@st.cache_resource
def get_agent_1():
    return Agent(
        name = "Ingredient Analyzer",
        model = OpenAIChat(id = "gpt-4o"),
        system_prompt=SYSTEM_PROMPT1,
        instructions=INSTRUCTIONS1,
        tools = [DuckDuckGo()],
        show_tool_calls = False,
        markdown = True
    )

def get_agent_2():
    return Agent(
        name = "Health Agent",
        model = OpenAIChat(id = "gpt-4o"),
        system_prompt=SYSTEM_PROMPT1,
        instructions=INSTRUCTIONS2,
        tools = [DuckDuckGo()],
        show_tool_calls = False,
        markdown = True
    )

def extract_text_from_image(image):
    # Perform OCR on the uploaded image to extract text (ingredients)
    img = Image.open(image)
    text = pytesseract.image_to_string(img)
    return text


def analyze_image(image):
    extracted_text = extract_text_from_image(image)
    agent_1 = get_agent_1()
    agent_2 = get_agent_2()

    # Analyze with the first agent
    with st.spinner('Analyzing the ingredients with Agent 1 - Ingredient Analyzer ...'):
        response_1 = agent_1.run(
            "Analyze the following ingredients: " + extracted_text,
            images=None  # Not needed since we are passing extracted text
        )
        st.markdown(response_1.content, unsafe_allow_html=True)

    # Analyze with the second agent
    with st.spinner('Analyzing ingredients with Agent 2 - Health Agent ...'):
        response_2 = agent_2.run(
            "Analyze the following ingredients: " + extracted_text,
            images=None  # Not needed
        )
        st.markdown(response_2.content, unsafe_allow_html=True)


def main():
    st.title('🔍 Cosmetic Analyzer')

    if 'selected_example' in st.session_state:
        st.session_state.selected_example = None
    if "analyze_clicked" not in st.session_state:
        st.session_state.analyze_clicked = False

    tab_upload, tab_camera = st.tabs([
        "📤 Upload Image",
        "📸 Take Photo"
    ])

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload an image of the ingredient section of the cosmetic product.",
            type=['png', 'jpg', 'jpeg', 'gif'],
            help = "Upload a clear and full image of the product's ingredients"
        )
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            st.image(resized_image, caption='Uploaded Image', width=MAX_IMAGE_WIDTH)
            if st.button("🔍 Analyze", key="analyze_upload"):
                analyze_image(uploaded_file)

    with tab_camera:
        captured_photo = st.camera_input('Take a picture of the ingredient section of the cosmetic product')
        if captured_photo:
            resized_image = resize_image_for_display(captured_photo)
            st.image(resized_image, caption='Uploaded Image', width=MAX_IMAGE_WIDTH)
            if st.button("🔍 Analyze", key="analyze_captured"):
                analyze_image(captured_photo)


if __name__ == '__main__':
    st.set_page_config(
        page_title='Cosmetic Analyzer',
        layout='wide',
        initial_sidebar_state='expanded',
    )
    main()