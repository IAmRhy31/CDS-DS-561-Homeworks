from flask import Flask, request
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud.exceptions import NotFound
from google.cloud.sql.connector import Connector
import sqlalchemy
import google.cloud.logging
import logging
import datetime

app = Flask(__name__)

project_id = "ds-561-project-1"
bucket_name = "hw10-rhythm"
folder_name = "generated-content"
topic_name = "hw10-topic"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

banned_countries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq", "Libya", "Sudan", "Zimbabwe", "Syria"]

client = google.cloud.logging.Client()
client.setup_logging()

region="us-east1"
instance_name = "hw10-gdm-instance"
INSTANCE_CONNECTION_NAME = f"{project_id}:{region}:{instance_name}" 
print(f"Your Instance Connection Name is: {INSTANCE_CONNECTION_NAME}")
DB_USER = "root"
DB_NAME = "hw10-db"
DB_PASS = "admin"

connector = Connector()

def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

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

def log_request_to_db(request_data):
    with pool.connect() as db_conn:
        try:
            insert_request_query = sqlalchemy.text(
                "INSERT INTO Requests (country, is_banned, client_ip, time_of_day, requested_file) "
                "VALUES (:country, :is_banned, :client_ip, :time_of_day, :requested_file)"
            )

            request_details = db_conn.execute(insert_request_query, parameters={
                "country": request_data.get("country"),
                "is_banned": request_data.get("is_banned"),
                "client_ip": request_data.get("client_ip"),
                "time_of_day": request_data.get("time_of_day"),
                "requested_file": request_data.get("requested_file")
            })
            db_conn.commit()

            last_id = request_details.lastrowid

            insert_user_details_query = sqlalchemy.text(
                "INSERT INTO User_Details (gender, age, income, request_id) "
                "VALUES (:gender, :age, :income, :request_id)"
            )

            db_conn.execute(insert_user_details_query, parameters={
                "gender": request_data.get("gender"),
                "age": request_data.get("age"),
                "income": request_data.get("income"),
                "request_id": last_id
            })
            db_conn.commit()

        except Exception as e:
            logging.error(f"Exception: {str(e)}")
            return "500: Internal Server Error", 500

def log_error_to_db(error_data):
    with pool.connect() as db_conn:
        try:
            insert_error_query = sqlalchemy.text(
                "INSERT INTO Errors (time_of_day, requested_file, error_code) "
                "VALUES (:time_of_day, :requested_file, :error_code)"
            )

            db_conn.execute(insert_error_query, parameters={
                "time_of_day": error_data.get("time_of_day"),
                "requested_file": error_data.get("requested_file"),
                "error_code": error_data.get("error_code")
            })
            db_conn.commit()

        except Exception as e:
            logging.error(f"Exception: {str(e)}")
            return "500: Internal Server Error", 500


@app.route("/", methods=['GET'])
def usage():
    return "Welcome to the file server! To retrieve a file, use the following URL format: /bucket_name/folder_name/file_name", 200, {"Content-Type": "text/html"}

@app.route("/<bucket_name>/<folder_name>/<file_name>", methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def serve_file(bucket_name, folder_name, file_name):
    if request.method != "GET":
        error_data = {
            "time_of_day": datetime.datetime.now(),
            "requested_file": file_name,
            "error_code": 501
        }
        log_error_to_db(error_data)
        logging.error("501: Method not implemented")
        return "501: Method not implemented", 501

    country = request.headers.get("X-country" , "unknown")
    gender = request.headers.get("X-gender")
    age = request.headers.get("X-age")
    income = request.headers.get("X-income")
    time_of_day = request.headers.get("X-time")

    if country in banned_countries:
        message_data = {"Country": country}
        message_id = publisher.publish(topic_path, data=str(message_data).encode("utf-8"))
        error_data = {
            "time_of_day": datetime.datetime.now(),
            "requested_file": file_name,
            "error_code": 403 
        }
        log_error_to_db(error_data)
        return "Hey! I got a request from one of the forbidden countries.", 403

    storage_client = storage.Client.create_anonymous_client()
    blob = storage_client.bucket(bucket_name).blob(f"{folder_name}/{file_name}")

    try:
        file_contents = blob.download_as_text()
    except Exception as e:
        error_data = {
            "time_of_day": datetime.datetime.now(),
            "requested_file": file_name,
            "error_code": 404  
        }
        log_error_to_db(error_data)
        logging.error("404: File not found")
        return "404: File not found", 404

    request_data = {
        "country": country,
        "client_ip": request.remote_addr,
        "is_banned": country in banned_countries,
        "time_of_day": time_of_day,
        "requested_file": file_name,
        "gender": gender,
        "age": age,
        "income": income,
    }
    log_request_to_db(request_data)

    return file_contents, 200, {"Content-Type": "text/html"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

