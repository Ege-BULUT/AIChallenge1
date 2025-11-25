import streamlit as st
import apibridge as API

if st.button("Check Health:"):
    with st.spinner("Checking..."):
        HP = API.health_check()
        st.write(HP)