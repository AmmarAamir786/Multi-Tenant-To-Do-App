from sqlmodel import SQLModel, create_engine, Session
from multi_tenant_to_do_app import setting

#step 7: Create Engine
    # Engine is used to establish the connection between our app and our db (neon)
    # Engine is one for whole application
    # Psycopg translates Python code and data structures into commands and data formats that PostgreSQL understands, enabling seamless interaction between your application and the database.
connection_string: str = str(setting.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args={"sslmode":"require"}, pool_recycle=300, pool_size=10, echo=True) 
    #sslmode will make the connection secure. Echo shows all the steps performed in the terminal

#step 8: create tables
def create_tables():
    SQLModel.metadata.create_all(engine)

#step 9: create session
    # for every fuction/transaction there will be a new session
    # E.g for every new logged in user, a new session is made
    # when user logs out, session closes
    # we are creating our session in a generator function so it closes the session automatically whenever we dont need it
def get_session():
    with Session(engine) as session:
        yield session