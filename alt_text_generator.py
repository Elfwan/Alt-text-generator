import streamlit as st
from PIL import Image
import pandas as pd
from transformers import BlipProcessor, BlipForConditionalGeneration
from deep_translator import GoogleTranslator

@st.cache_resource
def load_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    return processor, model

processor, model = load_model()

if 'alt_texts' not in st.session_state:
    st.session_state['alt_texts'] = []

st.title("Alt-Text Generator")
st.write("Ladda upp bilder, generera och redigera alt-texter. Export som CSV.")

if st.button("Rensa allt"):
    st.session_state['alt_texts'] = []
    st.experimental_rerun()

language = st.radio("Välj språk för alt-texterna:", ("Svenska", "Engelska"))
style = st.selectbox("Välj stil på dina alt-texter:", ("Beskrivande", "SEO-optimerad", "Tillgänglighetsanpassad"))
seo_keywords = st.text_input("Ange SEO-nyckelord (valfritt, separera med kommatecken)")

uploaded_files = st.file_uploader("Välj en eller flera bilder...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

def guess_media_type(desc):
    desc = desc.lower()
    if any(word in desc for word in ["drawing", "illustration", "sketch", "painting", "vector"]):
        return "illustration"
    return "foto"

if uploaded_files and st.button("Generera Alt-Texter"):
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        inputs = processor(image, return_tensors="pt", text="a detailed image of")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)

        if language == "Svenska":
            description = GoogleTranslator(source='en', target='sv').translate(description)

        media_type = guess_media_type(description)
        if language == "Svenska":
            typ = "En illustration" if media_type == "illustration" else "Ett foto"
        else:
            typ = "An illustration" if media_type == "illustration" else "A photo"

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
                alt_text = f"{typ} som föreställer: {description.lower()}."
            else:
                alt_text = f"{typ} depicting: {description.lower()}."

        st.session_state['alt_texts'].append({
            "filnamn": uploaded_file.name,
            "alt-text": alt_text
        })

if st.session_state['alt_texts']:
    st.subheader("Förhandsgranskning och redigering:")
    edited_texts = []

    for idx, entry in enumerate(st.session_state['alt_texts']):
        st.markdown(f"**{entry['filnamn']}**")
        edited_alt = st.text_area(f"Alt-text ({entry['filnamn']})", value=entry['alt-text'], key=f"alt_{idx}")
        edited_texts.append({
            "filnamn": entry['filnamn'],
            "alt-text": edited_alt
        })

    df = pd.DataFrame(edited_texts, columns=["filnamn", "alt-text"])
    csv = df.to_csv(index=False).encode('utf-8-sig')

    st.download_button(
        label="Ladda ner CSV (filnamn & alt-text)",
        data=csv,
        file_name='alt_texter.csv',
        mime='text/csv',
    )
