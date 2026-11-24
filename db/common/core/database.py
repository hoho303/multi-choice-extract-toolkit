from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker

class DatabaseConnector:
    def __init__(self, config: dict, database_type: str = "postgres"):
        self.config = config
        self.engine = None
        self.database_type = database_type

        self.username = self.config["username_db"]
        self.password = self.config["password_db"]
        self.host = self.config["host_db"]
        self.port = self.config["port_db"]
        self.dbname = self.config["database"]

        if self.database_type == "postgres":
            self.connection_string = (
                f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.dbname}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    def start(self):
        self.engine = create_engine(self.connection_string, pool_size=20, max_overflow=40)
        print(f"{self.database_type} engine created successfully.")

    def get_engine(self):
        return self.engine
    

    def get_session(self):
        return sessionmaker(bind=self.engine)

    def execute_raw_query(self, raw_query: str, kwargs: dict):
        try:
            query = text(raw_query)
            with self.engine.begin() as conn: 
                result = conn.execute(query, kwargs)
                return result.fetchall()
        except Exception as e:
            print(e)
            return None

    def stop(self):
        self.engine.dispose()
