import sys 
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import min, max


def create_dimension_tables():

    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    spark = SparkSession.builder \
            .appName("create_dimension_tables") \
            .getOrCreate()

    bucket_name = sys.argv[1]
    silver_input_path = f"gs://{bucket_name}/silver/cleaned_events/"
    gold_output_path = f"gs://{bucket_name}/gold"

    try:
        logging.info("Starting Dimension Tables creation...")
        df = spark.read.parquet(silver_input_path)

        # -----------------------------------------
        # 1. create dim_product
        # -----------------------------------------
        dim_product_df = (df
            .select(
                "product_id", 
                "category_id", 
                "category_code", 
                "brand"
            )
            .dropDuplicates(["product_id"]) 
        )

        (dim_product_df
            .write
            .mode("overwrite")
            .parquet(f"{gold_output_path}/dimensions/dim_product/")
        )
        logging.info("Created: dim_product")

        # -----------------------------------------
        # 2. create dim_user
        # -----------------------------------------
        dim_user_df = (df
            .groupBy("user_id")
            .agg(
                min("event_time").alias("first_active_time"),
                max("event_time").alias("last_active_time")
            )
        )

        (dim_user_df
            .write
            .mode("overwrite")
            .parquet(f"{gold_output_path}/dimensions/dim_user/")
        )
        logging.info("Created: dim_user")

        logging.info("All Dimension tables created successfully!")

    except Exception as e:
        logging.error(f"Unexpected error occurred!: {e}")
        raise e

    finally:
        spark.stop()

if __name__ == "__main__":
    create_dimension_tables()