# PasswordChecker website

This standalone Flask website runs the original trained TM471 model. It does not use Streamlit. The original project is preserved outside this directory.

## Run locally on this computer

Double-click `Start Website.bat`, leave that window open, then visit http://127.0.0.1:8080 . Alternatively, from this directory:

```powershell
..\.venv\Scripts\python.exe server.py
```

## Run on another computer

Install Python 3.12, create a virtual environment, install requirements.txt, and run server.py. Do not copy the Windows runtime or virtual environment to a Linux host.

## Deploy on Render

1. Create a repository containing the CONTENTS of this website directory at its root. Include src, templates, static, requirements.txt, server.py, render.yaml and the two artifacts. Do not upload raw password datasets, virtual environments, caches, logs or secrets.
2. Sign in to Render, create a Blueprint, and connect that repository. Review the free web service described by render.yaml before deploying.
3. Alternatively create a Python Web Service: build command `pip install -r requirements.txt`; start command `python server.py`; environment variables `PYTHON_VERSION=3.12.13` and `HOST=0.0.0.0`; health check `/health`. Render supplies PORT.
4. Open the HTTPS address provided by Render and test an invented example with and without the breach check. Verify `/health` returns `{"status":"ok"}`. Check resource usage before relying on the free plan for a presentation. Free services can sleep and need time to start.
5. In the service settings add your purchased domain. Follow the DNS values Render provides at your domain registrar, then wait for domain verification and HTTPS activation. No domain has been purchased or configured by this project.

## Privacy and operation

Inputs travel to the application server. The application does not persist or explicitly log them. Use HTTPS publicly. Do not enable debug mode, request-body logging, or analytics/session replay on the password form. Hosting providers may retain normal connection metadata; review their settings. The optional breach request sends only a five-character SHA-1 prefix to HIBP. The existing HIBP helper has a network timeout; a lookup failure does not discard the model result.

There is no account system or database. Requests are limited to 2 KB and inputs to 4–64 characters. A public demo should use the host's rate limiting/traffic protection if it attracts substantial traffic. No guarantee against automated abuse is made by this prototype.

## Verification

Run `python -m unittest test_web -v`. Tests cover page/assets, model parity, validation, response privacy, lookup opt-out, positive/negative lookup results and network failure. The trained artifact and prediction modules are copied unchanged from the graduation project. Changing them in the original later requires refreshing the website copies.

The model estimates similarity to experimental training distributions, not literal future account breach probability. Labels use the original thresholds, and guidance remains rule-based.
