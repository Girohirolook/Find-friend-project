from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from .database import Base


class LikedUser(Base):
    __tablename__ = 'liked_users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    liked_card_id = Column(Integer, ForeignKey('cards.id'))
    is_checked = Column(Boolean, default=False)

    liked_card = relationship('Card', foreign_keys=[liked_card_id])
    user = relationship('User', foreign_keys=[user_id])

