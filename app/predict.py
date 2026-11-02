"""
Task 2 - Prediction logic: load the model from Task 1 and classify one flower.
"""
from pathlib import Path

import joblib
from sklearn.datasets import load_iris

# Path is built from this file's location, not the current working directory,
# so it works no matter which folder the app is started from.
MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"

model = joblib.load(MODEL_PATH)              # already fitted in Task 1 -> no fit() here
SPECIES = load_iris().target_names.tolist()  # index = label: 0 setosa, 1 versicolor, 2 virginica


def predict(features):
    """features = [sepal length, sepal width, petal length, petal width] in cm (training order)."""
    label = model.predict([features])[0]  # [features] -> 2D: a collection with ONE flower
    return SPECIES[label]


if __name__ == "__main__":
    # Self-check: one known flower of each species from the Iris dataset.
    assert predict([5.1, 3.5, 1.4, 0.2]) == "setosa"
    assert predict([7.0, 3.2, 4.7, 1.4]) == "versicolor"
    assert predict([6.3, 3.3, 6.0, 2.5]) == "virginica"
    print("predict.py OK")
