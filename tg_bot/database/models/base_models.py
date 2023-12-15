from typing import Any

from asyncpg import UniqueViolationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declared_attr, DeclarativeBase

from tg_bot.exceptions.db import DBException


class Base(DeclarativeBase):
    id: Any
    __name__: str
    # Generate __tablename__ automatically

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()

    async def save(self, db_session: AsyncSession):
        """

        :param db_session:
        :return:
        """
        try:
            db_session.add(self)
            return await db_session.commit()
        except SQLAlchemyError as ex:
            raise DBException(repr(ex)) from ex

    def save_sync(self, db_session):
        """

        :param db_session:
        :return:
        """
        try:
            db_session.add(self)
            return db_session.commit()
        except SQLAlchemyError as ex:
            raise DBException(repr(ex)) from ex

    async def delete(self, db_session: AsyncSession):
        """

        :param db_session:
        :return:
        """
        try:
            await db_session.delete(self)
            await db_session.commit()
            return True
        except SQLAlchemyError as ex:
            raise DBException(repr(ex)) from ex

    async def update(self, db: AsyncSession, **kwargs):
        """

        :param db:
        :param kwargs
        :return:
        """
        try:
            for k, v in kwargs.items():
                setattr(self, k, v)
            return await db.commit()
        except SQLAlchemyError as ex:
            raise DBException(repr(ex)) from ex

    async def save_or_update(self, db: AsyncSession):
        try:
            db.add(self)
            return await db.commit()
        except IntegrityError as ex:
            if isinstance(ex.orig, UniqueViolationError):
                return await db.merge(self)
            else:
                raise DBException(repr(ex)) from ex
        finally:
            await db.close()
