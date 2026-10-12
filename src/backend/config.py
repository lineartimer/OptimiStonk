import os


BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
