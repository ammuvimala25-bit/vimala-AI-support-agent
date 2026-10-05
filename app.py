import streamlit as st
from product_agent import get_product_info
from web_loader import load_website_content

st.set_page_config(page_title="Vimala AI Support Agent", page_icon="🌸", layout="wide")

# Simple clean design - No background image needed
st.markdown("""
<style>
    .stApp {
        background-color: #FFF0F5;
    }
    h1 {
        color: #FF1493;
        text-align: center;
    }
    .stButton>button {
        background-color: #FF69B4;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌸 Vimala AI Support Agent 🌸")
st.markdown("<h3 style='text-align: center; color: #FF69B4;'>Vanakkam! Ungal kelvigalai kekkalam ma!</h3>", unsafe_allow_html=True)

st.write("---")

website_url = st.text_input("🌐 Website URL kodunga ma:", placeholder="https://example.com")

if st.button("📥 Load pannunga ma"):
    if website_url:
        with st.spinner("Loading ma..."):
            try:
                content = load_website_content(website_url)
                st.session_state['content'] = content
                st.success("✅ Load aagiduchu ma!")
            except Exception as e:
                st.error(f"Error ma: {e}")
    else:
        st.warning("⚠️ URL kudunga ma Vimala!")

st.write("---")

user_question = st.text_input("❓ Ungal kelvi enna ma?", placeholder="Product pathi kelunga ma...")

if st.button("💬 Answer pannunga ma"):
    if user_question:
        if 'content' not in st.session_state:
            st.warning("⚠️ Muthalla website ah load pannunga ma!")
        else:
            with st.spinner("Yosikuren ma..."):
                try:
                    answer = get_product_info(user_question, st.session_state.get('content', ''))
                    st.write("### 🌸 Answer ma:")
                    st.write(answer)
                except Exception as e:
                    st.error(f"Error ma: {e}")
    else:
        st.warning("⚠️ Kelvi kudunga ma!")

st.write("---")
st.markdown("<p style='text-align: center; color: #FF69B4;'>Made with 💖 by Vimala</p>", unsafe_allow_html=True)
