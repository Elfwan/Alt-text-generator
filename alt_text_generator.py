import streamlit as st
from PIL import Image
import pandas as pd
from transformers import BlipProcessor, BlipForConditionalGeneration
from deep_translator import GoogleTranslator

# Ladda modellen
@st.cache_resource
def load_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    return processor, model

processor, model = load_model()

# Initiera session_state
if 'alt_texts' not in st.session_state:
    st.session_state['alt_texts'] = []

# Sidhuvud
st.title("Alt-Text Generator")
st.write("Ladda upp bilder, generera och redigera alt-texter. Export sker som CSV med filnamn och alt-text.")

# Välj språk
language = st.radio("Välj språk för alt-texterna:", ("Svenska", "Engelska"))

# Stilval
style = st.selectbox("Välj stil på dina alt-texter:", ("Beskrivande", "SEO-optimerad", "Tillgänglighetsanpassad"))

# SEO-nyckelord (frivilligt)
seo_keywords = st.text_input("Ange SEO-nyckelord (valfritt, separera med kommatecken)")

# Ladda upp bilder
uploaded_files = st.file_uploader("Välj en eller flera bilder...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Generera alt-texter
if uploaded_files and st.button("Generera Alt-Texter"):
    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)

        # Översättning om svenska är valt
        if language == "Svenska":
            description = GoogleTranslator(source='en', target='sv').translate(description)

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

        # Spara alt-text
        st.session_state['alt_texts'].append({
            "filnamn": uploaded_file.name,
            "alt-text": alt_text
        })

# Redigering och nedladdning
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

    # Skapa CSV med rätt teckenkodning
    df = pd.DataFrame(edited_texts)
    csv = df.to_csv(index=False).encode('utf-8-sig')

    # Nedladdningsknapp
    st.download_button(
        label="Ladda ner CSV (filnamn & alt-text)",
        data=csv,
        file_name='alt_texter.csv',
        mime='text/csv',
    )
