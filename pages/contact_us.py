import streamlit as st


st.markdown(
    """
    <div class="ct-page-head">
        <div class="ct-kicker">Contact us</div>
        <h1>Have a question or feedback?</h1>
        <p>Send us a message about CineTruth AI, the sentiment analyzer, product feedback or future feature ideas.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("contact_form", clear_on_submit=False):
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message", height=160)
    submitted = st.form_submit_button("Send Message")

    if submitted:
        if not name.strip() or not email.strip() or not message.strip():
            st.warning("Please fill in all fields.")
        else:
            st.success("Thanks! Your message has been captured in the form UI. Connect this form to your preferred email or backend service when you are ready.")
