"""
Task 1 - Train, evaluate, save and reuse a first ML model.

Workflow: load data -> split -> train -> predict -> evaluate -> save -> load & reuse
Dataset:  Iris (scikit-learn) - multiclass classification, 3 species.
"""
import os

import joblib
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

MODEL_PATH = "model.joblib"

# --- Step 1: Load and explore the dataset ---
iris = load_iris()
X = iris.data    # features (150, 4): one row = 4 measurements (cm) of ONE flower
y = iris.target  # target (150,): one value = that flower's species, encoded 0/1/2

print("=== Step 1: Dataset ===")
print("Number of samples: ", X.shape[0])
print("Number of features:", X.shape[1])
print("Feature names:     ", iris.feature_names)
print("Class names:       ", iris.target_names.tolist())  # index = label value in y

# --- Step 2: Create training and test sets (80/20) ---
# The model never sees the test set during training, so the test score estimates
# how it performs on NEW data (generalisation) instead of rewarding memorisation.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=67  # fixed seed -> identical split on every run
)

print("\n=== Step 2: Train/test split ===")
print("Training samples:", len(X_train))
print("Test samples:    ", len(X_test))

# --- Step 3: Choose and train a classifier ---
model = LogisticRegression(max_iter=1000)  # headroom so the solver surely converges
model.fit(X_train, y_train)  # learns weights (coef_) and biases (intercept_) from training data

print("\n=== Step 3: Training ===")
print("Learned weights shape (classes x features):", model.coef_.shape)

# --- Step 4: Make predictions ---
y_pred = model.predict(X_test)  # y_test = actual classes, y_pred = model's predictions

print("\n=== Step 4: Predictions (first 10 test samples) ===")
for actual, predicted in zip(y_test[:10], y_pred[:10]):
    print(f"actual: {iris.target_names[actual]:<11} predicted: {iris.target_names[predicted]}")

# --- Step 5: Evaluate the model ---
accuracy = accuracy_score(y_test, y_pred)  # share of correct predictions
cm = confusion_matrix(y_test, y_pred)      # rows = actual class, columns = predicted class
correct = cm.trace()                       # diagonal = correctly classified samples

print("\n=== Step 5: Evaluation ===")
print(f"Test Accuracy: {accuracy:.4f}")
print("Confusion matrix (rows = actual, cols = predicted), order:", iris.target_names.tolist())
print(cm)
print(f"Correct: {correct}/{len(y_test)}, incorrect: {len(y_test) - correct}")
# Accuracy alone is not enough: a single number hides WHICH classes get mixed up
# (off-diagonal cells) and can look high even when a minority class is always wrong.

# --- Step 6: Save the trained model ---
joblib.dump(model, MODEL_PATH)  # serialises the fitted model, incl. learned parameters

print("\n=== Step 6: Save ===")
print(f"{MODEL_PATH} created: {os.path.exists(MODEL_PATH)} ({os.path.getsize(MODEL_PATH)} bytes)")

# --- Step 7: Load and reuse the model (no fit() call) ---
loaded_model = joblib.load(MODEL_PATH)
y_pred_loaded = loaded_model.predict(X_test)
loaded_accuracy = accuracy_score(y_test, y_pred_loaded)

print("\n=== Step 7: Load & reuse ===")
print(f"Original model accuracy: {accuracy:.4f}")
print(f"Loaded model accuracy:   {loaded_accuracy:.4f}")
print("Same predictions:       ", (y_pred == y_pred_loaded).all())
# Same output without re-training: the file stores the already-learned parameters,
# and predict() just applies them - it's deterministic.
