import streamlit as st

st.set_page_config(page_title="Test App", layout="wide")
st.title("🧪 Test App")

st.write("This is a simple test to verify Streamlit is working.")

if st.button("Click me!"):
    st.success("Button clicked successfully!")

st.write("If you can see this, Streamlit is working correctly.")

