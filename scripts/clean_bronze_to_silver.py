import sys 
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *


def clean_bronze_to_silver():

    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    spark = SparkSession.builder \
            .appName("clean_bronze_to_silver") \
            .getOrCreate()

    bucket_name = sys.argv[1]
    bronze_input_path = f"gs://{bucket_name}/bronze/raw_events/"
    silver_output_path = f"gs://{bucket_name}/silver/cleaned_events/"

    try:
        logging.info("Starting clean process...")
        df = spark.read.parquet(bronze_input_path)

        cleaned_df = (df 

                    # Data Type (Casting)
                    .select(
                        to_timestamp(col("event_time"), "yyyy-MM-dd HH:mm:ss z").alias("event_time"),
                        col("event_type").cast(StringType()),
                        col("product_id").cast(StringType()),
                        col("category_id").cast(StringType()),
                        col("category_code").cast(StringType()),
                        col("brand").cast(StringType()),
                        col("price").cast(DecimalType(10, 2)),
                        col("user_id").cast(StringType()),
                        col("user_session").cast(StringType())
                    )
                      
                    # Handling null values
                    .dropna(subset=["event_time", "user_id"])
                    .fillna({
                        "category_code": "Unknown", 
                        "brand": "Unknown", 
                        "price": 0.0}
                    )

                    # Handling negative values
                    .filter(col("price") >= 0)

                    # Handling duplicates 
                    .dropDuplicates([
                        "event_time", 
                        "event_type", 
                        "product_id", 
                        "user_id", 
                        "user_session"]
                    )

                    # Add timestamps and create event_date for partitioning
                    .withColumn("event_date", to_date(col("event_time")))
                    .withColumn("processed_at", current_timestamp())                   
        )

        (cleaned_df
            .write
            .partitionBy("event_date")
            .mode("overwrite")
            .parquet(silver_output_path)
        )
        logging.info(f"Successfully cleaned and uploaded data to {silver_output_path}")

    except Exception as e:
        logging.error(f"Unexpected error occurred!: {e}")
        raise e

    finally:
        spark.stop()

if __name__ == "__main__":
    clean_bronze_to_silver()