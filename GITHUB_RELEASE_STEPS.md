# PFIV Guard — GitHub Repository Release Steps

## Current status

- A clean, repository-ready source package is included in this submission pack.
- No GitHub repository URL or successful push is evidenced yet.
- Keep the repository **private initially**. The team should obtain supervisor/VIT IPR clearance before making source code, paper, or detailed implementation public.
- Do not upload `.venv/`, `.env`, `.streamlit/secrets.toml`, personal QR/payment screenshots, participant responses, access tokens, credentials, or private keys.
- A patent application has not been evidenced in the current handover. Public release may affect IP strategy; seek institutional advice first.

## 1. Extract the repository-ready ZIP

Extract `PFIV_Guard_Repository_Ready.zip` to a working folder, for example:

`C:\Projects\PFIV_Guard`

Open PowerShell in that folder.

## 2. Configure Git identity (once per computer)

```powershell
git config --global user.name "Pranav Dwivedi"
git config --global user.email "YOUR_GITHUB_EMAIL"
```

Replace the email with the address associated with your GitHub account.

## 3. Initialise and commit

```powershell
git init -b main
git add .
git status
git commit -m "Initial PFIV Guard academic research prototype"
```

Before `git commit`, inspect `git status`. Confirm that no secrets, private QR screenshots, `.venv`, participant files or local machine paths are staged.

## 4. Create a private GitHub repository

Create an empty repository from GitHub's website. Suggested repository name:

`pfiv-guard`

Choose **Private** for the first push. Do not select “Add a README” or a licence when creating the empty remote because these files already exist locally.

Then connect and push:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/pfiv-guard.git
git push -u origin main
```

Replace `YOUR_USERNAME` with the actual GitHub username. Authenticate using Git Credential Manager or the approved GitHub flow; never paste a personal access token into source code or chat.

## 5. Verify repository

- Open the GitHub repository in a private/incognito browser window after signing in.
- Confirm `README.md`, `requirements.txt`, `packages.txt`, `app.py`, `models/`, synthetic `data/`, tests and documentation are present.
- Confirm `.venv`, secrets, private participant files and private QR/payment screenshots are absent.
- Run GitHub Actions if the workflow is enabled. A green workflow is evidence of CI for the committed revision, not proof of real-world security.

## 6. Deploy after repository and IP review

For Streamlit Community Cloud:

1. Open `https://share.streamlit.io/`.
2. Select Create app and choose the `pfiv-guard` repository.
3. Select branch `main` and app file `app.py`.
4. Deploy and review the build logs.
5. Test URL analysis, OCR, QR, WPFD/PFIV and safe network handling on the hosted URL.
6. Record the actual generated `.streamlit.app` URL in the report only after deployment succeeds.

The repo includes `requirements.txt` and `packages.txt` for Python and OS-level dependencies. Cloud deployment can still fail due to Python/package/model compatibility, memory limits, or platform restrictions. The saved Random Forest model was serialized with scikit-learn 1.6.1; keep that version pinned and verify the cloud environment loads it successfully.

Official documentation:
- GitHub: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
