import os


BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
EMBEDDING_MODEL = "text-embedding-3-small"
