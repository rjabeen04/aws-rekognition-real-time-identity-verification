import streamlit as st
from app.config import DANGER_LABELS
from app.rekognition import save_data


def render_settings():
    st.markdown('<h2 style="color:white;">⚙️ System Settings</h2>', unsafe_allow_html=True)
    st.markdown("---")

    # --- SIMILARITY THRESHOLD ---
    st.markdown('<p style="color:#00ffcc; font-size:1.2rem; font-weight:900;">🎯 Face Match Similarity Threshold</p>', unsafe_allow_html=True)
    threshold = st.slider("Minimum similarity % to verify identity", 50, 99,
                          st.session_state.get("similarity_threshold", 80), step=1)
    st.markdown(f'<p style="color:#ffffff; font-size:1.1rem; font-weight:800;">Current: <span style="color:#00ffcc; font-weight:900;">{threshold}%</span> — higher = stricter matching</p>', unsafe_allow_html=True)

    st.markdown("---")

    # --- MAX LABELS ---
    st.markdown('<p style="color:#00ffcc; font-size:1.2rem; font-weight:900;">🔍 Max Rekognition Labels</p>', unsafe_allow_html=True)
    max_labels = st.slider("Maximum labels to detect per scan", 5, 30,
                           st.session_state.get("max_labels", 20), step=1)

    st.markdown("---")

    # --- DANGER LABELS ---
    st.markdown('<p style="color:#00ffcc; font-size:1.2rem; font-weight:900;">🚨 Danger Labels</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:#ffffff; font-size:1.1rem; font-weight:800;">These labels trigger a security alert when detected.</p>', unsafe_allow_html=True)

    if "custom_danger_labels" not in st.session_state:
        st.session_state.custom_danger_labels = sorted(DANGER_LABELS)

    cols = st.columns(4)
    for idx, label in enumerate(st.session_state.custom_danger_labels):
        with cols[idx % 4]:
            st.markdown(f'<div style="background:#1a0000; border:1px solid #ff4444; border-radius:6px; padding:8px; text-align:center; margin-bottom:8px;"><p style="color:#ff4444; font-weight:800; margin:0; font-size:1rem;">{label}</p></div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        new_label = st.text_input("Add new danger label", placeholder="e.g. Scissors", label_visibility="collapsed")
    with col_btn:
        if st.button("➕ Add", type="primary"):
            if new_label and new_label not in st.session_state.custom_danger_labels:
                st.session_state.custom_danger_labels.append(new_label)
                save_data()
                st.rerun()

    if st.session_state.custom_danger_labels:
        remove_label = st.selectbox("Remove a danger label", ["-- Select --"] + st.session_state.custom_danger_labels)
        if st.button("🗑️ Remove", type="primary"):
            if remove_label != "-- Select --":
                st.session_state.custom_danger_labels.remove(remove_label)
                save_data()
                st.rerun()

    st.markdown("---")
    if st.button("💾 Save Settings", type="primary"):
        st.session_state.similarity_threshold = threshold
        st.session_state.max_labels = max_labels
        save_data()
        st.success("✅ Settings saved.")
