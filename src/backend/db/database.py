from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL
from backend.db.models import Base, WebSearch, WebPage


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


def get_web_search(query: str) -> WebSearch | None:
    with SessionFactory() as session:
        return session.scalar(
            select(WebSearch).where(WebSearch.query == query)
        )


def save_web_search(query: str, search_result: list) -> WebSearch:
    with SessionFactory() as session:
        brave_search = WebSearch(query=query, search_result=search_result)

        session.add(brave_search)
        session.commit()

        return brave_search
