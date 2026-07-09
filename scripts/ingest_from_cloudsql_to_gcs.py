import sys 
import logging
from pyspark.sql import SparkSession


def ingest_from_cloudsql_to_gcs():

    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    spark = (SparkSession.builder
        .appName("ingest_from_cloudsql_to_gcs")
        .getOrCreate()
    )

    db_host = sys.argv[1]      
    db_user = sys.argv[2]      
    db_password = sys.argv[3]  
    bucket_name = sys.argv[4]  

    jdbc_url = f"jdbc:postgresql://{db_host}:5432/ecommerce_db"
    table_name = "ecommerce_events" 
    bronze_output_path = f"gs://{bucket_name}/bronze/raw_events/"
    

    try:
        logging.info("Starting ingest raw data from Cloud SQL...")

        df = (spark.read.format("jdbc")
            .option("url", jdbc_url)
            .option("dbtable", table_name)
            .option("user", db_user)
            .option("password", db_password)
            .option("driver", "org.postgresql.Driver")
            .load()
        )

        (df.write
            .mode("overwrite")
            .parquet(bronze_output_path)
        )

        logging.info(f"Successfully uploaded data to: {bronze_output_path}")

    except Exception as e:
        logging.error(f"Unexpected error occurred!: {e}")
        raise e 

    finally:
        spark.stop()

if __name__ == "__main__":
    ingest_from_cloudsql_to_gcs()