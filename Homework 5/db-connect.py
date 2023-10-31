from google.cloud.sql.connector import Connector
import sqlalchemy

INSTANCE_CONNECTION_NAME = "ds-561-project-1:us-central1:mysql-hw5-db"
DB_USER = "root"
DB_PASS = "admin"
DB_NAME = "hw5-db"

# Initialize Connector object
connector = Connector()

# Function to return the database connection object
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# Create a connection pool with the 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# Connect to the connection pool
with pool.connect() as db_conn:
    # Execute creation of the tables
    db_conn.execute(
        sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS Requests ("
            "request_id INT AUTO_INCREMENT PRIMARY KEY,"
            "country VARCHAR(255),"
            "is_banned BOOLEAN,"
            'client_ip VARCHAR(255),'
            "time_of_day TIMESTAMP,"
            "requested_file VARCHAR(255)  );"
        )
    )

    db_conn.execute(
        sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS User_Details ("
            "user_id INT AUTO_INCREMENT PRIMARY KEY,"
            "gender VARCHAR(10),"
            "age VARCHAR(20),"
            "income VARCHAR(20),"
            "request_id INT,"
            "FOREIGN KEY (request_id) REFERENCES Requests(request_id)  );"
        )
    )

    db_conn.execute(
        sqlalchemy.text(
            "CREATE TABLE IF NOT EXISTS Errors ("
            "error_id INT AUTO_INCREMENT PRIMARY KEY,"
            "time_of_day TIMESTAMP,"
            "requested_file VARCHAR(255),"
            "error_code INT,"   
            "request_id INT,"         
            "FOREIGN KEY (request_id) REFERENCES Requests(request_id)  );"
        )
    )

    # Get metadata about the tables
    meta = sqlalchemy.MetaData()
    meta.reflect(bind=db_conn)

    # Retrieve table names
    table_names = meta.tables.keys()
    print("Table names in the database:")
    for table_name in table_names:
        print(table_name)
