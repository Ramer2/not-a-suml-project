"""
Task 2 - Streamlit interface. Run from the project root:  streamlit run app/app.py
"""
import streamlit as st

from predict import predict  # works because Streamlit puts app/ on sys.path

st.title("Iris Species Predictor")
st.write(
    "Enter the four measurements of an iris flower (in centimeters) and click "
    "**Predict**. The app predicts the species: setosa, versicolor or virginica."
)

# Defaults are a real setosa flower so the first click already shows a result.
sepal_length = st.number_input("Sepal length (cm)", min_value=0.0, value=5.1, step=0.1)
sepal_width = st.number_input("Sepal width (cm)", min_value=0.0, value=3.5, step=0.1)
petal_length = st.number_input("Petal length (cm)", min_value=0.0, value=1.4, step=0.1)
petal_width = st.number_input("Petal width (cm)", min_value=0.0, value=0.2, step=0.1)

if st.button("Predict"):
    features = [sepal_length, sepal_width, petal_length, petal_width]  # training order
    species = predict(features)
    st.success(f"Predicted species: {species.capitalize()}")
