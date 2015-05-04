from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()


class Sport(Base):
    __tablename__ = 'sport'
    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)


class SportItem(Base):
    __tablename__ = 'sport_item'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    sport_id = Column(Integer, ForeignKey('sport.id'))
    sport = relationship(Sport)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'sport': self.sport.name
        }


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


engine = create_engine('sqlite:///sportsitems.db')
Base.metadata.create_all(engine)
