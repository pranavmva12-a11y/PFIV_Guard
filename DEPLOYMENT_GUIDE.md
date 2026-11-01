# PFIV Guard — Public Academic Demo Deployment

This guide prepares the project for **Streamlit Community Cloud**. The source archive is deployment-ready at the configuration level, but no public app has been created yet. A public URL is issued only after the owner connects a GitHub repository and clicks Deploy.

## Before publishing

1. Review the repository for personal information, credentials and private data. Do not commit `.env`, `.streamlit/secrets.toml`, access tokens, or participant records.
2. Keep the trained model `models/random_forest.pkl` in the repository. It is required for the live ML branch. The supplied artifact is 33.6 MB.
3. Keep `requirements.txt`, `packages.txt`, `.streamlit/config.toml`, `app.py`, Python modules, model artifacts and required data files in the same repository structure.
4. Do not upload `.venv/`, `__pycache__/`, `.pytest_cache/`, `.git/`, or local secrets.
5. Run the tests before publishing:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q -rs
   .\.venv\Scripts\python.exe purpose_pfiv_evaluation.py
   ```

6. Ensure `PFIV_ENABLE_LOCAL_DEMO_UI` is **not** set in cloud environment variables. The localhost fixture bypass remains hidden/off by default.

## Publish source to GitHub

Create a repository such as `pfiv-guard`. A public repository is convenient for a university demonstration; use a private repository if appropriate for your project/team and ensure the deployment service is granted access.

From the project root in PowerShell:

```powershell
git init
git add .
git status
git commit -m "Prepare PFIV Guard academic demo"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/pfiv-guard.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with the actual GitHub account name. Inspect `git status` before committing and confirm that `.venv`, secrets, and participant data are not staged.

## Deploy on Streamlit Community Cloud

1. Sign in at <https://share.streamlit.io/> using the GitHub account that owns the repository.
2. Select **Create app**.
3. Choose the repository `YOUR_GITHUB_USERNAME/pfiv-guard`.
4. Select branch `main`.
5. Set the app entrypoint file to `app.py`.
6. Open **Advanced settings** and select **Python 3.12**. The saved model dependency is pinned to scikit-learn 1.6.1; use the pinned `requirements.txt` in the repo.
7. Leave secrets empty unless a future, documented integration needs them. No API key is required by the current version.
8. Deploy and wait for the build log to finish. If the build fails, inspect the first dependency/import error in the log and fix that specific issue.
9. Open the generated `https://<your-app-name>.streamlit.app` URL and run the smoke tests below.

The root `packages.txt` installs the Linux Tesseract executable needed by `pytesseract`. `requirements.txt` installs the Python dependencies. Streamlit Community Cloud reads these files from the repository; see its official documentation for dependency and deployment details.

## Post-deployment smoke test

Use public, non-sensitive pages first:

- `https://www.python.org/` — expect a purpose estimate such as Education / Learning or Informational / Knowledge depending on the currently served page HTML; no fixed classifier result should be promised.
- `https://www.wikipedia.org/` — informational content; PFIV should be Not Applicable when no active transaction page is observed.
- A public e-commerce homepage — purpose estimate; PFIV should remain Not Applicable unless the inspected HTML contains an active checkout step.
- Screenshot demo — OCR evidence only; the OCR score is not phishing probability.
- UPI QR demo — decode fields only; do not initiate payment or claim payee identity is verified.

Do not expect a payment processor to be detected on every payment-company homepage: a marketing page is not necessarily a checkout page. Dynamic, login-gated, anti-bot, or JavaScript-rendered pages may return incomplete evidence.

## Public demo safeguards and limitations

- Localhost fixture controls are hidden unless `PFIV_ENABLE_LOCAL_DEMO_UI=1` is explicitly set. Do not set it on a public instance.
- The app limits analysis requests per browser session, but this does not provide global rate limiting or protection against coordinated abuse.
- The URL fetcher applies private/loopback/reserved-target checks, redirect checks, response-size bounds and timeouts. This has not been independently penetration-tested; DNS rebinding and broader SSRF threats need expert review before production use.
- Do not deploy this academic prototype as a service for sensitive financial decisions or unrestricted public URL scanning.
- Do not collect real card numbers, CVV, OTPs, passwords, PINs, or actual payment transactions.
- The facilitator-mode usability study keeps records in the active Streamlit session and provides CSV download; it is not a secure study database. Download and store records in an institution-approved location.

## Alternative: Docker

For a host that supports Docker:

```bash
docker build -t pfiv-guard .
docker run --rm -p 8501:8501 pfiv-guard
```

Open `http://localhost:8501`. The Docker image installs Tesseract and uses Python 3.12. Keep the local demo bypass disabled.

## Deployment status wording for reports

Before a working hosted URL exists, describe the status as:

> “Deployment configuration has been prepared for Streamlit Community Cloud. Public hosting is pending repository-owner authentication and deployment.”

After deployment, record the actual generated URL, deployment date, build status and post-deployment smoke-test evidence. Do not invent a public URL or claim deployment before those steps are complete.

## Official references

- Streamlit Community Cloud deployment: <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy>
- Streamlit dependency management: <https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies>
- Streamlit app management and GitHub redeployment: <https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app>
