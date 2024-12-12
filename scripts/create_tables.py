# # from airflow import DAG
# # from airflow.operators.python import PythonOperator
# # from datetime import timedelta
# # from airflow.utils.dates import days_ago
from scripts.utils import get_database_connection, setup_logging


# create tables

def create_tables():
    logger = setup_logging()
    

    try:
        connection = get_database_connection()
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_news(
                article_id VARCHAR(50) PRIMARY KEY,
                category VARCHAR(15),
                title VARCHAR(1000),
                description VARCHAR(10000),
                link VARCHAR(600),
                pub_date DATE,
                pub_time TIME,
                source_name VARCHAR(50),
                country VARCHAR(50),
                image_url VARCHAR(400),
                video_url VARCHAR(200),
                word_count FLOAT,
                sentiment VARCHAR(10),
                sentiment_score FLOAT  
            );
        """)
        
        logger.info("Daily news table created successfully.")

    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        
    finally:
        if connection:
            cursor.close()
            connection.close()

            
if __name__ == "__main__":
    create_tables()


# # Define the default arguments for the DAG

# # default_args = {
# #             "owner": "kike",
# #             "depends_on_past": False,
# #             "email_on_failure": False,
# #             "email_on_retry": False,
# #             "retries": 2,
# #             "retry_delay": timedelta(minutes=5),
# # }

# # with DAG(
# #     dag_id="create_table_dag",
# #     default_args=default_args,
# #     description="DAG that runs once to create the table",
# #     schedule_interval=None,
# #     start_date=days_ago(1),
# #     catchup=False,
# # ) as dag:

# #     create_tables_task = PythonOperator(
# #         task_id='create_tables',
# #         python_callable=create_tables,
# #     )

# #     create_tables_task 



