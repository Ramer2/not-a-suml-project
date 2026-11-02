# Task 2: Iris Prediction App (defense notes)

The flow: **enter 4 measurements → click Predict → see the species.**

---

## 1. Project structure

```
SUML_project/
├── train_model.py    Task 1: trains the model and saves it to model.joblib
├── model.joblib      the trained model (output of Task 1, input of Task 2)
└── app/
    ├── predict.py    model logic: loads model.joblib, defines predict(features)
    └── app.py        interface (Streamlit): inputs, Predict button, result
```

**What each file does, one line each:**

| File | Job |
|---|---|
| `train_model.py` | Learns from the Iris data (`fit`), checks accuracy, saves `model.joblib`. Runs once. |
| `model.joblib` | The trained model in a file. It connects Task 1 and Task 2. |
| `app/predict.py` | Loads the model **once**, turns 4 numbers into a species name. No UI code. |
| `app/app.py` | What the user sees. Collects 4 numbers, calls `predict()`, shows the result. No ML code. |

**How data flows:**

```
user types 4 numbers in the browser
        ↓
app.py puts them in a list in training order: [sepal_len, sepal_wid, petal_len, petal_wid]
        ↓
predict(features)  wraps the list as [[...]] and calls model.predict()
        ↓
model returns 0, 1 or 2
        ↓
predict.py maps the number to a name (0 setosa, 1 versicolor, 2 virginica)
        ↓
app.py shows "Predicted species: Setosa"
```

**Why two files?** Each has one job. `predict.py` = the model, `app.py` = the page.
If the page shows a wrong result, run `python app/predict.py` on its own: if it
passes, the bug is in how `app.py` collects the inputs.

---

## 2. Walking through the code

### `app/predict.py`

```python
MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"
```
Finds `model.joblib` relative to **this file**, not to the folder you ran the
command from. `__file__` = `app/predict.py` → `.parent` = `app/` → `.parent` = project root.
So the app works no matter where it is started from.

```python
model = joblib.load(MODEL_PATH)
SPECIES = load_iris().target_names.tolist()
```
Loads the already trained model. `SPECIES` is the list `["setosa", "versicolor", "virginica"]`;
the position in the list equals the number the model returns. `load_iris()` is used only
to read these names; nothing is trained here. `.tolist()` makes it a plain Python list,
so `predict()` returns a normal string.

```python
def predict(features):
    label = model.predict([features])[0]
    return SPECIES[label]
```
- `[features]` turns one flower `[5.1, 3.5, 1.4, 0.2]` into `[[5.1, 3.5, 1.4, 0.2]]`.
- `model.predict(...)` returns an array with one answer, e.g. `[0]`; `[0]` takes it out → `0`.
- `SPECIES[0]` → `"setosa"`.

The `if __name__ == "__main__":` block at the bottom is a self-check: one known
flower of each species. Run `python app/predict.py` → prints `predict.py OK`.

### `app/app.py`

```python
from predict import predict
```
Works because `streamlit run app/app.py` adds the `app/` folder to Python's import path.

- `st.title(...)` and `st.write(...)` explain what the app does.
- 4 × `st.number_input("... (cm)", min_value=0.0, value=..., step=0.1)` are the inputs.
  The `(cm)` in the label tells the user the unit. `min_value=0.0` rejects negative
  sizes. Defaults are a real setosa flower so the first click already works.
- `if st.button("Predict"):` runs the code below only when the button is clicked.
- Inside: build `features` in **training order**, call `predict(features)`,
  show it with `st.success(...)` (a green box).

---

## 3. Questions from the assignment

### The three you must be ready to explain

**Q1. Why does the feature order matter?**
The model does not know names like "petal width". It only sees a list of 4 numbers
and treats them by **position**: 1st = sepal length, 2nd = sepal width,
3rd = petal length, 4th = petal width, because that is the order it was trained on
(`iris.feature_names`). If you swap two values, the model gets 4 valid numbers that
describe a **different flower**. There is no error, so the mistake is silent.

Example (swap sepal length and petal width, as in the assignment):

| Input | Prediction |
|---|---|
| `[7.0, 3.2, 4.7, 1.4]` correct order | versicolor |
| `[1.4, 3.2, 4.7, 7.0]` swapped | **virginica** (wrong) |

The same swap on `[5.1, 3.5, 1.4, 0.2]` still gives setosa, so a wrong order can even
look right on one test. That is why `app.py` builds the list explicitly in training order.

**Q2. Why does the input for one flower have two levels of brackets?**
scikit-learn's `predict()` always expects a **table**: rows = flowers, columns = features
(shape `(n_samples, 4)`). The model was trained on a table of 120 rows like that.
- Outer brackets: the list of flowers (here only one).
- Inner brackets: the 4 measurements of that flower.

`[[5.1, 3.5, 1.4, 0.2]]` = a table with 1 row and 4 columns.
With one level `[5.1, 3.5, 1.4, 0.2]`, sklearn raises an error ("Expected 2D array, got 1D array").
For two flowers it would be `[[5.1, 3.5, 1.4, 0.2], [7.0, 3.2, 4.7, 1.4]]`.

**Q3. Why doesn't the app need to train the model again?**
Training (`fit`) happened once in Task 1. Its result, the learned weights
(`coef_`, `intercept_`), was saved into `model.joblib` by `joblib.dump`.
`joblib.load` restores the model **with those weights**, so `predict()` can be
used right away. Two separate stages:
- Task 1: train → evaluate → save `model.joblib`
- Task 2: load `model.joblib` → take input → predict

Why not retrain anyway?
- The app should use **the model you evaluated** in Task 1. The accuracy you measured
  (0.9333 on the test set) belongs to this file; a model retrained inside the app is
  one nobody checked.
- Training is the expensive step (milliseconds for Iris, hours for real models);
  `predict()` is cheap.
- `predict.py` calls `load_iris()` only to read the species names, never `fit()`.

### Other questions from the learning material (short answers)

**Why put a model in an app at all?**
Without the app, using the model requires writing Python and calling `model.predict()`.
The app lets anyone use it: type numbers, click, read the answer. It does **not**
make the model more accurate; it is only an interface.

**How does Streamlit work?**
The app is a normal Python script; each `st.` call draws an element on the page.
**Streamlit reruns the whole script from top to bottom every time the user
interacts** (changes a number, clicks a button). On each run the widgets return
their current values, so Predict always uses the latest numbers, not the ones from
the previous click.
No HTML or JavaScript needed.

**Why do we show a name and not 0/1/2?**
The model returns a number (class label). A user does not know that 0 means setosa.
We map it with the dataset's own `target_names` (not a guess), so the mapping is
guaranteed to match the training labels.

**What do you check if something goes wrong?**
- App does not start → can it find `model.joblib` and import `predict.py`?
  (Solved with a path built from `__file__`.)
- `model.joblib` missing → run `python train_model.py` **from the project root**.
  It saves the file into the folder you run it from.
- App shows a wrong species → check feature order, the `[[...]]` shape, and the
  number-to-name mapping.

**Streamlit reruns the script on every click. Is the model loaded every time?**
No. Only `app.py` reruns. `predict.py` is an imported module, and Python imports a
module once and keeps it in memory, so `model.joblib` is read once (on the first page
load) and reused.

**Why does the result disappear when I change a number?**
Changing a number reruns the script. `st.button("Predict")` is `True` only in the run
caused by the click, so the new run does not draw the result. Click Predict again.

**What if the input is nonsense?**
Negative values are rejected (`min_value=0.0`): if you type -1, Streamlit does not
accept it and keeps using the last valid number. Other odd values still get an answer:
the model always picks one of the three species, even for all zeros (setosa) or 100 cm
everywhere (virginica). It cannot say "this is not an iris". Passing 3 numbers instead
of 4 to `predict()` raises
`ValueError: X has 3 features, but LogisticRegression is expecting 4 features as input.`

---

## 4. Demo script (what to show in class)

1. Show the structure (section 1) and point at `model.joblib` from Task 1.
2. Open `app/predict.py` → show `predict(features)`. Optional: `python app/predict.py`
   prints `predict.py OK` (the function works without the UI).
3. Open `app/app.py` → show the 4 `number_input`s and the `if st.button("Predict")` block.
4. From the project root (in PyCharm's terminal the venv is usually already active;
   the prompt starts with `(.venv)`):
   ```
   .venv\Scripts\Activate.ps1
   streamlit run app/app.py
   ```
   Open http://localhost:8501. Stop the app with Ctrl+C.
5. Click **Predict** with the defaults → **Setosa**.
6. Change to these values and click Predict again to show the result follows the inputs:

| Sepal L | Sepal W | Petal L | Petal W | Expected |
|---|---|---|---|---|
| 5.1 | 3.5 | 1.4 | 0.2 | Setosa |
| 7.0 | 3.2 | 4.7 | 1.4 | Versicolor |
| 6.3 | 3.3 | 6.0 | 2.5 | Virginica |

If PyCharm underlines `from predict import predict` in `app.py`, that is only the IDE: it
doesn't know Streamlit adds `app/` to the import path. Optional fix: right-click `app/` →
Mark Directory as → Sources Root.
