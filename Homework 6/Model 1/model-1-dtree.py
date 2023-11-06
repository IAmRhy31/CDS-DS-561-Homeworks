from flask import Flask
from google.cloud.sql.connector import Connector
import sqlalchemy
import apache_beam as beam
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
import pandas as pd

app = Flask(__name__)

project_id = "ds-561-project-1"
region = "us-central1"
instance_name = "mysql-hw5-db"
INSTANCE_CONNECTION_NAME = f"{project_id}:{region}:{instance_name}" 
print(f"Your Instance Connection Name is: {INSTANCE_CONNECTION_NAME}")
DB_USER = "root"
DB_NAME = "hw5-db"
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

data_list = []

def fetch_data():
    with pool.connect() as db_conn:
        result = db_conn.execute(sqlalchemy.text("SELECT client_ip, country FROM Requests"))
        data = [{"client_ip": row[0], "country": row[1]} for row in result]
    return data

class Printer(beam.DoFn):
    def process(self, element):
        data_list.append(element)
        yield element

with beam.Pipeline() as pipeline:
    input_data = pipeline | "Create PCollections" >> beam.Create(fetch_data())
    client_country_data = (
        input_data
        | "Extract Client IP and Country" >> beam.Map(lambda x: (x["client_ip"], x["country"]))
        | "Print elements" >> beam.ParDo(Printer())
    )

    pipeline.run()

df = pd.DataFrame(data_list, columns=['client_ip', 'country'])

label_encoder = LabelEncoder()
df['client_ip'] = label_encoder.fit_transform(df['client_ip'])

label_encoder = LabelEncoder()
df['country'] = label_encoder.fit_transform(df['country'])

X = df.drop('country', axis=1)
y = df['country']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = DecisionTreeClassifier()

clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print(f"Model 1 - Decision Tree Classifier : Test Accuracy = {accuracy * 100:.2f}%")
