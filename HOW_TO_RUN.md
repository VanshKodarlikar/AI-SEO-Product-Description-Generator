# How to Run

## Requirements

- Windows with Python 3.10 or newer
- The Excel workbook `T47_SEO_Product_Description_Generator_COMPLETE.xlsx` in the same folder as `app.py`

## First-time setup

Open PowerShell in the project folder and run. This uses standard (non-free-threaded) Python 3.13, which has prebuilt wheels for the dependencies:

```powershell
py -3.13 -m venv .venv-standard
.\.venv-standard\Scripts\python.exe -m pip install -r requirements.txt
```

## Start the app

From the project folder, run:

```powershell
.\.venv-standard\Scripts\python.exe -m streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. Open that address in your browser.

## Generate content

- **Demo mode** works without an API key and uses the built-in template generator.
- **Gemini API** uses Gemini 2.5 Flash. Select that mode and enter your Google AI Studio API key in the app. Do not put the key in source code or commit it.

## Troubleshooting

- If the app reports that the product sheet could not be loaded, place `T47_SEO_Product_Description_Generator_COMPLETE.xlsx` beside `app.py`.
- If the `py` command is unavailable, install standard Python 3.13 and ensure the Python launcher is enabled. Avoid a free-threaded `3.13t` interpreter for this setup.
- To stop the local server, focus the PowerShell window running Streamlit and press `Ctrl+C`.