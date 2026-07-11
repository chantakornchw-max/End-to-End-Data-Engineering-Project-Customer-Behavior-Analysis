from airflow import DAG
from airflow.utils import timezone
from airflow.models import Variable
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocSubmitJobOperator,
    DataprocDeleteClusterOperator
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.utils.trigger_rule import TriggerRule


# ==========================================
# Variables Configuration
# ==========================================
PROJECT_ID = Variable.get("project_id")
REGION = "asia-southeast1"
CLUSTER_NAME = "ecommerce-ephemeral-cluster"
GCS_BUCKET = "ecommerce-customer-behavior-2026-prod" 
DATASET_ID = "ecommerce_wh_prod"
DB_HOST = Variable.get("db_host")
DB_USERNAME = Variable.get("db_username")
DB_PASSWORD = Variable.get("db_password")

# ==========================================
# Dataproc Configuration (Spark)
# ==========================================
# CLUSTER_CONFIG = {
#     "master_config": {
#         "num_instances": 1,
#         "machine_type_uri": "n1-standard-2",
#         "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 30},
#     },
#     "worker_config": {
#         "num_instances": 2,
#         "machine_type_uri": "n1-standard-2",
#         "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 30},
#     },
# }

CLUSTER_CONFIG = {
    "master_config": {
        "num_instances": 1,
        "machine_type_uri": "n1-standard-2",
        "disk_config": {"boot_disk_type": "pd-standard", "boot_disk_size_gb": 30},
    },
    "worker_config": {
        "num_instances": 0, 
    },
    "software_config": {
        "properties": {
            "dataproc:dataproc.allow.zero.workers": "true" 
        }
    },
    
    "gce_cluster_config": {
        "zone_uri": "asia-southeast1-b", 
    }
}

# ==========================================
# Table name and gcs path
# ==========================================
GOLD_TABLES = {
    "fact_events": "gold/facts/fact_events/*.parquet",
    "fact_sales_daily": "gold/facts/fact_sales_daily/*.parquet",
    "fact_funnel_metrics": "gold/facts/fact_funnel_metrics/*.parquet",
    "dim_product": "gold/dimensions/dim_product/*.parquet",
    "dim_user": "gold/dimensions/dim_user/*.parquet",
}


with DAG(
    dag_id="ecommerce_pipeline",
    start_date=timezone.datetime(2026, 7, 1),
    schedule='@daily',
    catchup=False,
):

    create_dataproc_cluster = DataprocCreateClusterOperator(
        task_id="create_dataproc_cluster",
        project_id=PROJECT_ID,
        cluster_config=CLUSTER_CONFIG,
        region=REGION,
        cluster_name=CLUSTER_NAME,
    )

    submit_ingest_data_job = DataprocSubmitJobOperator(
        task_id="submit_ingest_data_job",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "reference": {"project_id": PROJECT_ID},
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": f"gs://{GCS_BUCKET}/scripts/ingest_from_cloudsql_to_gcs.py",
                "args": [DB_HOST, DB_USERNAME, DB_PASSWORD, GCS_BUCKET],
                "properties": {
                    "spark.jars": f"gs://{GCS_BUCKET}/jars/postgresql-42.6.0.jar"
                }
            },
        },
    )

    submit_clean_data_job = DataprocSubmitJobOperator(
        task_id="submit_clean_data_job",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "reference": {"project_id": PROJECT_ID},
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": f"gs://{GCS_BUCKET}/scripts/clean_bronze_to_silver.py",
                "args": [GCS_BUCKET] 
            },
        },
    )

    submit_create_fact_tables_job = DataprocSubmitJobOperator(
        task_id="submit_create_fact_tables_job",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "reference": {"project_id": PROJECT_ID},
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": f"gs://{GCS_BUCKET}/scripts/create_fact_tables.py",
                "args": [GCS_BUCKET] 
            },
        },
    )

    submit_create_dimension_tables_job = DataprocSubmitJobOperator(
        task_id="submit_create_dimension_tables_job",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "reference": {"project_id": PROJECT_ID},
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": f"gs://{GCS_BUCKET}/scripts/create_dimension_tables.py",
                "args": [GCS_BUCKET]
            },
        },
    )

    delete_dataproc_cluster = DataprocDeleteClusterOperator(
        task_id="delete_dataproc_cluster",
        project_id=PROJECT_ID,
        cluster_name=CLUSTER_NAME,
        region=REGION,
        trigger_rule=TriggerRule.ALL_DONE, 
    )

    load_to_bq_tasks = []

    for table_name, gcs_path in GOLD_TABLES.items():
        load_to_bq = GCSToBigQueryOperator(
            task_id=f"load_{table_name}_to_bq",
            bucket=GCS_BUCKET,
            source_objects=[gcs_path], 
            destination_project_dataset_table=f"{PROJECT_ID}.{DATASET_ID}.{table_name}",
            source_format="PARQUET",
            write_disposition="WRITE_TRUNCATE", 
            autodetect=True, 
        )
        load_to_bq_tasks.append(load_to_bq)

    # ==========================================
    # Dependencies
    # ==========================================
    create_dataproc_cluster >> submit_ingest_data_job >> submit_clean_data_job

    submit_clean_data_job >> [submit_create_fact_tables_job, submit_create_dimension_tables_job]

    [submit_create_fact_tables_job, submit_create_dimension_tables_job] >> delete_dataproc_cluster

    delete_dataproc_cluster >> load_to_bq_tasks