import os
from datetime import datetime
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

AWS_CONN_ID = 'aws_default'
BUCKET_NAME = 'jungwoohan-temp-source-bucket'
FILE_NAME = 'temp.csv'

def task_s3_log_load():
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)

    # Get list of objects on a bucket
    keys = hook.list_keys(BUCKET_NAME)

    for key in keys:
        print(key)

        obj = hook.get_key(key, BUCKET_NAME)

        print(obj.bucket_name, obj.key)

def download_from_s3(key: str, bucket_name: str, local_path: str) -> str:
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)
    file_name = hook.download_file(key=key, bucket_name=bucket_name, local_path=local_path)
    return file_name

def rename_file(ti, new_name: str) -> None:
    downloaded_file_name = ti.xcom_pull(task_ids=['download_from_s3'])
    downloaded_file_path = '/'.join(downloaded_file_name[0].split('/')[:-1])
    os.rename(src=downloaded_file_name[0], dst=f"{downloaded_file_path}/{new_name}")

with DAG(
    dag_id='main',
    schedule_interval='@daily',
    start_date=datetime(2022, 3, 1),
    catchup=False
) as dag:
    task_1 = PythonOperator(
        task_id='s3_analysis',
        python_callable=task_s3_log_load,
        dag=dag
    )

    # Download a file
    task_download_from_s3 = PythonOperator(
        task_id='download_from_s3',
        python_callable=download_from_s3,
        op_kwargs={
            'key': FILE_NAME,
            'bucket_name': BUCKET_NAME,
            'local_path': './'
        }
    )

    # Rename the file
    task_rename_file = PythonOperator(
        task_id='rename_file',
        python_callable=rename_file,
        op_kwargs={
            'new_name': 'temp.csv'
        }
    )

    task_1 >> task_download_from_s3 >> task_rename_file
