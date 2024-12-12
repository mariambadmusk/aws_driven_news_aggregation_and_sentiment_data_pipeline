# Setup Guide for this project for EC2, AWS System Manager, and RDS

#### Description:
    This project automates a data pipeline to collect daily news articles from Newsdata API, perform sentiment analysis, and store the processed data in PostgreSQL deployed to Amazon RDS

#### Key Features:
    - Daily Data Collection:
        - Extracts news articles (title, description, source, link, published date, country) using Newsdata API.
        - Schedules data collection for each category every 30 minutes to stay within API free rate limits.
    - Sentiment Analysis:
        - Calculates description length.
        - Determines sentiment based on article descriptions using Hugging Face Transformers library  nlptown/bert-base-multilingual-uncased-sentiment


## Step 1: Create an EC2 Instance
1. Launch a Linux AMI EC2 instance.
2. **Tag the Instance:** Use a consistent tag (e.g., `ProjectTag`) to ensure easier management across services.
3. **Configure Security Rules:**
   - Allow **Airflow port (8080)**.
   - Allow **PostgreSQL port (5432)**.
   - **Source:** Anywhere (IPv4)
4. Save changes and copy the public IPv4 DNS of the EC2 instance.

## Step 2: Set Up Amazon RDS
1. Create an Amazon RDS instance using PostgreSQL.
2. Select the VPC created during the EC2 setup.

## Step 3: Configure IAM Roles
1. Create IAM roles for AWS System Manager, EC2, and RDS:
   - **Role:** AWS service role for EC2 instances to call AWS services on your behalf.
   - **Use Case:** Select "System Manager" under AWS Services.
   - **Attach Policies:**
     - `AmazonRDSFullAccess`
     - `AmazonSSMAutomationRole`
   - Create the role.
2. Assign the created role to your EC2 instance.

## Step 4: Set Up AWS System Manager
Follow the AWS Systems Manager documentation to automate the Start/Stop of Amazon EC2 instances. Refer to AWS Systems Manager (SSM) - D

[text](https://www.youtube.com/watch?v=SFJDESVF3pY)

---

## Step 5: Configure the EC2 Instance
### Install Dependencies and Environment Setup
1. Update system packages:
   ```bash
   sudo apt update
   sudo apt install python3-pip sqlite3 python3.10-venv libpq-dev
   ```
2. Initialise a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install airflow
   ```bash
   pip install "apache-airflow[celery]==2.10.3" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.3/constraints-3.8.txt"
   ```
4. Install Postgresql
   ```bash
   sudo apt-get install postgresql postgresql-contrib
   ```
5. Set up directories and scripts by cloning or using commands:

 ```bash 
   sudo install git   # follow the rest of the commands
   ```

   OR 

   ```bash
   mkdir news_etl 
   nano app.log
   nano .env
      mkdir dags 
         - nano daily_news.py     # Copy and save script in the dags folder.
      nano requirements.txt  # Add package requirements and save.
      mkdir scripts
      - nano utils.py          # Copy and save utility functions.
      - nano create_tables.py  # Copy and save database initialisation script.
      - nano __init__.py
   ```
   or create folders and files manually and copy scripts

         news_etl/
      ├── dags/
      │   ├── daily_news.py
      ├── logs/
      │  ├── etl.log
      ├── .env
      ├── scripts/
      │   ├── create_tables.py
      │   ├── utils.py
      │   ├── __init__.py
      ├── requirements.txt
   
6. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Initialise Airflow
1. Install and initialise Airflow:
   ```bash
   airflow db init
   airflow users create -u <username> -f <first_name> -l <last_name> -r Admin -e <email>
   ```

---

## Step 6: Connect EC2 to RDS
1. Use the RDS endpoint, username, password, and port to connect from the EC2 instance:
   ```bash
   psql --host=<RDS_ENDPOINT> --port=5432 --username=<username> --dbname=<database_name> --password
   ```
2. Create project and Airflow databases in PostgreSQL:
   ```sql
   CREATE DATABASE <database>;
   CREATE USER <user> WITH PASSWORD '<password>';
   GRANT ALL PRIVILEGES ON DATABASE <database> TO <user>;

   CREATE DATABASE airflow;
   CREATE USER airflow WITH PASSWORD 'airflow';
   GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
   ```

---

## Step 7: Configure Airflow
1. Update Airflow configuration:
   ```bash
   cd airflow
   grep sql_alchemy airflow.cfg
   sed -i 's#sqlite:////home/ubuntu/airflow/airflow.db#postgresql+psycopg2://<rds_user>:<rds_password>@<rds_host>:<rds_port>/<rds_database>#g' airflow.cfg

   grep executor airflow.cfg
   sed -i 's#SequentialExecutor#LocalExecutor#g' airflow.cfg
   ```
2. Recreate the Airflow admin user:
   ```bash
   airflow users create -u <username> -f <first_name> -l <last_name> -r Admin -e <email>
   ```

---

## Step 8: Set Environment Variables
1. Create and configure `.env` file:
   ```bash
   nano .env   # add postgresql+psycopg2://<rds_user>:<rds_password>@<rds_endpoint>:5432/<rds_database> as connection url
               # add api_key
   ```
   Add the following:
   - RDS connection URL (as defined in `utils.py`).
   - NEWDATA.io API key.
2. Save and exit (Ctrl+S, Ctrl+X).

3. 5. Run the `create_tables.py` script:
   ```bash
   python3 create_tables.py
   ```

Your setup is now complete!


## Challenges:
    - API 
        - Using https://newsdata.io/ free tier provides 200 API credit at one article per 10 credit which restricted the numbers of articles that can be requested to a maximum of 20 articles per day.


