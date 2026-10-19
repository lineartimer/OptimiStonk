OptimiStonk
===========

OptimiStonk is an agentic app for discovering investment opportunities.

This is achieved by an automatic discovery process that
- Collects financial data from various sources (e.g. Edgar and Yahoo Finance) for the several thousand companies listed on NASDAQ and the NYSE
- Searches the web, reads web pages and extracts information from this data using AI agents
- Stores the financial data in a relational database along with a vector-based representation of financial reports to allow for RAG and semantic search
- Calculates a rank for each stock using common financial ratios that indicate financial strength and valuation
- Allows users to look at the results through an interactive dashboard

The project uses the following tech stack:
- LangChain
- LlamaIndex
- Fast API
- SqlAlchemy
- React/Next.js
- Recharts

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
- It will take a minute or so to start the app for the first time
- Open http://127.0.0.1:3000 in a browser
