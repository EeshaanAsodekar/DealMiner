# Airflow Pipeline Setup and Usage Guide

## Prerequisites

- Docker Desktop installed and running
- Docker Compose available (usually comes with Docker Desktop)
- Git repository cloned

## Step 1: Initial Setup

### 1.1 Set Airflow UID (Linux/Mac only)
```bash
# Check your user ID
echo $AIRFLOW_UID

# If empty, set it (replace 50000 with your user ID if different)
export AIRFLOW_UID=50000
```

On Windows, you can skip this step - the default in docker-compose.yml will work.

### 1.2 Verify Docker is Running
```bash
docker --version
docker-compose --version
```

Both commands should return version numbers.

## Step 2: Start Airflow Services

### 2.1 Navigate to Project Directory
```bash
cd C:\code\DealMiner
```

### 2.2 Initialize Airflow Database (First Time Only)
```bash
docker-compose up airflow-init
```

This will:
- Create the Airflow database
- Create the admin user (username: `airflow`, password: `airflow`)
- Run database migrations

Wait for the message: `airflow-init_1       | User "airflow" created with admin role password`

### 2.3 Start All Services
```bash
docker-compose up -d
```

The `-d` flag runs containers in detached mode (background).

This will start:
- PostgreSQL database
- Airflow webserver (UI) on port 8080
- Airflow scheduler
- Airflow init (if first time)

### 2.4 Check Container Status
```bash
docker-compose ps
```

You should see:
- `postgres` - Running
- `airflow-webserver` - Running (healthy)
- `airflow-scheduler` - Running
- `airflow-init` - Exited (this is normal)

If any container shows as unhealthy, check logs:
```bash
docker-compose logs [service-name]
```

## Step 3: Verify Installation

### 3.1 Check Airflow Webserver Logs
```bash
docker-compose logs airflow-webserver
```

Look for:
- `Running on http://0.0.0.0:8080`
- No critical errors

### 3.2 Check Airflow Scheduler Logs
```bash
docker-compose logs airflow-scheduler
```

Look for:
- `INFO - Starting the scheduler`
- `INFO - Searching for files in /opt/airflow/dags`

### 3.3 Verify DAG is Loaded
```bash
docker-compose exec airflow-webserver airflow dags list
```

You should see `sec_filing_pipeline` in the list.

If the DAG doesn't appear, check for import errors:
```bash
docker-compose exec airflow-webserver airflow dags list-import-errors
```

## Step 4: Access Airflow UI

1. Open your web browser
2. Navigate to: **http://localhost:8080**
3. Login with:
   - **Username:** `airflow`
   - **Password:** `airflow`

## Step 5: Trigger the DAG

### Option A: Via Airflow UI (Recommended)

1. In the Airflow UI, find the DAG: **`sec_filing_pipeline`**
2. Click the **play/pause** button to turn it ON (if paused)
3. Click the **"Trigger DAG w/ config"** button (play icon with config)
4. In the popup, enter the JSON configuration:
   ```json
   {
     "target_date": "2025-12-22"
   }
   ```
5. Click **"Trigger"**

### Option B: Via CLI

```bash
docker-compose exec airflow-webserver airflow dags trigger sec_filing_pipeline --conf '{"target_date": "2025-12-22"}'
```

## Step 6: Monitor Execution

1. Click on the DAG name **`sec_filing_pipeline`**
2. Click on the latest **DAG Run** (should show the current date/time)
3. Click **"Graph View"** to see task status:
   - **Green** = Success
   - **Orange** = Running
   - **Red** = Failed
   - **Light Blue** = Queued

4. Click on individual tasks to:
   - View logs
   - See task details
   - Check XCom data (task outputs)

## Step 7: View Logs

### In Airflow UI:
1. Click on a task in Graph/Tree view
2. Click **"Log"** button
3. View task execution logs

### Via CLI:
```bash
# View webserver logs
docker-compose logs -f airflow-webserver

# View scheduler logs
docker-compose logs -f airflow-scheduler

# View specific task logs (after DAG run)
docker-compose exec airflow-webserver airflow tasks logs sec_filing_pipeline discover_filings [dag_run_id] [task_instance_id]
```

## Step 8: Test Individual Tasks (Before Full DAG Run)

Test each task in isolation to verify it works before running the full pipeline:

### 8.1 Open Airflow Container Shell
```powershell
# Find the scheduler container ID
docker ps

# Open interactive bash (use your container ID, e.g. dde96cec707c)
docker exec -it dde96cec707c /bin/bash
```

### 8.2 Run Task Tests (inside container)
Use an execution date in the past. The `discover_filings` task uses `target_date` from DAG config; when testing, it falls back to yesterday if no config.

```bash
# Test 1: discover_filings
airflow tasks test sec_filing_pipeline discover_filings 2026-01-31

# Test 2: download_target_forms (needs discover_filings XCom - will get empty list if run alone)
airflow tasks test sec_filing_pipeline download_target_forms 2026-01-31

# Test 3: download_8k_filings (same - needs discover_filings XCom)
airflow tasks test sec_filing_pipeline download_8k_filings 2026-01-31

# Test 4: parse_filter_8k (needs download_8k_filings XCom)
airflow tasks test sec_filing_pipeline parse_filter_8k 2026-01-31

# Test 5: store_filings (needs download_target_forms + parse_filter_8k XCom)
airflow tasks test sec_filing_pipeline store_filings 2026-01-31
```

**Note:** Tasks 2–5 pull data from upstream tasks via XCom. When testing in isolation, they receive empty lists and should complete quickly (no-op). Run `discover_filings` first to verify the read-only fix; it writes CSV to `/opt/airflow/data/processed/`.

### 8.3 Exit Container
```bash
exit
```

## Common Issues and Solutions

### Issue 1: DAG Not Appearing
**Check:**
```bash
docker-compose exec airflow-webserver airflow dags list-import-errors
```
**Solution:** Fix import errors in the output. Common issues:
- Missing Python packages
- Path issues in DAG files

### Issue 2: "Read-only file system" when writing CSV/data
**Error:** `OSError: [Errno 30] Read-only file system: '/opt/airflow/dealminer/data/processed/...'`

**Solution:** The `DEALMINER_DATA_DIR` env var must point to `/opt/airflow/data` (writable mount). This is set in docker-compose.yml. Restart containers after any config change: `docker-compose down && docker-compose up -d`.

### Issue 3: MongoDB Connection Failed
**Check logs:**
```bash
docker-compose logs airflow-scheduler | grep -i mongo
```
**Solution:** Verify MongoDB connection string in `env.example` and ensure it's accessible from Docker container.

### Issue 4: Container Keeps Restarting
**Check:**
```bash
docker-compose ps
docker-compose logs [service-name]
```
**Solution:** Check logs for specific errors. Common causes:
- Port 8080 already in use
- Insufficient memory/CPU
- Database connection issues

### Issue 4: Tasks Failing
**Check task logs in Airflow UI:**
1. Click on failed task
2. Click "Log" button
3. Look for error messages

**Common fixes:**
- Missing dependencies: Check `requirements.txt`
- File permissions: Ensure volumes are mounted correctly
- Network issues: Check internet connectivity for SEC downloads

## Stopping Services

```bash
# Stop all services (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove containers AND volumes (deletes data)
docker-compose down -v
```

## Restarting After Changes

If you modify DAG files or Python code:
1. Save files
2. Wait ~30 seconds for Airflow to reload DAGs (or restart):
   ```bash
   docker-compose restart airflow-webserver airflow-scheduler
   ```

## Useful Commands

```bash
# Check if DAG is paused
docker-compose exec airflow-webserver airflow dags list-runs -d sec_filing_pipeline

# Unpause DAG
docker-compose exec airflow-webserver airflow dags unpause sec_filing_pipeline

# Pause DAG
docker-compose exec airflow-webserver airflow dags pause sec_filing_pipeline

# Test a task without running the full DAG
docker-compose exec airflow-webserver airflow tasks test sec_filing_pipeline discover_filings 2025-12-22

# Check Python packages in container
docker-compose exec airflow-webserver pip list

# Access container shell
docker-compose exec airflow-webserver bash
```

## Next Steps After First Run

1. **Verify MongoDB**: Check that filings were stored:
   ```bash
   # Connect to MongoDB and verify collection
   # Use MongoDB Compass or CLI with connection string
   ```

2. **Check Downloaded Files**: 
   - Local files should be in `dealminer/data/raw/filings/`
   - Organized by form type

3. **Review Logs**: Check for any warnings or errors in task logs

## Troubleshooting Quick Reference

| Issue | Command to Check |
|-------|------------------|
| DAG not showing | `docker-compose exec airflow-webserver airflow dags list-import-errors` |
| Container not starting | `docker-compose logs [service-name]` |
| Task failing | Check logs in Airflow UI or `docker-compose logs airflow-scheduler` |
| Port in use | Change port in `docker-compose.yml` or stop conflicting service |
| MongoDB connection | Check connection string and network access from container |
