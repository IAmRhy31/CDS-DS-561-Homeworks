from google.cloud import pubsub_v1
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class SecondAppHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")
        print("400: Permission Denied! Received Pub/Sub Message:")
        print(post_data)
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()

def callback(message):
    print(f"400: Permission Denied! Received Pub/Sub Message: {message.data}")
    message.ack()

project_id = "ds-561-project-1"
subscription_name = "hw10-topic"
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_name)

if __name__ == "__main__":
    server_address = ("localhost", 8082)  
    httpd = HTTPServer(server_address, SecondAppHandler)
    print("Second App is listening on", server_address)

    subscriber.subscribe(subscription_path, callback=callback)
    print(f"Listening for messages on {subscription_path}.")
    httpd.serve_forever()