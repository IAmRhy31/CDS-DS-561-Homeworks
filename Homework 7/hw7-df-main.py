import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import storage
from bs4 import BeautifulSoup
import logging

def addKey(row):
    return (1, row)

def print_stats(element):
    stat_in, stat_out = element
    return (stat_in, stat_out)

def sortGroupedData(row):
    (keyNumber, sortData) = row
    sortData.sort(key=lambda x: x[1], reverse=True)
    return sortData[0:5]

def run_cloud_dataflow():
    options = PipelineOptions()
    options.view_as(beam.options.pipeline_options.StandardOptions).runner = "DataflowRunner"
    options.view_as(beam.options.pipeline_options.GoogleCloudOptions).project = "ds-561-project-1"
    options.view_as(beam.options.pipeline_options.GoogleCloudOptions).region = "us-central1"
    options.view_as(beam.options.pipeline_options.GoogleCloudOptions).job_name = "hw7-job-dataflow"
    options.view_as(beam.options.pipeline_options.GoogleCloudOptions).temp_location = "gs://hw2-rhythm/generated-content/temp"
    options.view_as(beam.options.pipeline_options.GoogleCloudOptions).staging_location = "gs://hw7-rhythm/staging"

    output_path = "gs://hw7-rhythm/"
    result_incoming = output_path + "df_result_incoming.txt"
    result_outgoing = output_path + "df_result_outgoing.txt"

    with beam.Pipeline(options=options) as pipeline:
        storage_client = storage.Client.create_anonymous_client()
        bucket_name = "hw2-rhythm"
        folder_name = "generated-content/"
        bucket = storage_client.bucket(bucket_name)

        file_count = 10000
        stat_in = [["", 0] for _ in range(file_count)]
        stat_out = [["", 0] for _ in range(file_count)]

        logging.info("Stats getting built...")

        for page_id in range(file_count):
            filename = str(page_id) + '.html'
            blob = bucket.blob(folder_name + filename)

            html_content = blob.download_as_text(encoding='utf-8')

            page_index = int(filename[:-5])
            soup = BeautifulSoup(html_content, 'html.parser')

            for link in soup.findAll('a'):
                href = link.get('href')
                linked_page_index = int(href[:-5])

                # Outgoing  
                stat_out[page_index][0] = filename  
                stat_out[page_index][1] += 1  

                # Incoming
                stat_in[linked_page_index][0] = href  
                stat_in[linked_page_index][1] += 1  

        logging.info("Pipelines processing...")

        files_incoming = (
            pipeline
            | "Create input incoming" >> beam.Create(stat_in)
            | 'AddKeyIn' >> beam.Map(addKey)
            | 'GroupByKeyIn' >> beam.GroupByKey()
            | 'SortGroupedDataIn' >> beam.Map(sortGroupedData)
            | 'Write sortIn' >> beam.io.WriteToText(result_incoming)
        )

        files_outgoing = (
            pipeline
            | "Create input outgoing" >> beam.Create(stat_out)
            | 'AddKeyOut' >> beam.Map(addKey)
            | 'GroupByKeyOut' >> beam.GroupByKey()
            | 'SortGroupedDataOut' >> beam.Map(sortGroupedData)
            | 'Write sortOut' >> beam.io.WriteToText(result_outgoing)
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_cloud_dataflow()
