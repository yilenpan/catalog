from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Sport, SportItem

DATA = [
{'item':'shoes', 'category':'running', 'desc':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus nisi debitis ipsa illum distinctio laudantium facilis necessitatibus, eius sit suscipit alias dolorem voluptate dicta explicabo placeat eos ducimus adipisci consequatur!'},
{'item':'bat', 'category':'baseball', 'desc':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus nisi debitis ipsa illum distinctio laudantium facilis necessitatibus, eius sit suscipit alias dolorem voluptate dicta explicabo placeat eos ducimus adipisci consequatur!'},
{'item':'speedo', 'category':'swimming', 'desc':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus nisi debitis ipsa illum distinctio laudantium facilis necessitatibus, eius sit suscipit alias dolorem voluptate dicta explicabo placeat eos ducimus adipisci consequatur!'},
{'item':'gloves', 'category':'boxing', 'desc':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus nisi debitis ipsa illum distinctio laudantium facilis necessitatibus, eius sit suscipit alias dolorem voluptate dicta explicabo placeat eos ducimus adipisci consequatur!'},
{'item':'car', 'category':'racing', 'desc':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus nisi debitis ipsa illum distinctio laudantium facilis necessitatibus, eius sit suscipit alias dolorem voluptate dicta explicabo placeat eos ducimus adipisci consequatur!'},
{'item':'board', 'category':'snow boarding', 'desc':'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusamus nisi debitis ipsa illum distinctio laudantium facilis necessitatibus, eius sit suscipit alias dolorem voluptate dicta explicabo placeat eos ducimus adipisci consequatur!'}
]

engine = create_engine('sqlite:///sportsitems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

for item in DATA:
    sport = Sport(name=item['category'])
    session.add(sport)
    session.commit()
    item = SportItem(name=item['item'], description=item['desc'], sport=sport)
    session.add(item)
    session.commit()

sports = session.query(Sport).all()
print sports


