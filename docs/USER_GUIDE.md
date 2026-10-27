# HuisClos user guide

This guide is written for lawyers and legal staff. It assumes no programming knowledge.
HuisClos replaces names and identifiers in a French legal document with tokens such as
`[PERSONNE_1]`, so that you can send the text to an AI tool. It then puts the real values
back into the answer. With a local installation, everything runs on your computer. The
online demo runs on the host's server and must only receive fictitious data.

Important: pseudonymization is not anonymization (GDPR, art. 4(5) and recital 26). The
pseudonymized text remains personal data. Read it before you send it.

## 1. Installation

You install HuisClos once. You need an internet connection during the installation, and
about ten minutes. After that, HuisClos works without internet.

### Windows

1. **Install Python 3.12.** Go to https://www.python.org/downloads/windows/ and download the
   latest "Windows installer (64-bit)" of Python 3.12. Run it. On the first screen, tick the
   box **Add python.exe to PATH**, then click **Install Now**.
2. **Download HuisClos.** Two options:
   - Without Git: open https://github.com/Negan-san/huisclos, click the green **Code** button,
     then **Download ZIP**. Right-click the downloaded file, choose **Extract All**, and
     extract it into your Documents folder.
   - With Git: open PowerShell and run
     `git clone https://github.com/Negan-san/huisclos.git`.
3. **Open PowerShell in the HuisClos folder.** In File Explorer, open the folder that contains
   the file `streamlit_app.py`. Click in the address bar, type `powershell` and press Enter.
   A blue or black window opens in that folder.
4. **Check Python.** Type the following command and press Enter. It must print
   `Python 3.12` followed by a number.

   ```powershell
   python --version
   ```

5. **Create the environment and install HuisClos.** Run these two commands, one after the
   other. The second one downloads the libraries and the French language model; it takes a
   few minutes.

   ```powershell
   python -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

6. **Start HuisClos.**

   ```powershell
   .venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address localhost
   ```

   The first time, Streamlit may ask for an email address in the window. Leave it empty and
   press Enter. Your browser then opens HuisClos.

### macOS

1. **Install Python 3.12.** Go to https://www.python.org/downloads/macos/ and download the
   latest "macOS 64-bit universal2 installer" of Python 3.12. Open it and follow the steps.
2. **Download HuisClos** as a ZIP file (green **Code** button, then **Download ZIP**) and
   double-click it to extract it, or run `git clone https://github.com/Negan-san/huisclos.git`
   in Terminal.
3. **Open Terminal** (Applications, Utilities). Type `cd` followed by a space, drag the
   HuisClos folder (the one that contains `streamlit_app.py`) into the window, and press
   Enter.
4. **Create the environment, install and start:**

   ```bash
   python3.12 -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt
   .venv/bin/python -m streamlit run streamlit_app.py --server.address localhost
   ```

## 2. Starting and stopping

- **Start**: open PowerShell (or Terminal) in the HuisClos folder, as in step 3 above, and run
  the start command only:
  - Windows: `.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address localhost`
  - macOS: `.venv/bin/python -m streamlit run streamlit_app.py --server.address localhost`
- The browser opens http://localhost:8501. "localhost" means your own computer: the page is
  not on the internet. If the browser does not open, copy this address into it.
- Keep `--server.address localhost`: it limits access to your own computer. Without it,
  the default server also accepts connections through your network interfaces.
- **Stop**: go back to the PowerShell or Terminal window and press **Ctrl+C**, then close the
  window. Closing the browser tab does not stop HuisClos.
- The first detection after a start takes longer, because the French language model is
  loaded into memory.

## 3. The three steps

The left column shows the pages (**Pseudonymize**, **Evaluation**, **Method & limits**) and
the settings. The **Pseudonymize** page guides you through three steps: **Import**,
**Review** and **Restore**. A step becomes available once the previous one is done.

### Step 1: Import

![Import step](screenshots/01_import.png)

1. Choose the tab **Paste text** and paste your document, or the tab **Upload a file** and
   choose a .txt, .docx or .pdf file. To try HuisClos first, click **Load sample case**: it
   loads a fictitious case.
2. Check the settings in the left column (section 4 below).
3. Click **Detect sensitive data**.

Accepted files: up to 5 MB and 200,000 characters. PDF files must contain selectable text;
scanned documents are refused.

### Step 2: Review

![Review step: highlighted text](screenshots/02_review_highlight.png)

The **Highlighted text** shows every detection with a colour and a label such as PERSON,
COMPANY or ADDRESS. The **Legend** explains the labels. Hover over a highlight to see its
score and source.

![Review step: entity table](screenshots/03_review_table.png)

The **Entities** table has one row per entity, however many times it appears.

- **Mask**: uncheck the box to keep this value in clear everywhere. Click in the centre of
  the box.
- **Type**: change it if the detection chose the wrong type.
- **Occurrences** and **Variants**: how many times and in which forms the value appears.
- **Note**: "Check: may refer to another person" means that a short form, such as a surname
  alone, may belong to two people. Read those places.
- **Show only these types** filters the table.

If a value was missed, use **Add a value the detection missed**: type it in **Value to
mask**, choose its **Type of this value**, then click **Add and mask everywhere**. Case and
accents are ignored when HuisClos looks for it.

A forgotten name is a breach of professional secrecy; a word masked by mistake is only a
nuisance. When in doubt, mask. Then click **Pseudonymize**. **Back to Import** returns to the
first step.

### Step 3: Restore

![Restore step: text to send](screenshots/04_restore_send.png)

1. Under **Send to your AI tool**, copy the pseudonymized text. Read it once more: a value
   that was not masked leaves your computer in clear.
2. Copy one of the lines under **Recommended instruction** (section 5) with the text, and
   send both to your AI tool.
3. Under **Restore the AI answer**, paste the answer in **Answer from the AI tool** and click
   **Restore**.

![Restore step: restored answer](screenshots/05_restore_result.png)

The **Restored text** shows the answer with the real values. Read the messages above it:

- **Exact mode** (you pasted the pseudonymized text itself): every value comes back as it was
  written.
- **Tolerant mode** (an answer from an AI tool): each token comes back in the main form of
  its value. A name written in capitals in the original may come back in normal case.
- **Unknown tokens** and **altered tokens** are listed (section 5).

Under **Download**, save the files you need (section 6). **Start a new document** erases the
current session after a confirmation (**Yes, start a new document**). **Back to Review**
returns to the review.

The **Evaluation** page shows the measured results of the detection; **Method & limits**
explains how HuisClos works.

![Evaluation page](screenshots/06_evaluation.png)

## 4. Settings in the left column

- **Types to detect**: the kinds of values HuisClos looks for. Remove a type only if you are
  sure the document does not need it. **Place** is off by default, because place names are
  rarely identifying on their own and masking them makes the text harder to use.
- **Confidence threshold**: each detection has a score. HuisClos keeps the detections whose
  score reaches the threshold. A lower threshold masks more text and misses fewer values; a
  higher threshold masks less text but may miss names. The default, 0.30, is the threshold
  selected on the development corpus (see `results/summary.md`); it is also the lowest
  value. Keep it unless you have a reason to change it.
- **Token style**: **French labels [PERSONNE_1]** or **English labels [PERSON_1]**. Choose
  English labels if you write to the AI tool in English.
- **Language**: **English** or **Français** for the interface.
- **Reset session**: erases the text, the detections and the mapping table, after
  confirmation (**Yes, reset** or **Cancel**).

Choose the settings before you click **Detect sensitive data**. If you change them later, go
back to Import and run the detection again.

## 5. Working with ChatGPT, Claude or Mistral

Send the pseudonymized text and your question. Add one of the recommended instructions shown
in the application, so that the AI tool keeps the tokens unchanged:

- In French: "Conserve exactement chaque jeton entre crochets, par exemple [PERSONNE_1], sans
  le modifier ni le traduire, et n'en invente aucun."
- In English: "Keep every bracketed token exactly as written, for example [PERSON_1]; do not
  change, translate or invent tokens."

After **Restore**, HuisClos may show three messages:

- **Altered tokens were recognized and restored**: the AI tool wrote a token differently, for
  example in lower case. HuisClos restored it. Check these places.
- **Unknown tokens were left unchanged**: the token is not in the mapping table. Either the AI
  tool invented it, or you loaded the mapping table of another document. Check that the table
  matches the document. Otherwise, ask the AI tool to use only the tokens of the text, or
  complete the passage by hand. Never send the mapping table to the AI tool to solve this.
- **Tokens of the table not found in the answer**: normal when the answer is a summary.

Your AI tool's account settings still apply: check whether your conversations may be used to
train its models.

**Mistral connector (optional).** HuisClos can send the pseudonymized text to Mistral
directly. The block **Send to Mistral (optional)** appears only if an API key is configured.
In PowerShell, set it in the same window before the start command:

```powershell
$env:MISTRAL_API_KEY = "your-key"
```

Then write your instruction, tick **I confirm that only the pseudonymized text above will be
sent** and click **Send to Mistral**. The answer is placed in the Restore step. On Mistral's
free Experiment plan, requests may be used to train Mistral's models: use fictitious data
only.

## 6. Exported files and security rules

| File | Contains | Rule |
| --- | --- | --- |
| Pseudonymized text (.txt, .docx) | Tokens instead of values | May be sent to an AI tool after you have read it |
| Restored text (.txt, .docx) | Real values | Client document: store it with the client file |
| Mapping table (.mapping.json) | Every token and its real value | Sensitive: keep it on your computer |

Rules for the mapping table:

- Never send it to an AI tool, and never send it by email or chat.
- Store it with the client file, where only authorized people can read it.
- HuisClos does not keep it. Download it if you will receive the answer later; to restore
  that answer, upload it under **Use a saved mapping table (optional)**. In a new session,
  Restore is locked until Import and Review are complete. Click **Load sample case**, then
  **Detect sensitive data**, then **Pseudonymize** to open Restore. Upload your saved table
  there, paste the answer for your original document, and click **Restore**. Download only
  the restored answer: the sample's pseudonymized text and mapping table do not belong to
  your original document.
- Delete it when you no longer need it.

The browser saves the files in your usual downloads folder.

## 7. Troubleshooting

**"running scripts is disabled on this system" (PowerShell).** This appears only if you run
`.venv\Scripts\Activate.ps1`. The commands of this guide do not need it. If you want to
activate the environment anyway, allow scripts for the current window only, then activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

**"python is not recognized".** The box **Add python.exe to PATH** was not ticked. Run the
Python installer again, choose **Modify**, then tick **Add Python to environment variables**.
You can also use the Python launcher instead of `python`:

```powershell
py -3.12 -m venv .venv
```

**Port 8501 is already used.** HuisClos (or another Streamlit application) is already
running. Streamlit then opens on the next free port and shows it in the window, for example
`Local URL: http://localhost:8502`. Use that address, or stop the other window with Ctrl+C
and start again. To find which program uses port 8501, or to choose the port yourself:

```powershell
netstat -ano | findstr :8501
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address localhost --server.port 8502
```

**"The detection engine could not start".** The French language model is missing. Check it:

```powershell
.venv\Scripts\python.exe -c "import fr_core_news_md; print('ok')"
```

If this command shows an error instead of `ok`, run the installation command again, with an
internet connection: `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

**"DLL load failed" with "file name too long" (Windows).** The HuisClos folder is too deep
in your folders: Windows limits the length of file paths. Move the folder to a short
location, for example directly in Documents, delete its `.venv` folder, and repeat step 5 of
the installation.

**"This PDF has no selectable text".** The PDF is a scan (an image). HuisClos does not read
images. Convert it with an OCR tool, then upload the result or paste its text. Check the
converted text: OCR errors can hide names from the detection.

**The online demo shows a sleeping page.** The hosted demo goes to sleep when nobody uses it.
Click the button on the page to wake it up and wait a few minutes. The first detection then
takes longer, because the language model is loaded. Remember: fictitious data only online.

**The computer slows down or HuisClos stops.** The French language model needs several
hundred megabytes of memory. Close other programs, process long documents in parts, and
restart HuisClos.

## 8. Frequently asked questions

**Does my document leave my computer?** With a local installation, processing stays on your
computer. You decide whether to copy the pseudonymized text to an AI tool. The optional
Mistral connector sends that text and your instruction after an explicit confirmation.
On the online demo, the original text passes through the host's server.

**Is the pseudonymized text anonymous?** No. The facts of the case can still identify a
person. Pseudonymized data remain personal data under the GDPR.

**Can I use the online demo with a real file?** No. Online, the text passes through the
server of the host. Install HuisClos on your computer for real files.

**Does HuisClos keep my documents?** HuisClos does not save them to disk. The text, the
detections and the mapping table are held in session memory. Closing a tab does not
guarantee immediate removal from server memory. To clear the current session explicitly, use
**Reset session** or
**Start a new document** and confirm; stop the local server with Ctrl+C when finished.

**Why is a word masked when it should not be?** The detection prefers masking too much to
missing a name. Uncheck **Mask** for that row in the Review step.

**Can I restore an answer received days later?** Yes, if you downloaded the mapping table.
Follow the new-session workaround in section 6, then upload it under
**Use a saved mapping table (optional)** in the Restore step.

**Which files are accepted?** .txt, .docx and .pdf with selectable text, in French.

## 9. Uninstalling

1. Stop HuisClos (Ctrl+C in its window).
2. Delete the HuisClos folder. It contains the program and its environment (`.venv`). Python,
   browser downloads, and caches or settings created by pip and Streamlit outside that folder
   are separate and may remain.
3. Before deleting, move any mapping table or restored text you want to keep out of your
   downloads folder into the client file, or delete them.
4. To remove Python as well: on Windows, open Settings, Apps, Installed apps, and uninstall
   "Python 3.12"; on macOS, delete the "Python 3.12" folder in Applications.
