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
    # Image
    # description
    # Liked games
    # contacts