from flask import Flask, request
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud import pubsub_v1
import google.cloud.logging
import logging
from google.oauth2 import service_account

service_account_key = "hw9-key.json"
credentials = service_account.Credentials.from_service_account_file(service_account_key)
client = google.cloud.logging.Client(credentials=credentials)
client.setup_logging()

app = Flask(__name__)
bucket_name = "hw2-rhythm"
folder_name = "generated-content"

banned_countries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq", "Libya", "Sudan", "Zimbabwe", "Syria"]

project_id = "ds-561-project-1"
topic_name = "hw-3"
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(project_id, topic_name)

@app.route("/", methods=['GET'])
def usage():
    return "Welcome to the file server! To retrieve a file, use the following URL format: /bucket_name/folder_name/file_name", 200, {"Content-Type": "text/html"}

@app.route("/<bucket_name>/<folder_name>/<file_name>", methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH'])
def serve_file(bucket_name, folder_name, file_name):
    if request.method != "GET":
        logging.error("501: Method not implemented")
        return "501: Method not implemented", 501

    country = request.headers.get("X-country")
    if country in banned_countries:
        message_data = {"Country": country}
        message_id = publisher.publish(topic_path, data=str(message_data).encode("utf-8"))
        return "Hey! I got a request from one of the forbidden countries.", 403

    storage_client = storage.Client.create_anonymous_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f"{folder_name}/{file_name}")

    try:
        file_contents = blob.download_as_text()
    except NotFound:
        logging.error("404: File not found")
        return "404: File not found", 404
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return "500: Internal Server Error", 500

    return file_contents, 200, {"Content-Type": "text/html"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)