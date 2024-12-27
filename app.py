import streamlit as st
import os
from io import BytesIO
import pytesseract
from PIL import Image
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from dotenv import load_dotenv
from pywin.framework.toolmenu import tools

from constant import SYSTEM_PROMPT1, INSTRUCTIONS1, INSTRUCTIONS2

load_dotenv()

MAX_IMAGE_WIDTH = 300


def resize_image_for_display(image_file):
    if isinstance(image_file, str):
        img = Image.open(image_file)
    else:
        img = Image.open(image_file)
        image_file.seek(0)
    aspect_ratio = img.height / img.width
    new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
    img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

def extract_text_from_image(image):
    img = Image.open(image)
    text = pytesseract.image_to_string(img)
    return text


@st.cache_resource
def get_ingredient_analyzer():
    return Agent(
        name="Ingredient Analyzer",
        model=OpenAIChat(id="gpt-4o"),
        system_prompt=SYSTEM_PROMPT1,
        instructions=INSTRUCTIONS1,
        tools=[DuckDuckGo()],
        show_tool_calls=False,
        markdown=True
    )


@st.cache_resource
def get_health_assessor():
    return Agent(
        name="Health Agent",
        model=OpenAIChat(id="gpt-4o"),
        system_prompt=SYSTEM_PROMPT1,
        instructions=INSTRUCTIONS2,
        tools=[DuckDuckGo()],
        show_tool_calls=False,
        markdown=True
    )


def collaborative_analysis(image):
    extracted_text = extract_text_from_image(image)
    ingredient_analyzer = get_ingredient_analyzer()
    health_assessor = get_health_assessor()

    # First phase: Ingredient Analysis
    with st.spinner('Phase 1: Analyzing ingredients composition...'):
        ingredient_prompt = f"""
        Please analyze these cosmetic ingredients and provide a detailed report following your instructions: 
        {extracted_text}

        Format your response clearly with sections for each ingredient's analysis as specified in your instructions.
        Make sure to prepare the information in a way that will be useful for the Health Agent's assessment.
        """

        ingredient_analysis = ingredient_analyzer.run(ingredient_prompt)
        st.subheader("🧪 Ingredient Analysis Report")
        st.markdown(ingredient_analysis.content, unsafe_allow_html=True)

    # Second phase: Health Assessment
    with st.spinner('Phase 2: Performing comprehensive health assessment...'):
        health_prompt = f"""
        Based on the Ingredient Analyzer's detailed report: {ingredient_analysis.content}
        
        Please do a research what is the health impact of {ingredient_analysis.content} for humans from using {tools}

        Please provide a comprehensive health assessment following your instructions.
        Make sure to include:
        1. Complete health impact analysis
        2. Research-backed validation
        3. Clear risk-benefit analysis
        4. Specific percentage indicating how good this product is for human health
        5. Final recommendations
        """

        health_assessment = health_assessor.run(health_prompt)
        st.subheader("🏥 Health Assessment Report")
        st.markdown(health_assessment.content, unsafe_allow_html=True)

    # Final collaborative summary
    with st.spinner('Phase 3: Generating final collaborative summary...'):
        summary_prompt = f"""
        Based on both analyses:
        1. Ingredient Analysis: {ingredient_analysis.content}
        2. Health Assessment: {health_assessment.content}

        Please provide a final collaborative summary that:
        1. Highlights the key findings from both analyses
        2. Emphasizes the most important safety considerations
        3. Provides clear, actionable recommendations
        4. States the final health benefit percentage
        5. Suggests alternatives if necessary

        Format this as a clear, concise final report for the user.
        """

        final_summary = ingredient_analyzer.run(summary_prompt)
        st.subheader("📋 Final Collaborative Summary")
        st.markdown(final_summary.content, unsafe_allow_html=True)


def main():
    st.title('🔍 Smart Cosmetic Analyzer')

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
            help="Upload a clear and full image of the product's ingredients"
        )
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            st.image(resized_image, caption='Uploaded Image', width=MAX_IMAGE_WIDTH)
            if st.button("🔍 Analyze", key="analyze_upload"):
                collaborative_analysis(uploaded_file)

    with tab_camera:
        captured_photo = st.camera_input('Take a picture of the ingredient section of the cosmetic product')
        if captured_photo:
            resized_image = resize_image_for_display(captured_photo)
            st.image(resized_image, caption='Captured Image', width=MAX_IMAGE_WIDTH)
            if st.button("🔍 Analyze", key="analyze_captured"):
                collaborative_analysis(captured_photo)


if __name__ == '__main__':
    st.set_page_config(
        page_title='Smart Cosmetic Analyzer',
        layout='wide',
        initial_sidebar_state='expanded',
    )
    main()