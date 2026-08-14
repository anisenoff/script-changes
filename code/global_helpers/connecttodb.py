import psycopg2
import psycopg2.extras as extras


def connect_to_db():
    return psycopg2.connect(database="downstream", 
                        user='nisenoff', 
                        password='ElevenChanceHidden', 
                        host='127.0.0.1', 
                        port= '5432')