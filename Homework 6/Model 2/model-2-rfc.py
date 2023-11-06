from flask import Flask
from google.cloud.sql.connector import Connector
import sqlalchemy
import apache_beam as beam
from sklearn.ensemble import RandomForestClassifier
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

data_list_2 = []

def fetch_data_user_details():
    with pool.connect() as db_conn:
        result = db_conn.execute(sqlalchemy.text("SELECT gender, age, income FROM User_Details"))
        data = [{"gender": row[0], "age": row[1], "income": row[2]} for row in result]
    return data

class PrinterUserDetails(beam.DoFn):
    def process(self, element):
        data_list_2.append(element)
        yield element

with beam.Pipeline() as pipeline:
    input_data_user_details = pipeline | "Create PCollections User Details" >> beam.Create(fetch_data_user_details())
    gender_age_income_data = (
        input_data_user_details
        | "Extract Gender, Age and Income" >> beam.Map(lambda x: (x["gender"], x["age"], x["income"]))
        | "Print elements User Details" >> beam.ParDo(PrinterUserDetails())
    )

    pipeline.run()

df2 = pd.DataFrame(data_list_2, columns=['gender', 'age', 'income'])

label_encoder = LabelEncoder()
df2['gender'] = label_encoder.fit_transform(df2['gender'])
df2['age'] = label_encoder.fit_transform(df2['age'])

X2 = df2[['gender', 'age']].values
y2 = df2['income'].values

classifiers = [
    RandomForestClassifier(n_estimators=200, max_depth=None)
]

for clf in classifiers:

    clf.fit(X2, y2)
    
    predictions = clf.predict(X2)
    
    accuracy = accuracy_score(y2, predictions)
    
    print(f"Model 2 - Random Forest Classifier : Test Accuracy = {accuracy * 100:.2f}%")
    