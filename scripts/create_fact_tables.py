import sys 
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round, sum, countDistinct


def create_fact_tables():

    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    spark = SparkSession.builder \
            .appName("create_fact_tables") \
            .getOrCreate()

    bucket_name = sys.argv[1]
    silver_input_path = f"gs://{bucket_name}/silver/cleaned_events/"
    gold_output_path = f"gs://{bucket_name}/gold"

    try:
        logging.info("Starting Fact Tables creation...")
        df = spark.read.parquet(silver_input_path)

        # -----------------------------------------
        # 1. create fact_events
        # -----------------------------------------
        fact_events_df = (df
                          .select(
                              col("event_time"),
                              col("event_type"),
                              col("event_date"),
                              col("product_id"),
                              col("price"),
                              col("user_id"),
                              col("user_session")
                          )
        )

        (fact_events_df
            .write
            .partitionBy("event_date")
            .mode("overwrite")
            .parquet(f"{gold_output_path}/facts/fact_events/")
        )
        logging.info("Created: fact_events")

        # -----------------------------------------
        # 2. create fact_sales_daily
        # -----------------------------------------
        fact_sales_daily_df = (df
                    .where(col("event_type") == "purchase")
                    .groupBy(col("event_date"))
                    .agg(round(sum("price"), 2).alias("total_sales"))
                    .orderBy("event_date")    
        )

        (fact_sales_daily_df 
            .write
            .mode("overwrite")
            .parquet(f"{gold_output_path}/facts/fact_sales_daily/")
        )
        logging.info("Created: fact_sales_daily")

        # -----------------------------------------
        # 3. create fact_funnel_metrics
        # -----------------------------------------
        fact_funnel_metrics_df = (df
                    .groupBy(col("event_type"))
                    .agg(countDistinct("user_session").alias("total_sessions"))
        )

        (fact_funnel_metrics_df
            .write
            .mode("overwrite")
            .parquet(f"{gold_output_path}/facts/fact_funnel_metrics/")
        )
        logging.info("Created: fact_funnel_metrics")

        logging.info("All Fact tables created successfully!")

    except Exception as e:
        logging.error(f"Unexpected error occurred!: {e}")
        raise e

    finally:
        spark.stop()

if __name__ == "__main__":
    create_fact_tables()