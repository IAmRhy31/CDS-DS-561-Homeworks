from flask import Flask
from google.cloud.sql.connector import Connector
import sqlalchemy
import apache_beam as beam
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
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

data_list_2 = []

def fetch_data():
    with pool.connect() as db_conn:
        result = db_conn.execute(sqlalchemy.text("SELECT age, gender, income FROM User_Details"))
        data = [{"age": row[0], "gender": row[1], "income": row[2]} for row in result]
    return data

class Printer(beam.DoFn):
    def process(self, element):
        data_list_2.append(element)
        yield element

with beam.Pipeline() as pipeline:
    input_data = pipeline | "Create PCollections" >> beam.Create(fetch_data())
    client_country_data = (
        input_data
        | "Extract Age, Gender and Income" >> beam.Map(lambda x: (x["age"], x["gender"], x["income"]))
        | "Print elements" >> beam.ParDo(Printer())
    )

    pipeline.run()

df = pd.DataFrame(data_list_2, columns=['age', 'gender', 'income'])

data = pd.get_dummies(df, columns=['gender'], drop_first=True)

label_encoder = LabelEncoder()
data['gender'] = label_encoder.fit_transform(df['gender'])
data['age'] = label_encoder.fit_transform(df['age'])

def convert_income_ranges(income_range):
    income_groups = {
        '0-10k': 'Low',
        '10k-20k': 'Low',
        '20k-40k': 'Medium',
        '40k-60k': 'Medium',
        '60k-100k': 'Medium',
        '100k-150k': 'High',
        '150k-250k': 'High',
        '250k+': 'High'
    }
    return income_groups.get(income_range, 'Unknown')

data['income_group'] = df['income'].apply(convert_income_ranges)

X = data[['age', 'gender_Male']]
y = data['income_group']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = DecisionTreeClassifier()

clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print(f"Model 2 - Decision Tree : Test Accuracy = {accuracy * 100:.2f}%")
