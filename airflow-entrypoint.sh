#!/bin/bash
set -e

echo "=== Airflow Entrypoint ==="

# Install dependencies
pip install requests beautifulsoup4 psycopg2-binary

# Wait for database
echo "Waiting for Airflow database..."
until pg_isready -h airflow-postgres -p 5432 -U airflow 2>/dev/null; do 
  echo "Database not ready, waiting 2 seconds..."
  sleep 2
done

echo "Database ready. Waiting 3 more seconds..."
sleep 3

# Export environment
echo "Setting Airflow environment variables..."
export AIRFLOW__CORE__LOAD_EXAMPLES="False"
export AIRFLOW__CORE__EXECUTOR="LocalExecutor"
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://airflow:airflow@airflow-postgres:5432/airflow"

# Check database connection
echo "Testing database connection..."
airflow db check || echo "Database check failed, will init..."

# Initialize database
echo "Initializing Airflow database..."
airflow db init

echo "Database initialized successfully!"

# Create admin user
echo "Creating admin user..."
airflow users create -u admin -p admin -r Admin -e a@a -f a -l d || true

# Start services
echo "Starting Airflow services..."
airflow scheduler &
sleep 2
airflow webserver

