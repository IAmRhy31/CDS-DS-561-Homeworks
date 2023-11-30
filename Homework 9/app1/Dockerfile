FROM python:3

RUN pip install --no-cache-dir Flask==2.2.5 \
    google-cloud-error-reporting==1.9.1 \
    google-cloud-storage==2.10.0 \
    google-cloud-pubsub==2.18.4 \
    google-cloud-logging==3.8.0

RUN wget -qO- https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz | tar -xz -C /usr/local
RUN /usr/local/google-cloud-sdk/install.sh

ENV PATH $PATH:/usr/local/google-cloud-sdk/bin

ENV GCS_BUCKET="app1-access"
ENV OBJECT_NAME_KEY="hw9-key.json"
ENV OBJECT_NAME_MAIN="main.py"

RUN gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME_KEY . && \
    gsutil cp gs://$GCS_BUCKET/$OBJECT_NAME_MAIN .

RUN gcloud auth activate-service-account --key-file=$OBJECT_NAME_KEY
EXPOSE 80

CMD [ "python3", "main.py" ]