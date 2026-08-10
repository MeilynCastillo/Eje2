import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
import json
from groq import Groq
import os

# ======================
# CONFIGURACIÓN
# ======================
st.set_page_config(
    page_title="Detección de Enfermedades en Hojas de Café",
    page_icon="🍃",
    layout="centered"
)

# Cargar modelo y clases
@st.cache_resource
def load_model():
    model = tf.keras.models.load_model("mejor_modelo.keras")
    with open("clases.json", "r") as f:
        clases = json.load(f)
    return model, clases

model, clases = load_model()

# Cliente de Groq (usa variable de entorno o pega tu API key)
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))

def obtener_recomendaciones(enfermedad, confianza):
    if not GROQ_API_KEY:
        return "No se configuró la API Key de Groq."

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
    Eres un experto agrónomo especializado en cultivos de café.
    La hoja de café ha sido diagnosticada con la siguiente enfermedad: **{enfermedad}**
    con un nivel de confianza del {confianza:.1f}%.

    Genera una respuesta clara, profesional y práctica en español con estas secciones:

    1. **Descripción de la enfermedad**: qué es y cómo afecta a la planta.
    2. **Recomendaciones técnicas de manejo preventivo**.
    3. **Buenas prácticas para el cuidado del cultivo**.
    4. **Acciones de seguimiento y monitoreo**.

    Usa un lenguaje técnico pero comprensible para agricultores.
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.4,
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error al conectar con Groq: {str(e)}"

# ======================
# INTERFAZ
# ======================
st.title("Detección de Enfermedades en Hojas de Café")
st.markdown("Sube una foto de una hoja de café y el sistema detectará posibles enfermedades usando Inteligencia Artificial.")

uploaded_file = st.file_uploader("Selecciona una imagen de hoja de café", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Mostrar imagen
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Imagen cargada", use_container_width=True)

    # Preprocesar
    img = image.resize((224, 224))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # Predicción
    prediccion = model.predict(img_array, verbose=0)
    clase_idx = np.argmax(prediccion)
    confianza = float(np.max(prediccion) * 100)
    enfermedad = clases[str(clase_idx)]

    # Resultados
    st.success(f"**Enfermedad detectada:** {enfermedad}")
    st.info(f"**Confianza:** {confianza:.2f}%")

    # Barra de progreso
    st.progress(confianza / 100)

    # Recomendaciones con Groq
    with st.spinner("Generando recomendaciones técnicas con IA..."):
        recomendaciones = obtener_recomendaciones(enfermedad, confianza)
        st.markdown("---")
        st.subheader("Recomendaciones Técnicas")
        st.markdown(recomendaciones)

else:
    st.info("Sube una imagen para comenzar el diagnóstico.")

