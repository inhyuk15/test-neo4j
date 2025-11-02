from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "1234aaaa" 

def create_sample_data(tx):
    tx.run("""
CREATE (a:Person {name: 'Alice', age: 30})
CREATE (b:Person {name: 'Bob', age: 25})
CREATE (c: City {name: 'Seoul'})
CREATE (a)-[:FRIEND_WITH]->(b)
CREATE (a)-[:LIVES_IN]->(c)
    """)
    

def print_people(tx):
    result = tx.run('MATCH (p:Person) RETURN p.name AS name, p.age as age')
    for record in result:
        print(f'{record['name']} ({record['age']})')

def delete_all(tx):
    tx.run('match (n) detach delete n')


def test():
    driver = GraphDatabase.driver(uri, auth=(user, password))
    print(f'driver: {driver}')

    with driver.session(database="neo4j") as session:
        # session.execute_write(create_sample_data)
        session.execute_write(delete_all)
        session.execute_read(print_people)

    driver.close()
