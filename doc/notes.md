python3 -m venv .venv
source .venv/bin/activate
deactivate

pip install -r requirements.txt

VS Code: Ctrl + Shift + P -> Python: Select Interpreter -> .venv/bin/python

If pylance erronously underlines a module import, restart VS Code

python backend/main.py

http://127.0.0.1:8000