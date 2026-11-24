# PasswordChecker

A responsive web application that estimates how closely a password resembles patterns learned from leaked-password data. PasswordChecker combines a trained machine-learning model, practical improvement guidance, and an optional known-breach lookup.

**Live demo:** https://sakargraduationproject.cloud (hosted on Render; the free plan can take a short time to wake up after being idle).

Final-year project (TM471B) at the Arab Open University. Use invented example passwords only.

## Features

- AI-estimated leaked-pattern risk score with Strong, Medium, and Weak labels.
- Optional lookup against Have I Been Pwned's Pwned Passwords service.
- Guidance about length, repetition, and predictable sequences.
- Masked input with a show/hide control and responsive desktop/mobile layouts.
- Server-side input validation and graceful handling of breach-service failures.

## How it works

The main score comes from the project's saved **Logistic Regression** model, calibrated with sigmoid (Platt) scaling. It analyzes 13 numeric features and character 2-4-gram patterns learned from 50,000 leaked (RockYou sample) and 50,000 generated strong passwords. The model was selected in the training script after comparison with a Random Forest and a rule-based length-and-character-class baseline (at least 8 characters and at least three of the four character classes).

The score is an estimate of similarity to the training data, **not the probability that an account will be hacked**.

| Score | Password label |
| --- | --- |
| Below 30% | Strong |
| 30% through 70% | Medium |
| Above 70% | Weak |

Labels and improvement guidance use rules. The optional breach check is a separate database lookup for the exact password; it is not an AI prediction. A low score or no breach match does not guarantee safety.

**Known limitation:** the "strong" class in the training data is random 12-24 character strings that contain all four character classes. Natural multi-word passphrases look different from those, so the model can label them Weak even when they are long. The score measures similarity to the training data, not real-world strength.

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
train.py                 Training and evaluation script (see "Retrain the model")
templates/index.html     Website interface
static/style.css         Responsive styling
static/app.js            Form interaction and result rendering
src/password_risk/       Data loading, features, baseline, predictor, breach check
artifacts/               Trained model, model manifest (and metrics if you add them)
tests/                   Unit tests for features, baseline, predictor, breach lookup, model
test_web.py              Website integration tests
requirements.txt         Python dependencies
render.yaml              Render deployment configuration
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

## Tests

After installing the dependencies, run both test sets using the same environment.

Windows (PowerShell):

```powershell
.\.venv\Scripts\python.exe -m unittest test_web -v
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS/Linux:

```bash
.venv/bin/python -m unittest test_web -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

`test_web.py` (5 tests) covers page/asset loading, predictions matching the saved model, invalid inputs, omission of password text from responses, breach-check opt-out, match/no-match responses, and breach-service failure.

`tests/` (11 tests) covers the feature extraction, the rule-based baseline, the predictor output, the breach-lookup helper, and a check that the saved model file loads and returns a valid score.

## Retrain the model

The dataset is **not** included in this repository. To retrain you need the RockYou list (`rockyou.txt` or `rockyou.txt.tar.gz`):

```bash
python train.py --leaked path/to/rockyou.txt.tar.gz
```

By default this writes to `artifacts/` and **overwrites** `password_risk_model.joblib`, the manifest and the metrics files. Use `--output some_other_folder` to keep the supplied model unchanged. The seed is fixed (42), so the sampling, the generated passwords and the 64,000 / 16,000 / 20,000 train / calibration / evaluation split are reproducible. Training is not needed to run the website or the supplied model.

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

The hosting platform supplies `PORT`. See [DEPLOYMENT.md](DEPLOYMENT.md) for setup and domain connection steps. The live deployment uses the Render service from this repository with the custom domain https://sakargraduationproject.cloud.

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
