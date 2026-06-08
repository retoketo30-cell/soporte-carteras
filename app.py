import streamlit as st
from google import genai
from google.genai import types
import pypdf
import os

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Soporte Pack Ebooks Carteras", page_icon="👜", layout="centered")

st.title("👜 Soporte Experto - Pack de Ebooks")
st.subheader("¡Hola! Te doy una mano con cualquier duda de tus libros.")

# 2. CONFIGURACIÓN SEGURA DE LA API KEY
# Verificamos si la app corre en Streamlit Cloud o de forma local
if "GEMINI_API_KEY" in st.secrets:
    # Entorno de producción (Streamlit Cloud Secrets)
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
else:
    # Entorno local (Su computadora). Pegue su clave aquí si prueba localmente:
    os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6JdXgmexu3sQz_Pco894eh144kSvXEv3uzSMkT7HuIRWQ"

# Inicialización del cliente oficial sin pasar parámetros (toma la variable de entorno automáticamente)
try:
    client = genai.Client()
except Exception as e:
    st.error(f"Error al inicializar el cliente de Gemini: {e}")
    st.stop()

# 3. FUNCIÓN PARA LEER TODOS LOS PDFS DE LA CARPETA
@st.cache_resource
def cargar_contexto_libros():
    texto_completo = ""
    # Recorremos la carpeta buscando archivos .pdf
    archivos = [f for f in os.listdir(".") if f.endswith(".pdf")]
    
    if not archivos:
        return None
        
    for archivo in archivos:
        try:
            reader = pypdf.PdfReader(archivo)
            for page in reader.pages:
                texto_completo += page.extract_text() + "\n"
        except Exception as e:
            st.warning(f"No se pudo leer el archivo {archivo}: {e}")
            
    return texto_completo

# Cargamos el contenido de los libros en memoria
contexto_ebooks = cargar_contexto_libros()

if not contexto_ebooks:
    st.info("💡 Asegúrate de poner tus archivos PDF dentro de la misma carpeta del proyecto.")
    st.stop()

# 4. HISTORIAL DE CHAT EN MEMORIA DE STREAMLIT
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar los mensajes anteriores en la pantalla
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. INTERACCIÓN DEL USUARIO
if prompt := st.chat_input("¿Qué duda tenés sobre las carteras o los libros?"):
    # Mostramos el mensaje del cliente
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Preparar las instrucciones estrictas del sistema (System Prompt)
    instrucciones_sistema = """
    Eres una asistente virtual experta en diseño, confección y asesoramiento de carteras en malla de plástico. Tu único objetivo es guiar a las usuarias que compraron nuestro pack de ebooks.
    
    REGLAS DE ORO:
    1. Hablá siempre en español argentino rioplatense (forma natural y muy amigable).
    2. Respondé basándote estrictamente en el material provisto en el contexto. Tienes el contenido completo de los libros disponibles.
    3. ¡PROHIBIDO INVENTAR! Si la respuesta o el tema no se menciona en los libros provistos, debés decir textualmente: "Eso exacto no lo encontré en los ebooks. ¿Me lo consultás de otra forma o sobre otro tema de los libros?". No utilices conocimiento externo a menos que se relacione directamente con lo que dice el libro.
    """

    # Generamos la respuesta de la IA llamando a Gemini 2.5 Flash de forma oficial
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Pensando... 👜")
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    f"CONTEXTO DE LOS EBOOKS:\n{contexto_ebooks}\n\nPREGUNTA DE LA USUARIA:\n{prompt}"
                ],
                config=types.GenerateContentConfig(
                    system_instruction=instrucciones_sistema,
                    temperature=0.3, # Temperatura baja para que sea más exacto y no invente
                )
            )
            respuesta_ia = response.text
            message_placeholder.markdown(respuesta_ia)
            st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
            
        except Exception as e:
            st.error(f"Hubo un error con la API de Gemini: {e}")