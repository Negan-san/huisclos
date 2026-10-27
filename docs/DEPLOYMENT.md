# Deploying HuisClos on Streamlit Community Cloud

The hosted app at <https://huisclos.streamlit.app> is a public demonstration on fictitious data. On the cloud, the text you paste travels to the host's server, so real client files must only be processed with a local installation (see D-14 in docs/DECISIONS.md).

## Before deploying

- Deploy from the `main` branch, after a gate GO.
- `requirements.txt` pins every dependency (`==` or the spaCy model wheel URL) and excludes PyTorch and transformers; `tests/test_deploy.py` checks this.
- `.streamlit/config.toml` sets `gatherUsageStats = false`. No web font, CDN or telemetry is used.
- A clean install of `requirements.txt` on Python 3.12 takes a few minutes; the measured duration is recorded in docs/PROGRESS.md (session S51).
- Memory: `python scripts/measure_memory.py` reports the resident memory after startup, after the first detection and after ten more. The S51 measurement is in D-05; its sampled values stay below 1 GB. The script's "Peak RSS" is the maximum of these three snapshots, not a continuously measured peak; cloud memory remains to be checked in the hosting logs.

## Deployment steps

1. Sign in to <https://share.streamlit.io> with the GitHub account that can read the repository, and authorise Streamlit to access it.
2. Click **Create app**, then choose to deploy a public app from GitHub.
3. Fill in the form:
   - Repository: the HuisClos repository;
   - Branch: `main`;
   - Main file path: `streamlit_app.py`;
   - App URL: `huisclos` (gives huisclos.streamlit.app).
4. Open **Advanced settings**:
   - Python version: **3.12**;
   - Secrets: paste the line below, which shows the public demo banner.

   ```toml
   HUISCLOS_PUBLIC_DEMO = "true"
   ```

5. Click **Deploy**. The first build installs the dependencies and the spaCy model, which takes several minutes. The first detection then loads the model (a few seconds); later detections reuse the same engine, shared by all visitors through `st.cache_resource`.
6. Check the result: the yellow "Public demo" banner is visible, **Load sample case** then **Detect sensitive data** opens the Review step.

## Operating the app

- **Sleep**: an app with no traffic for 12 hours goes to sleep. The next visitor sees a page with a button to wake it up; the app then restarts and rebuilds its environment, which can take a few minutes.
- **Python version**: it cannot be changed on a running app. To change it, delete the app from the workspace, then deploy it again with the same URL and the new version in Advanced settings. Secrets must be entered again.
- **Updates**: each push to `main` redeploys the app automatically. A change to `requirements.txt` triggers a full reinstall.
- **Secrets**: they can be edited later from the app menu (**Settings**, then **Secrets**) without redeploying. The app reads `HUISCLOS_PUBLIC_DEMO` from the environment or from the secrets; only the value `"true"` shows the banner.
- **Logs**: open the app, then **Manage app** in the bottom right corner; the panel shows the build and runtime logs. From the workspace, the app menu also offers **Logs** and **Reboot app**.
- **Data**: application code does not write user documents or mapping tables to the server disk; downloads are built in memory. User text is never cached between sessions (`tests/test_deploy.py`). These static checks cover the interface code, not all framework internals or hosting infrastructure. Closing a tab does not guarantee immediate removal of disconnected session state from server memory. Use **Reset session** and confirm to clear the active session explicitly. Use fictitious data only on the hosted demo.
