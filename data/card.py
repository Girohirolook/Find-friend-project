from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    about = Column(String)
    tags = Column(String)
    contacts = Column(String)
    liked_users_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    watched_users_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    liked_users = relationship('User', foreign_keys=[liked_users_id])
    watched_users = relationship('User', foreign_keys=[watched_users_id])
    # Image
    # description
    # Liked games
    # contacts