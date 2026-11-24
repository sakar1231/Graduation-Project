# PasswordChecker website

This standalone Flask website runs the original trained TM471 model. It does not use Streamlit. The training script (`train.py`), the unit tests (`tests/`) and the model manifest are included in this repository.

## Run locally

Install Python 3.12, create a virtual environment, install `requirements.txt`, then from this directory run:

```powershell
.venv\Scripts\python.exe server.py
```

Visit http://127.0.0.1:8080 and leave the window open.

## Run on another computer

On macOS or Linux use `.venv/bin/python server.py` after installing the requirements. Do not copy a Windows virtual environment to a Linux host.

## Deploy on Render

1. Create a repository containing the CONTENTS of this website directory at its root. Include src, templates, static, requirements.txt, server.py, render.yaml and the two artifacts. Do not upload raw password datasets, virtual environments, caches, logs or secrets.
2. Sign in to Render, create a Blueprint, and connect that repository. Review the free web service described by render.yaml before deploying.
3. Alternatively create a Python Web Service: build command `pip install -r requirements.txt`; start command `python server.py`; environment variables `PYTHON_VERSION=3.12.13` and `HOST=0.0.0.0`; health check `/health`. Render supplies PORT.
4. Open the HTTPS address provided by Render and test an invented example with and without the breach check. Verify `/health` returns `{"status":"ok"}`. Check resource usage before relying on the free plan for a presentation. Free services can sleep and need time to start.
5. In the service settings add the custom domain (this project uses `sakargraduationproject.cloud`). Follow the DNS values Render provides at the domain registrar, then wait for domain verification and HTTPS activation. After you push changes to the repository, Render redeploys automatically.

## Privacy and operation

Inputs travel to the application server. The application does not persist or explicitly log them. Use HTTPS publicly. Do not enable debug mode, request-body logging, or analytics/session replay on the password form. Hosting providers may retain normal connection metadata; review their settings. The optional breach request sends only a five-character SHA-1 prefix to HIBP. The existing HIBP helper has a network timeout; a lookup failure does not discard the model result.

There is no account system or database. Requests are limited to 2 KB and inputs to 4–64 characters. A public demo should use the host's rate limiting/traffic protection if it attracts substantial traffic. No guarantee against automated abuse is made by this prototype.

## Verification

Run `python -m unittest test_web -v` (5 website tests: page/assets, model parity, validation, response privacy, lookup opt-out, positive/negative lookup results and network failure) and `PYTHONPATH=src python -m unittest discover -s tests -v` (11 unit tests for features, baseline, predictor, breach lookup and the saved model; on Windows PowerShell set `$env:PYTHONPATH="src"` first). The trained artifact and prediction modules are the ones produced by the graduation project's `train.py`; retraining overwrites `artifacts/` unless `--output` points elsewhere. The raw RockYou dataset is not stored in the repository.

The model estimates similarity to experimental training distributions, not literal future account breach probability. Labels use the original thresholds, and guidance remains rule-based.
