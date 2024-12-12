from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from newsdataapi import NewsDataApiClient
import pandas as pd
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from transformers import pipeline
from torch.utils.data import DataLoader
from scripts.utils import get_news_category_mapping, setup_logging


# Default arguments for the DAG
default_args = {
    'depends_on_past': False,
    'start_date': datetime(), #set tiem and date
    'email_on_failure': False,
    'email_on_retry': False,
}


class NewsETL():
    def __init__(self):
        load_dotenv()
        self.logger = setup_logging()
        self.api_key = os.getenv("API_KEY")
        self.db_connection = os.getenv("LOCAL_CONNECTION")
        if not self.api_key:
            self.logger.error("API_KEY not found in environment variables.")
        if not self.db_connection:
            self.logger.error("DB_CONNECTION not found in environment variables.")


    # get news data from newsdataapi for a category
    def get_api(self, category):
        try:
            api = NewsDataApiClient(apikey=self.api_key)
            self.logger.info(f'Fetching news for {category} category')
            response = api.latest_api(q=category, language='en', image=False, video=False, scroll=True, max_result=300)
            if response:
                return response
            else:
                self.logger.error(f'Fetching news for {category} category failed')      
        except Exception as e:
            self.logger.error(f'Fetching news for {category} category failed: {e}')
            exit(1)  


    # create dataframe from the api response for a category
    def create_dataframe(self, response, category):
        try:
            if response or response["results"]:
                self.logger.info(f"Creating a dataframe for {category} category")
                df = pd.DataFrame(response['results'], columns = ["article_id", "title", "description", "link", "pubDate", "source_name", "country", "image_url", "video_url"])
                df["description"] = df["description"].apply(lambda x: "No description available" if x == "" or pd.isna(x) or x is None else x)
                df['word_count'] = df['description'].apply(lambda x: len(x.split())if x is not None else x)
                df['sentiment'] = None
                df.insert(1, 'category', category)
                return df
            else:
                self.logger.error(f"Creating a dataframe for {category} category failed")
                return None
        except Exception as e:
            self.logger.error(f'Creating a dataframe for {category} category failed: {e}')
            return None 
        
    def add_sentiment_analysis(self, df):
        self.logger.info(f'Analysing and adding sentiment to the dataframe...')
        classification = pipeline('sentiment-analysis', truncation=True)
        dataset = df["description"].values
        try:
            dataloader = DataLoader(dataset, batch_size=5, shuffle=False)
            results = []
            for batch in dataloader:
                results.extend(classification(list(batch)))

            df["sentiment"] = [result["label"] for result in results]

            df["sentiment_score"] = [result["score"] for result in results]
            return df
        except Exception as e:
            self.logger.error(f'Analysing and adding sentiment to the dataframe failed: {e}')
            return None
            
        
        
    def clean_dataframe(self, df):
        try:
            self.logger.info(f'Cleaning and transforming dataframe...')
            df.drop_duplicates(subset=["article_id"],inplace=True)
            df.drop_duplicates(subset=["title"],inplace=True)

            # clean pubDate column
            df["pubDate"] = pd.to_datetime(df["pubDate"])
            df["pub_time"] = df["pubDate"].dt.strftime('%H:%M:%S')
            df["pub_date"] = df["pubDate"].dt.strftime('%d-%m-%Y')
            self.logger.info(f'Cleaning and transforming dataframe...')

            # reorder columns
            df.insert(5, "pub_date", df.pop("pub_date"))
            df.insert(6, "pub_time", df.pop("pub_time"))
            df.drop("pubDate", inplace=True, axis=1)

            # remove [] from country column
            df["country"] = df["country"].astype(str).str.replace(r'\[', '', regex=True)
            df["country"] = df["country"].astype(str).str.replace(r'\]', '', regex=True)
            df["country"] = df["country"].astype(str).str.replace(r'\'', '', regex=True)

            # Make sentiment column lowercase
            df["sentiment"] = df["sentiment"].str.lower()


            return df
        except Exception as e:
            self.logger.error(f'Cleaning and transforming dataframe failed: {e}')
            return None

        
    # insert dataframes to sql database
    def load_to_db(self, df, table_name, category):
        try:
            self.logger.info(f'Appending {category} to daily_news')
            engine = create_engine(self.db_connection)
            with engine.begin() as conn:
                df.to_sql(table_name, conn, if_exists = 'append', index = False)
            self.logger.info(f'NewsETL {category} completed successfully')
        except Exception as e:
            self.logger.error(f'Appending {category} to daily_news failed: {e}')



def main():
    etl = NewsETL()
    categories = get_news_category_mapping()
    for category in categories:
        response = etl.get_api(category)
        df = etl.create_dataframe(response, category)
        if df is not None:
            df = etl.add_sentiment_analysis(df)
            df = etl.clean_dataframe(df) 
            df = etl.load_to_db(df, "daily_news", category)
        


if __name__=="__main__":
    main()



# Define the DAG
with DAG(
    dag_id="daily_news_dag",
    default_args=default_args,
    schedule_interval='@daily',  
    catchup=False,  
    max_active_runs=1, 
    ) as dag:
    
    # Create a dummy start task
    start_task = DummyOperator(task_id='start_task')


    # Define the categories using the function from utils
    category_dict = get_news_category_mapping()

    # List to hold dynamically created tasks
    crawl_and_process_category_tasks = []

    # Create tasks for each category and set them to run every 30 minutes
    for idx, category in enumerate(category_dict):
        execution_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        task = PythonOperator(
            task_id=f'crawl_and_process_{category}',  
            python_callable=main,  
            op_args=[category], 
            execution_timeout=timedelta(minutes=30), 
            dag=dag
        )
        crawl_and_process_category_tasks.append(task)

        
        execution_time = execution_time = datetime.strptime(execution_date, "%Y-%m-%d %H:%M")
        task.execution_time_fn = lambda execution_time , offset=idx: execution_time + timedelta(minutes=30 * offset)

    # Create a dummy end task
    end_task = DummyOperator(task_id='end_task')


    # Set start_task to trigger the crawl_and_process_category_tasks
    start_task >> crawl_and_process_category_tasks >> end_task  


