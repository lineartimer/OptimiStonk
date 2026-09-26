OptimiStonk
===========

An agentic app striving for alpha.

# Running the app locally

- Clone the repo on your computer
- Create a .env file with the following content:

```dotenv
OPENAI_API_KEY="<Your OpenAI API key>"
BRAVE_API_KEY="<Your Brave API key>"
EDGAR_IDENTITY="<Your name> <Your email>"
```

- Run scripts/init-repo.command
- Then run scripts/run.command

Or to debug the app:
- Open OptimiStonk.code-workspace in VS Code
- Hit F5
- It takes some time to run the app the first time
- Open http://127.0.0.1:3000 in a browser
