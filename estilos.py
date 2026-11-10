import streamlit as st

def aplicar_estilos():
    st.markdown('<style>.stApp{background-color:#FAF7F2;color:#2D2420;font-family:sans-serif}.brand-navbar{background-color:#3C2A21;color:#F4EAE0;padding:18px 25px;border-radius:14px;display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.brand-title{font-size:22px;font-weight:700;margin:0;color:#F4EAE0}.brand-tag{background-color:#D5CEA3;color:#1A120B;font-size:12px;font-weight:600;padding:5px 12px;border-radius:20px}.login-card{background-color:#FFFFFF;padding:30px;border-radius:14px;border:1px solid #E6D5B8}.stTabs [data-baseweb="tab-list"]{gap:10px}.stTabs [data-baseweb="tab"]{height:44px;border-radius:8px;padding:0 20px;background-color:#EAE3D2;color:#3C2A21;font-weight:600}.stTabs [aria-selected="true"]{background-color:#D5CEA3!important;color:#1A120B!important}.stButton>button{border-radius:8px;font-weight:600}</style>', unsafe_allow_html=True)

def mostrar_barra(titulo, subtitulo, etiqueta):
    st.markdown(f'<div class="brand-navbar"><div><h1 class="brand-title">{titulo}</h1><span style="font-size:13px;opacity:0.8;">{subtitulo}</span></div><span class="brand-tag">{etiqueta}</span></div>', unsafe_allow_html=True)
