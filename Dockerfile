FROM apache/airflow:2.8.0

USER root

# Install system dependencies if needed
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies (excluding apache-airflow as base image has it)
# The base image already has Airflow, so we only install our project dependencies
# Note: Using system pip (not --user) as base Airflow image expects packages in system location
RUN pip install --no-cache-dir \
    requests>=2.31.0 \
    beautifulsoup4>=4.12.0 \
    lxml>=4.9.0 \
    pymongo>=4.6.0 \
    pydantic>=2.5.0 \
    python-dotenv>=1.0.0

# Copy dealminer package
COPY --chown=airflow:root dealminer /opt/airflow/dealminer

# Set PYTHONPATH to include dealminer
ENV PYTHONPATH=/opt/airflow:/opt/airflow/dealminer:${PYTHONPATH}
