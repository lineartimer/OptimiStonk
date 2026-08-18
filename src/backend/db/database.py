from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL
from backend.db.models import Base, WebPage


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


def get_web_page(url: str) -> WebPage | None:
    with SessionFactory() as session:
        return session.scalar(select(WebPage).where(WebPage.url == url))


def save_web_page(url: str, content: str) -> WebPage:
    with SessionFactory() as session:
        web_page = WebPage(url=url, content=content)

        session.add(web_page)
        session.commit()

        return web_page

