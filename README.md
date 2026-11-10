# PasswordChecker

A responsive web application that estimates how closely a password resembles patterns learned from leaked-password data. PasswordChecker combines a trained machine-learning model, practical improvement guidance, and an optional known-breach lookup.

## Features

- AI-estimated leaked-pattern risk score with Strong, Medium, and Weak labels.
- Optional lookup against Have I Been Pwned's Pwned Passwords service.
- Guidance about length, repetition, and predictable sequences.
- Masked input with a show/hide control and responsive desktop/mobile layouts.
- Server-side input validation and graceful handling of breach-service failures.

## How it works

The main score comes from the project's saved **Logistic Regression** model. It analyzes numeric features and character patterns learned from leaked and generated password examples. The model was selected in the original training project after comparison with Random Forest and a rule-based baseline.

The score is an estimate of similarity to the training data, **not the probability that an account will be hacked**.

| Score | Password label |
| --- | --- |
| Below 30% | Strong |
| 30% through 70% | Medium |
| Above 70% | Weak |

Labels and improvement guidance use rules. The optional breach check is a separate database lookup for the exact password; it is not an AI prediction. A low score or no breach match does not guarantee safety.

## Technology

| Layer | Technology |
| --- | --- |
| Interface | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Web server | Waitress |
| Model | scikit-learn, joblib |
| Breach data | Have I Been Pwned range API |

This website does not require Streamlit, C++, an account system, or a database.

## Project structure

```text
server.py                Flask routes and application startup
templates/index.html     Website interface
static/style.css         Responsive styling
static/app.js            Form interaction and result rendering
src/password_risk/       Existing model and breach-check modules
artifacts/               Trained model and model manifest
requirements.txt         Python dependencies
render.yaml              Render deployment configuration
test_web.py              Website integration tests
Start Website.bat        Launcher for the original Windows project setup
DEPLOYMENT.md            Hosting and operational notes
```

## Run locally

Use **Python 3.12**. From the repository directory, create an isolated environment and install the dependencies.

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

### macOS or Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python server.py
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080) and leave the server running. The default host is local-only. Set `PORT` to change the port.

On the original project computer, `Start Website.bat` uses the existing environment in the parent project directory. For a standalone clone, use the commands above.

## Tests

After installing the dependencies, run using the same environment:

```powershell
.\.venv\Scripts\python.exe -m unittest test_web -v
```

On macOS/Linux, use `.venv/bin/python -m unittest test_web -v`.

Tests cover page/assets loading, predictions matching the existing model, invalid inputs, omission of password text from responses, breach-check opt-out, match/no-match responses, and breach-service failure.

## Deployment

Upload this directory's **contents** to the repository root so `server.py`, `requirements.txt`, and `render.yaml` are at the top level. Include the trained model and the source modules. Exclude virtual environments, runtime installations, caches, secrets, and raw password datasets.

The included Render configuration specifies:

| Setting | Value |
| --- | --- |
| Python version | `3.12.13` |
| Build command | `pip install -r requirements.txt` |
| Start command | `python server.py` |
| Host environment variable | `HOST=0.0.0.0` |
| Health endpoint | `/health` |

The hosting platform supplies `PORT`. See [DEPLOYMENT.md](DEPLOYMENT.md) for setup and domain connection steps. A public URL and custom domain must be configured separately; none is implied by this repository.

## Privacy and limitations

- Use invented test passwords rather than real credentials.
- Input is sent from the browser to this application's server for analysis. The application does not save or explicitly log password entries.
- When enabled, the breach lookup hashes the password on the server and sends only the first five hash characters to Have I Been Pwned. The raw password and full hash are not sent to that service.
- Public hosting must use HTTPS. Do not enable request-body logging, debug mode, or session replay on the password form. Hosting providers may retain connection metadata.
- Inputs must be 4–64 characters. Request bodies are limited to 2 KB.
- Internet access is required for the optional breach lookup; local model inference works independently.
- The model reflects the experimental training distributions. It does not measure every aspect of password security or predict future compromises.

## Acknowledgment

Known-breach data is provided by [Have I Been Pwned: Pwned Passwords](https://haveibeenpwned.com/Passwords).
