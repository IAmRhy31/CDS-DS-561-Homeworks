import functions_framework
from flask import Flask, request
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud import pubsub_v1
import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()

app = Flask(__name__)
bucket_name = "hw2-rhythm"
folder_name = "generated-content"

banned_countries = ["North Korea", "Iran", "Cuba", "Myanmar", "Iraq", "Libya", "Sudan", "Zimbabwe", "Syria"]

project_id = "ds-561-project-1"
topic_name = "hw-3"
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

@functions_framework.http
def serve_file(request):
    if request.method != "GET":
        logging.error("501: Method not implemented")
        return "501: Method not implemented", 501

    file_path = request.path
    path_components = file_path.lstrip('/').split('/')
    
    if len(path_components) != 3:
        logging.error("400: Invalid path format")
        return "400: Invalid path format", 400
    
    country = request.headers.get("X-country")
    if country in banned_countries:
        message_data = {"Country": country}
        message_id = publisher.publish(topic_path, data=str(message_data).encode("utf-8"))
        print(f"Published message {message_id} to {topic_path}.")
        return "Hey! I got a request from one of the forbidden countries.", 400
    
    bucket_name, folder_name, file_name = path_components
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
    app.run(host="0.0.0.0", port=8080)