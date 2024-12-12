import psycopg2
from dotenv import load_dotenv
import os
import logging

def setup_logging():
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            filename='etl.log', 
            level=logging.DEBUG, 
            format='%(asctime)s - %(levelname)s - %(filename)s: - %(message)s'
        )

    return logging.getLogger(__name__)



# load environment variables for news sentiment analysis database
def load_env_db():
    load_dotenv()
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_password = os.getenv('POSTGRES_PASSWORD')
    postgres_db = os.getenv('POSTGRES_DB')
    postgres_host = os.getenv('POSTGRES_HOST')
    postgres_port = os.getenv('POSTGRES_PORT')

    return postgres_user, postgres_password, postgres_db, postgres_host, postgres_port


# connect to default database
def get_database_connection():
    logger = setup_logging()

    try:
        # connect to database
        postgres_user, postgres_password, postgres_db, postgres_host, postgres_port = load_env_db()
        db_config = {
            'dbname': postgres_db,
            'user': postgres_user,
            'password': postgres_password,
            'host': postgres_host,
            'port': postgres_port
        }

        connection = psycopg2.connect(**db_config)
        logger.info("News sentiment analysis database connection established successfully.")
        return connection
    except psycopg2.DatabaseError as error:
        logger.error(f"Error connecting to News sentiment analysis database: {error}")
        return None
    except psycopg2.OperationalError as error:
        logger.error(f"OperationalError connecting to News sentiment analysis database: {error}")
        return None


# map categories and category_id
def get_news_category_mapping():
    category_id_mapping = {
                'business': 101,
                'crime': 102,
                'education': 103,
                'entertainment': 104,
                'health': 105,
                'science': 106
            }
    return category_id_mapping





