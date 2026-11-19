# Task 3: Containerize the Iris app with Docker (defense notes)

The flow: **Dockerfile → `docker build` → image → `docker run` → container → app at http://localhost:8501.**

The Task 2 notes about the app code itself are in git history: `git show 97cce4e:DEFENSE.md`.

---

## 1. Project structure

```
not-a-suml-project/     project root = build context (run docker build from HERE)
├── Dockerfile          NEW: instructions for building the image
├── .dockerignore       NEW: what Docker leaves out of the build context
├── requirements.txt    NEW: Python packages with pinned versions
├── model.joblib        trained model from Task 1 (copied INTO the image)
├── train_model.py      Task 1 script (NOT in the image)
└── app/
    ├── predict.py      unchanged from Task 2
    └── app.py          unchanged from Task 2
```

| File | Job |
|---|---|
| `Dockerfile` | Recipe for the image: base Python, install packages, copy app + model, start command. |
| `requirements.txt` | Which packages `pip` installs in the image, each with an exact version (`==`). |
| `.dockerignore` | Files Docker should not send to the build (venv, caches, IDE files, training script). |

**What ends up inside the image** (checked with `docker run --rm iris-streamlit ls -la /app /app/app`):

```
/app/
├── requirements.txt
├── model.joblib
└── app/
    ├── app.py
    └── predict.py
```

The image has no training script, no dataset and no venv, only what the running app needs.

---

## 2. Walking through the files

### `Dockerfile`, line by line

```dockerfile
FROM python:3.12-slim
```
Starts from an existing image that already has Python 3.12 installed. The app ran on Python 3.12 in
Task 2, and scikit-learn 1.9.1 (the version that saved the model) installs on it.
`docker run --rm iris-streamlit python --version` prints `Python 3.12.x`. `slim` leaves out extra OS
packages, so the image is smaller. It does **not** include Streamlit or scikit-learn; we install those below.

```dockerfile
WORKDIR /app
```
Sets the working folder inside the image. From now on, `.` means `/app`.

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```
Copies `requirements.txt` from my computer to `/app/requirements.txt` in the image, then installs the
packages. `RUN` happens **at build time**, so the packages become part of the image.
`--no-cache-dir` tells pip not to keep its download cache, which makes the image smaller.

```dockerfile
COPY app/ ./app/
COPY model.joblib .
```
Code goes to `/app/app/`, model to `/app/model.joblib`.

```dockerfile
EXPOSE 8501
```
Documents that the app listens on port 8501. It does **not** open the port to my computer on its own;
that is what `-p` in `docker run` does.

```dockerfile
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
The command that runs **when a container starts** (not during the build). The list form
`["program", "arg1", ...]` is what the assignment asks for.
`--server.address=0.0.0.0` makes Streamlit listen on all of the container's network interfaces
(explained in section 3).

**Why copy `requirements.txt` before the code?** Docker caches every step. If I change `app.py` and
rebuild, Docker reuses the cached `pip install` and only repeats the `COPY` steps after it. If the code were
copied first, every code change would reinstall all packages.

### Why `predict.py` did not need any change

```python
MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"
```
Inside the container: `__file__` = `/app/app/predict.py` → `.parent` = `/app/app` → `.parent` = `/app`
→ `/app/model.joblib`. That is exactly where `COPY model.joblib .` puts it. The path is built from the
file's location, not from the folder the program was started in, so it works on my computer and in
the container without changes.

### `requirements.txt`

```
streamlit==1.67.0
scikit-learn==1.9.1
joblib==1.6.0
```
- These are the three packages the code imports.
- `scikit-learn==1.9.1` comes from the model file: `model.joblib` stores the version that saved it
  (`_sklearn_version` = `1.9.1`). Loading a model with a different scikit-learn version gives an
  `InconsistentVersionWarning` and can break or give wrong results.
- numpy, scipy, pandas and others get installed automatically as dependencies of these three. They are
  not pinned. The assignment says a short requirements.txt does not lock every indirect dependency,
  and that is fine for this exercise.

### `.dockerignore`

```
.venv/
venv/
**/__pycache__/
**/*.pyc
.idea/
.git/
train_model.py
*.md
```
Before building, Docker sends the build context (the whole folder) to the builder. `.dockerignore`
removes files from it:
- `.venv/`, `venv/`: my local virtual environment. It can be hundreds of MB, it was made for my own
  computer, and the image installs its own packages anyway.
- `**/__pycache__/`, `**/*.pyc`: Python cache, recreated automatically. The `**/` means "in any folder".
  A plain `__pycache__/` only matches a folder in the project root. Running the app locally creates
  `app/__pycache__/`, and without `**/` that folder would be copied into the image by `COPY app/ ./app/`.
  I tested both versions.
- `.idea/`: PyCharm project settings that are still in the repo. `.git/`: git history.
- `train_model.py`: the container needs the **trained model**, not training.
- `*.md`: these notes.

What it keeps: `app/`, `model.joblib`, `requirements.txt`, i.e. everything `COPY` needs.
If I added `model.joblib` to `.dockerignore`, the build would fail at `COPY model.joblib .` because the file would not be found.

There is no `.vscode/` line because the project has no such folder. Even if VS Code created one, it could
not get into the image: `COPY` only takes `requirements.txt`, `app/` and `model.joblib`.

---

## 3. Questions from the assignment

### The four you must be ready to explain

**Q1. What is the difference between an image and a container?**
- **Image** = the result of `docker build`. A packaged, read-only template: Python, the packages, the
  code and the model. It does not run.
- **Container** = a running instance created from an image by `docker run`.

It works like a class and an object: one image, as many containers as you want. Stopping or removing a
container does not delete the image. `docker images` lists images; `docker ps` lists running containers.

**Q2. What does the final `.` in `docker build -t iris-streamlit .` mean?**
It is the **build context**: the folder Docker can take files from. `COPY` source paths are relative to
it (the destination paths are relative to `WORKDIR`), and Docker looks for the `Dockerfile` there. That is
why I run the command from the project root. From another folder, Docker would not find the `Dockerfile`,
or `COPY model.joblib .` would fail.
`-t iris-streamlit` gives the image its name.

**Q3. Why must `model.joblib` be inside the image?**
A container sees only its own filesystem, the files that are in the image. It cannot see the files on
my computer. `predict.py` loads `/app/model.joblib` when the app starts. If `model.joblib` is missing from
the project folder, `docker build` fails at `COPY model.joblib .`. If the Dockerfile had no
`COPY model.joblib .` line at all, the image would build, but the app would fail with a
`FileNotFoundError` as soon as the page loads.
It also makes the image self-contained: the same image works on any computer with Docker, and
it ships **the exact model I evaluated** in Task 1 (accuracy 0.9333). The container does not retrain.

**Q4. What does `-p 8501:8501` do?**
It publishes a port: `-p HOST_PORT:CONTAINER_PORT`. A container has its own network, so without `-p`,
`localhost:8501` on my computer does not reach it. `-p 8501:8501` maps port 8501 on my computer to port
8501 in the container, where Streamlit listens, so the browser can use `localhost:8501`:

```
browser → localhost:8501 (my computer) → port 8501 (container) → Streamlit
```

If port 8501 were busy on my computer, `-p 8502:8501` would work with `localhost:8502`. The checkpoint
requires `8501:8501`, though.

### Other questions from the learning material (short answers)

**Why `--server.address=0.0.0.0`?**
Inside a container, `localhost` is the container's own loopback. Traffic forwarded by `-p` arrives on the
container's network interface, not on its loopback. If Streamlit listened only on `localhost`, the
browser could not connect even with `-p`. `0.0.0.0` = listen on all interfaces.

**Does the image contain an operating system?**
It contains Linux system files and programs (the `python:3.12-slim` base), but no kernel of its own.
Containers use the host's kernel. On Linux that is my computer's own kernel. On Windows and macOS,
Docker Desktop runs a small Linux VM (WSL 2 on Windows), and the containers use that VM's kernel.

**Build time vs run time?**

| Stage | Example | What happens |
|---|---|---|
| Build time | `RUN pip install -r requirements.txt` | Installs packages into the image. |
| Build time | `COPY model.joblib .` | Adds the model to the image. |
| Run time | `CMD ["streamlit", ...]` | Starts the app when a container starts. |
| Run time | `docker run -p 8501:8501 iris-streamlit` | Creates the container and publishes the port. |

**I changed `app.py`. Why don't I see the change?**
The image is a snapshot taken at build time. Run `docker build` again, then start a new container.

**The build took a few seconds and says `Using cache` (or `CACHED`). Did it really build anything?**
Yes. Docker reuses every step whose inputs have not changed since the last build, so `pip install` does
not run again. To show a build from scratch: `docker build --no-cache -t iris-streamlit .`. It downloads
all packages again, so it needs internet and takes longer.

**Why pin versions with `==`?**
Without a version, a build next month could install a newer release, and the same Dockerfile would
give a different environment. `==` fixes the versions of these three packages, so later builds change
much less. It doesn't lock everything: indirect dependencies and the `python:3.12-slim` base image can
still change. For scikit-learn the pin matters most, because the model must be loaded with a compatible version.

**What does the warning `Running pip as the 'root' user` during the build mean?**
It warns that installing as root can conflict with the system's own Python packages. In a container
that does not matter: the container is isolated and nothing else uses its Python. The build still succeeds.
(It only shows when the `pip install` step actually runs, not when it comes from the cache.)

**The build starts with `DEPRECATED: The legacy builder is deprecated`. Is that a problem?**
No. Ubuntu's `docker.io` package comes without the `buildx` plugin, so Docker uses its older builder.
The image is still built correctly; the output ends with `Successfully tagged iris-streamlit:latest`.
Docker Desktop uses the newer builder (BuildKit), which prints `[+] Building` and ends with
`naming to docker.io/library/iris-streamlit:latest`.

**Streamlit prints a Local, a Network and an External URL. Which one do I open?**
`http://localhost:8501`, the Local URL. Streamlit prints these addresses from inside the container, so it
does not know about `-p`. The Local URL is right only because I mapped 8501 to 8501; with `-p 8502:8501`
it would still say 8501, but the browser would need `localhost:8502`. The Network URL (`172.17.x.x`) is
the container's address on Docker's internal network, and the External URL is Streamlit's guess at my
public IP. The browser reaches the app through the `-p` mapping, so `localhost` is the address to use.

**Something fails. Where do I look?**
- **The image does not build** → find the first failed step in the output. Did I run the command from
  the project root? Did `.dockerignore` hide a file that `COPY` needs?
- **It builds, but the container stops** → read the error from `docker run`: check the `CMD` command,
  the script path, the installed packages.
- **`docker run` says `port is already allocated` or `address already in use`** → something already uses
  port 8501: an old container (`docker ps`, then `docker stop <CONTAINER ID>`) or a local
  `streamlit run` left over from Task 2 (stop it with Ctrl+C).
- **The page opens, but prediction fails** → is `model.joblib` at `/app/model.joblib`? Are the package
  versions compatible with the model? Quick check:
  `docker run --rm iris-streamlit python app/predict.py` should print `predict.py OK`.
- **The container runs, but the browser cannot connect** → Streamlit on port 8501 and address `0.0.0.0`?
  Did I use `-p 8501:8501`?

---

## 4. Demo script (what to show in class, in VS Code)

Before class:
- Make sure Docker is running. On Windows or macOS, start **Docker Desktop** and wait until it reports
  that the engine is running. On Linux the Docker service starts with the system.
- In VS Code: **File → Open Folder…** and choose `not-a-suml-project` (the folder with the `Dockerfile`).
- Open a terminal: **Terminal → New Terminal** (Ctrl+`). It starts in the project root; `ls` should list
  `Dockerfile`, `app` and `model.joblib`.

You don't need the venv for this task. Python and the packages live in the image.

1. Prove Docker works:
   ```
   docker --version
   docker info
   ```
2. Show the files in the VS Code Explorer: `Dockerfile`, `.dockerignore`, `requirements.txt` (section 2).
3. Build the image:
   ```
   docker build -t iris-streamlit .
   ```
   Success = no errors, and the output ends with `Successfully tagged iris-streamlit:latest`
   (or `naming to docker.io/library/iris-streamlit:latest` with Docker Desktop). Then:
   ```
   docker images
   ```
   lists `iris-streamlit`.
4. Run a container:
   ```
   docker run -p 8501:8501 iris-streamlit
   ```
   The terminal now shows Streamlit's log and stays busy while the container runs.
   Optional: open a second terminal with the **+** in the terminal panel (Ctrl+Shift+`) and run
   `docker ps`. It shows the container with `0.0.0.0:8501->8501/tcp`.
5. Open http://localhost:8501 (Ctrl+click the Local URL in the terminal, or type it in the browser).
   Check that all four inputs are on the page. Then test all three flowers, clicking **Predict** after
   each change:

| Sepal L | Sepal W | Petal L | Petal W | Expected |
|---|---|---|---|---|
| 5.1 | 3.5 | 1.4 | 0.2 | Setosa |
| 7.0 | 3.2 | 4.7 | 1.4 | Versicolor |
| 6.3 | 3.3 | 6.0 | 2.5 | Virginica |

6. Click into the terminal where `docker run` is running and press **Ctrl+C**. Streamlit prints
   `Stopping...` and the container stops. Then:
   ```
   docker ps -a
   docker images
   ```
   `docker ps -a` lists the container as `Exited`: it is stopped, not deleted. `docker images` still
   lists `iris-streamlit`: stopping a container does not delete its image.

If asked to prove the model and the code are inside the image:
```
docker run --rm iris-streamlit python app/predict.py
docker run --rm iris-streamlit ls -la /app /app/app
```
The first prints `predict.py OK`, the second lists the files from section 1. `--rm` deletes the
container as soon as the command finishes.
