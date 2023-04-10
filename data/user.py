from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from .database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    card_id = Column(Integer, ForeignKey('cards.id'))
    card = relationship('Card', foreign_keys=[card_id], uselist=False)
    # card = Card()
    # liked_cards = list[card]
    # watched_cards = list[card]