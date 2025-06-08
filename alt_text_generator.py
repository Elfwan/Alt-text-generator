import streamlit as st
from PIL import Image
import pandas as pd
from transformers import BlipProcessor, BlipForConditionalGeneration
from deep_translator import GoogleTranslator
from collections import Counter
import re

# Ladda modell
@st.cache_resource
def load_model():
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
    return processor, model

processor, model = load_model()

# Initiera session state
if 'alt_texts' not in st.session_state:
    st.session_state['alt_texts'] = []

# Rubrik
st.title("Alt-Text Generator med Lärande")
st.write("Ladda upp bilder, generera och redigera alt-texter. Tidigare redigeringar används för att förbättra framtida texter.")

# Rensa-knapp
if st.button("Rensa allt"):
    st.session_state['alt_texts'] = []
    st.session_state['clear_uploader'] = True
    st.success("Formuläret har rensats.")
else:
    st.session_state['clear_uploader'] = False

# Val
language = st.radio("Välj språk för alt-texterna:", ("Svenska", "Engelska"))
style = st.selectbox("Välj stil på alt-texterna:", ("Beskrivande", "SEO-optimerad", "Tillgänglighetsanpassad"))
seo_keywords = st.text_input("Ange SEO-nyckelord (valfritt, separera med kommatecken)")

# Upload
uploaded_files = st.file_uploader(
    "Välj bilder...", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True,
    key=None if not st.session_state.get('clear_uploader') else "new_upload"
)

# Ladda minne
def load_memory():
    try:
        return pd.read_csv("alt_memory.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["original", "edited"])

# Spara minne
def update_memory(edited_texts, original_descriptions):
    path = "alt_memory.csv"
    new_data = pd.DataFrame({
        "original": original_descriptions,
        "edited": [entry["alt-text"] for entry in edited_texts]
    })
    try:
        existing = pd.read_csv(path)
        combined = pd.concat([existing, new_data]).drop_duplicates(subset="original", keep="last")
    except FileNotFoundError:
        combined = new_data
    combined.to_csv(path, index=False, encoding='utf-8-sig')

# Extrahera regler från tidigare redigeringar
def extract_common_additions(df):
    additions = Counter()
    for _, row in df.iterrows():
        orig_words = set(re.findall(r"\w+", row["original"].lower()))
        edit_words = set(re.findall(r"\w+", row["edited"].lower()))
        added = edit_words - orig_words
        for word in added:
            if len(word) > 2:
                additions[word] += 1
    return [w for w, c in additions.items() if c >= 2]

# Applicera regler
def apply_learned_additions(description, additions):
    for word in additions:
        if word not in description.lower():
            description += f" {word}"
    return description.strip()

# Typ
def guess_media_type(desc):
    desc = desc.lower()
    if any(w in desc for w in ["drawing", "illustration", "sketch", "painting", "vector"]):
        return "illustration"
    return "foto"

# Generering
if uploaded_files and st.button("Generera Alt-Texter"):
    memory_df = load_memory()
    learned_additions = extract_common_additions(memory_df)

    if learned_additions:
        st.info(f"Tillämpade inlärda tillägg: {', '.join(learned_additions)}")

    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file)
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)

        if language == "Svenska":
            description = GoogleTranslator(source='en', target='sv').translate(description)

        description = description.replace("en detaljerad bild av ", "").replace("a detailed image of ", "").strip()

        # Kontrollera exakta redigeringar först
        existing_edit = memory_df[memory_df["original"] == description]
        if not existing_edit.empty:
            description = existing_edit.iloc[0]["edited"]
        else:
            description = apply_learned_additions(description, learned_additions)

        media_type = guess_media_type(description)
        typ_sv = "En illustration" if media_type == "illustration" else "Ett foto"
        typ_en = "An illustration" if media_type == "illustration" else "A photo"

        # Stil
        if style == "Beskrivande":
            alt_text = f"{description.capitalize()}."
        elif style == "SEO-optimerad":
            keywords = seo_keywords.split(",") if seo_keywor
