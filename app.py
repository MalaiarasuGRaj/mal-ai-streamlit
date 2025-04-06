import streamlit as st
from PIL import Image
import pytesseract
import io
import re
import logging
import fitz  # PyMuPdf
import openai
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import openai

logging.basicConfig(level=logging.INFO)

st.title("QuiZenius AI 🧠🔍")
st.markdown('<style>h1{color: orange; text-align: center; margin-bottom: 0px;}</style>', unsafe_allow_html=True)
st.subheader('Smart Learning, Enhanced by AI 📚🤖')
st.markdown('<style>h3{text-align: center; margin-top: 0;}</style>', unsafe_allow_html=True)

with st.sidebar:
    linkedin_url = "https://www.linkedin.com/in/malaiarasu-g-raj-38b695252/"
    github_url = "https://github.com/MalaiarasuGRaj"

    st.markdown(f"""
    Developed By:<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<font color='orange'>**Malaiarasu GRaj**</font><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[LinkedIn]({linkedin_url}) | [GitHub]({github_url})
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    st.header("Input your preferences")
    topic = st.text_input("Topic/Subject:", placeholder="Enter a topic...")
    familiarity = st.selectbox("Familiarity Level:", ["Select...", "Beginner", "Intermediate", "Advanced"])
    learning_mode = st.radio("Learning Mode:", ["Select...", "Lesson", "Quiz"])

    st.markdown("### Time Available (Minutes):")
    col1, col2 = st.columns([4, 1])

    if 'time_available' not in st.session_state:
        st.session_state.time_available = 30

    with col1:
        st.session_state.time_available = st.slider(
            "Time Available Slider",
            min_value=5,
            max_value=120,
            value=st.session_state.time_available,
            format="%d minutes",
            key="time_available_slider",
            label_visibility="collapsed"
        )

    with col2:
        time_available_text = st.text_input(
            "Time Available Box",
            value=str(st.session_state.time_available),
            max_chars=3,
            key="time_available_text",
            label_visibility="collapsed"
        )

        if time_available_text:
            st.session_state.time_available = int(time_available_text)

    if topic and familiarity != "Select..." and learning_mode != "Select..." and st.session_state.time_available:
        st.success("All required fields are filled!")
        uploaded_files = st.file_uploader("Upload Reference Material (Optional, PDF)", type=["pdf"],
                                          accept_multiple_files=True)
        additional_instructions = st.text_area("Additional Instructions (Optional):")
        generate_button = st.button("Generate Content")
    else:
        st.error("Please fill all the fields to proceed.")
        uploaded_files = None
        additional_instructions = None
        generate_button = None

def extract_pdf_content(pdf_files):
    combined_text = ""
    for pdf_file in pdf_files:
        try:
            doc = fitz.open(stream=pdf_file)
            text = ""
            image_text = ""

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()  

                images = page.get_images(full=True)
                for img in images:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))

                    try:
                        image_text += pytesseract.image_to_string(image) 
                    except pytesseract.TesseractNotFoundError as e:
                        logging.error(f"Tesseract not found: {e}")
                    except Exception as e:
                        logging.error(f"Error processing image: {e}")

            combined_text += text + " " + image_text
        except Exception as e:
            logging.error(f"Error extracting PDF content: {e}")
    return combined_text

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    return text.strip()

# Initialize SambaNova client
client = openai.OpenAI(
    api_key="55aa93ff-6bcb-4cd0-a0af-8d777bdd7220",
    base_url="https://api.sambanova.ai/v1",
)

def generate_content(topic, familiarity, learning_mode, time_available, uploaded_files, additional_instructions):
    if learning_mode == "Lesson":
        prompt = f"As an experienced educator, explain the reasoning behind the key concepts of '{topic}' to a {familiarity} level learner. Structure the explanation to ensure clarity within {time_available} minutes. Contextualize the content with real-world examples and guide the learner through the topic using relatable storytelling. Keep the learner motivated by highlighting practical applications. Finally, evaluate the learning process by recommending 2-3 free, high-quality online courses and suggest 1-2 projects for hands-on practice. Incorporate {additional_instructions} to further enhance the experience."

    elif learning_mode == "Quiz":
        prompt = f"As an experienced educator, assess the learner's understanding of '{topic}' with a quiz designed for a {familiarity} level learner. Include multiple-choice, true/false, and short-answer questions. Provide detailed instructions and context for each question. Evaluate the learner's progress by giving immediate feedback on correct and incorrect answers. Ensure the quiz fits within {time_available} minutes, and integrate {additional_instructions} to make the assessment more tailored and effective."

    if uploaded_files:
        prompt += f" Use the following content for reference: {uploaded_files}"

    try:
        response = client.chat.completions.create(
            model="Meta-Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": "You are an expert educational assistant specialized in creating personalized learning content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Failed to generate content: {e}")
        return None

def generate_pdf(content):
    pdf_output = io.BytesIO()
    c = canvas.Canvas(pdf_output, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)
    text_object = c.beginText(40, height - 40)
    text_object.setFont("Helvetica", 12)
    text_object.setTextOrigin(40, height - 40)

    for line in content.split('\n'):
        text_object.textLine(line)

    c.drawText(text_object)
    c.showPage()
    c.save()
    pdf_output.seek(0)
    return pdf_output

if generate_button:
    if uploaded_files:
        pdf_files = [file.getvalue() for file in uploaded_files]
        pdf_content = extract_pdf_content(pdf_files)
        cleaned_text = clean_text(pdf_content)
    else:
        cleaned_text = ""

    content = generate_content(topic, familiarity, learning_mode, st.session_state.time_available, uploaded_files,
                               additional_instructions)

    if content:
        st.session_state['content'] = content
        pdf_output = generate_pdf(content)
        st.markdown(content)
        st.sidebar.success("Content generated successfully!")
        st.sidebar.download_button("Download PDF", pdf_output, file_name="generated_content.pdf",
                                   mime="application/pdf")
    else:
        st.sidebar.error("Failed to generate content.")
