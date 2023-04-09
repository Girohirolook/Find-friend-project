from sqlalchemy import Column, Integer, String
from .database import Base


class Card(Base):
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True)
    name = Column()
    about = Column()
    tags = Column()
    contacts = Column()
    # Image
    # description
    # Liked games
    # contacts