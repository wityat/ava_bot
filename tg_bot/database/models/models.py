from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, select, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from tg_bot.database.models.base_models import Base
from tg_bot.exceptions.db import DBException


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    phone = Column(String(15), unique=True, nullable=True)  # Поле для телефона, предполагается уникальным
    accepted_terms = Column(Boolean, default=False, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    generation_jobs = relationship('GenerationJob', back_populates='user')

    def __repr__(self):
        return (f"<User(id={self.id}, tg_id='{self.tg_id}', phone='{self.phone}', "
                f"accepted_terms={self.accepted_terms}, is_banned={self.is_banned})>")

    @classmethod
    async def get(cls, db_session: AsyncSession, tg_id: int):
        """

        :param db_session:
        :param id:
        :return:
        """
        stmt = select(cls).where(cls.tg_id == tg_id)
        result = await db_session.execute(stmt)
        instance = result.scalars().first()
        if instance is None:
            raise DBException(
                f"There is no User for requested id: {tg_id}"
            )
        else:
            return instance


class GenerationJob(Base):
    __tablename__ = 'generation_job'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    text = Column(String)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    user = relationship('User', back_populates='generation_jobs')

    face_image = relationship("FaceImage", uselist=False, back_populates="generation_job")
    generated_image = relationship("GeneratedImage", uselist=False, back_populates="generation_job")
    final_image = relationship("FinalImage", uselist=False, back_populates="generation_job")

    @classmethod
    async def get(cls, db_session: AsyncSession, id: int):
        """

        :param id:
        :param db_session:
        :return:
        """
        stmt = select(cls).where(cls.id == id)
        result = await db_session.execute(stmt)
        instance = result.scalars().first()
        if instance is None:
            raise DBException(
                f"There is no GenerationJob for requested id: {id}"
            )
        else:
            return instance


class GeneratedImage(Base):
    __tablename__ = 'generated_images'
    id = Column(Integer, primary_key=True)
    file_id = Column(String, unique=True, nullable=False)
    generation_job_id = Column(Integer, ForeignKey('generation_job.id', ondelete='CASCADE'))
    generation_job = relationship("GenerationJob", back_populates="generated_image", uselist=False)


class FaceImage(Base):
    __tablename__ = 'face_images'
    id = Column(Integer, primary_key=True)
    file_id = Column(String, unique=True, nullable=False)
    generation_job_id = Column(Integer, ForeignKey('generation_job.id', ondelete='CASCADE'))
    generation_job = relationship("GenerationJob", back_populates="face_image", uselist=False)


class FinalImage(Base):
    __tablename__ = 'final_images'
    id = Column(Integer, primary_key=True)
    file_id = Column(String, unique=True, nullable=False)
    generation_job_id = Column(Integer, ForeignKey('generation_job.id', ondelete='CASCADE'))
    generation_job = relationship("GenerationJob", back_populates="final_image", uselist=False)
