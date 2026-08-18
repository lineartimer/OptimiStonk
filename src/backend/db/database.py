from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.db.models import Base, WebPage


DATABASE_PATH = Path(__file__).resolve().parents[2] / "database.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_web_page(url: str) -> WebPage | None:
    with SessionLocal() as session:
        return session.scalar(select(WebPage).where(WebPage.url == url))


def save_web_page(url: str, markdown_content: str) -> WebPage:
    with SessionLocal() as session:
        web_page = WebPage(url=url, markdown_content=markdown_content)
        session.add(web_page)
        session.commit()
        return web_page

