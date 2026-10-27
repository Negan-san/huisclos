# HuisClos

Use generative AI on client files without breaching professional secrecy.

HuisClos pseudonymizes French legal documents locally before they are sent to an LLM, then
restores the real values in the answer.

Work in progress.

## Installation

```
git clone <repository-url> huisclos && cd huisclos
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m streamlit run streamlit_app.py
```

On macOS or Linux, use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.
