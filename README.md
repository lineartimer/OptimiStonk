OptimiStonk
===========

An agentic app striving for alpha.

# Running the app locally

- Fork the repo, then clone it onto your computer
- Create a .env file with the following content:

OPENAI_API_KEY="<Your OpenAI API key>"

BRAVE_API_KEY="<Your Brave API key>"

EDGAR_IDENTITY="<Your name> <Your email>"

- Run scripts/init-repo.command
- Then open OptimiStonk.code-workspace in VS Code
- Hit F5
- It takes some time to run the app the first time
- Open http://127.0.0.1:8000 in a browser

## Troubleshooting

- Set the correct python interpreter in VS Code: Ctrl + Shift + P -> Python: Select Interpreter -> .venv/bin/python
- If pylance erronously underlines a module import, restart VS Code
- To create/activate/deactivate a virtual environment:

python3 -m venv .venv
source .venv/bin/activate
deactivate