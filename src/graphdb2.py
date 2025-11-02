from neomodel import StructuredNode, StringProperty, IntegerProperty, RelationshipTo, config

config.DATABASE_URL = 'bolt://neo4j:1234aaaa@localhost:7687'


class Person(StructuredNode):
    name = StringProperty(unique_index=True)
    age = IntegerProperty()
    friends = RelationshipTo('Person', 'FRIEND_WITH')

def test2():
    alice = Person(name='alice', age=30).save()
    bob = Person(name='Bob', age=25).save()

    alice.friends.connect(bob)



# for friend in alice.friends:
#     print