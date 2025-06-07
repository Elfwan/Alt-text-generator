import streamlit as st

# alt_text_generator_v6.py

import streamlit as st
from PIL import Image
import pandas as pd
import io
from transformers import BlipProcessor, BlipForConditionalGeneration
from googletrans import Translator
import language_tool_python

# Ladda modellen
@st.cache_resource
def load_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

processor, model = load_model()

# Spara data i session_state
if 'alt_texts' not in st.session_state:
    st.session_state['alt_texts'] = []

# Sidhuvud
st.title("Alt-Text Generator - Komplett Version")
st.write("Ladda upp bilder, generera, redigera, rätta och skapa SEO-metabeskrivningar!")

# Välj språk
language = st.radio(
    "Välj språk för alt-texterna:",
    ("Svenska", "Engelska")
)

# Stilval
style = st.selectbox(
    "Välj stil på dina alt-texter:",
    ("Beskrivande", "SEO-optimerad", "Tillgänglighetsanpassad")
)

# Anpassade SEO-nyckelord
seo_keywords = st.text_input("Ange SEO-nyckelord (valfritt, separera med kommatecken)")

# Ladda upp bilder
uploaded_files = st.file_uploader(
    "Välj en eller flera bilder...",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# Starta översättare och språkverktyg
translator = Translator()
tool = language_tool_python.LanguageTool('sv' if language == "Svenska" else 'en-US')

# Funktion för att skapa metabeskrivning
def generate_meta(description):
    if language == "Svenska":
        return f"Upptäck en bild som visar {description.lower()}. Perfekt för SEO och digital marknadsföring."
    else:
        return f"Discover an image depicting {description.lower()}. Perfect for SEO and digital marketing."

# Generera alt-texter
if uploaded_files and st.button("Generera Alt-Texter"):
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)

        # Översättning om svenska är valt
        if language == "Svenska":
            description = translator.translate(description, src='en', dest='sv').text

        # Skapa alt-text
        if style == "Beskrivande":
            alt_text = f"{description.capitalize()}."
        elif style == "SEO-optimerad":
            keywords = seo_keywords.split(",") if seo_keywords else []
            keywords_text = ", ".join([kw.strip() for kw in keywords])
            alt_text = f"Bild som visar {description.lower()}."
            if keywords_text:
                alt_text += f" Nyckelord: {keywords_text}."
        elif style == "Tillgänglighetsanpassad":
            if language == "Svenska":
                alt_text = f"En illustration eller ett foto som föreställer: {description.lower()}."
            else:
                alt_text = f"An illustration or a photo depicting: {description.lower()}."

        # Rättstavning
        corrected_text = tool.correct(alt_text)

        # Metabeskrivning om SEO-stil är vald
        meta_desc = generate_meta(description) if style == "SEO-optimerad" else ""

        st.session_state['alt_texts'].append({
            "filnamn": uploaded_file.name,
            "alt-text": corrected_text,
            "metabeskrivning": meta_desc
        })

# Redigera och live-rätta
if st.session_state['alt_texts']:
    st.subheader("Förhandsgranskning och live-rättning:")

    edited_texts = []
    for idx, entry in enumerate(st.session_state['alt_texts']):
        st.markdown(f"**{entry['filnamn']}**")

        edited_alt = st.text_area(f"Alt-text ({entry['filnamn']})", value=entry['alt-text'], key=f"alt_{idx}")
        corrected_live = tool.correct(edited_alt)
        st.text_area(f"Rättad version ({entry['filnamn']})", value=corrected_live, height=100, key=f"corr_{idx}")

        # Visa och redigera även metabeskrivning
        if entry['metabeskrivning']:
            meta_input = st.text_area(f"Metabeskrivning ({entry['filnamn']})", value=entry['metabeskrivning'], key=f"meta_{idx}")
        else:
            meta_input = ""

        edited_texts.append({
            "filnamn": entry['filnamn'],
            "alt-text": corrected_live,
            "metabeskrivning": meta_input
        })

    # Skapa CSV
    df = pd.DataFrame(edited_texts)
    csv = df.to_csv(index=False).encode('utf-8')

    # Ladda ner
    st.download_button(
        label="Ladda ner alla alt-texter och metabeskrivningar som CSV",
        data=csv,
        file_name='alt_texter_redigerade.csv',
        mime='text/csv',
    )
