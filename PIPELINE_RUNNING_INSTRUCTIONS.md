# Pipeline Running Instructions

Complete step-by-step guide to run the SEC Filing Pipeline from scratch.

---

## Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- Project cloned to `C:\code\DealMiner` (or your path)

---

## Part 1: Environment Setup

### 1.1 Create `.env` File

Ensure you have a `.env` file in the project root with your MongoDB and SEC settings:

```env
AIRFLOW_UID=50000

MONGODB_CONNECTION_STRING=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/
MONGODB_DATABASE=MnA_filings
MONGODB_COLLECTION_NAME=raw_filings

SEC_USER_AGENT=DealMiner/0.1 (your.email@example.com)
```

**MongoDB:** Use your Atlas connection string. Ensure your IP is whitelisted in Atlas Network Access.

**SEC:** The SEC requires a user-agent identifying your tool; use your real email.

---

## Part 2: Docker Commands (From Scratch)

### 2.1 Open Terminal and Navigate to Project

```powershell
cd C:\code\DealMiner
```

### 2.2 Stop Any Running Containers (If Restarting)

```powershell
docker-compose down
```

### 2.3 Initialize Airflow (First Time Only)

```powershell
docker-compose up --build airflow-init
```

Wait for:
- `Performing upgrade to the metadata database`
- `Database migrating done!`
- `airflow already exist in the db` or `User "airflow" created`
- `airflow-init-1 exited with code 0`

This creates the Airflow database and admin user. **Skip this step** if you've already run it.

### 2.4 Start All Services

```powershell
docker-compose up -d
```

Starts:
- **PostgreSQL** – Airflow metadata database
- **Airflow webserver** – UI at http://localhost:8080
- **Airflow scheduler** – Runs DAGs

### 2.5 Verify Containers Are Running

```powershell
docker-compose ps
```

All services should show `Up` and `(healthy)`:
- `dealminer-postgres-1`
- `dealminer-airflow-webserver-1`
- `dealminer-airflow-scheduler-1`

### 2.6 Wait for Services to Be Ready

Give it 30–60 seconds for the webserver and scheduler to become healthy. Check logs if needed:

```powershell
docker-compose logs -f airflow-scheduler
# Press Ctrl+C to stop following
```

---

## Part 3: Verify DAG Is Loaded

### 3.1 List DAGs

```powershell
docker-compose exec airflow-webserver airflow dags list
```

You should see `sec_filing_pipeline` in the output.

### 3.2 Check for Import Errors (If DAG Missing)

```powershell
docker-compose exec airflow-webserver airflow dags list-import-errors
```

---

## Part 4: Run the DAG

### 4.1 Access Airflow UI

1. Open browser: **http://localhost:8080**
2. Login: **airflow** / **airflow**

### 4.2 Trigger via UI (Recommended)

1. Find DAG: **sec_filing_pipeline**
2. Toggle the **pause switch** to ON (blue) if it’s paused
3. Click **Trigger DAG w/ config** (play icon with “+”)
4. Enter JSON:
   ```json
   {"target_date": "2026-01-30"}
   ```
5. Click **Trigger**

Replace `2026-01-30` with the date you want (YYYY-MM-DD).

### 4.3 Trigger via CLI (PowerShell)

PowerShell can mangle JSON, so use escaped quotes:

```powershell
docker-compose exec airflow-webserver airflow dags unpause sec_filing_pipeline

docker-compose exec airflow-webserver airflow dags trigger sec_filing_pipeline --conf "{\"target_date\": \"2026-01-30\"}"
```

**Alternative – from inside container:**

```powershell
# Get container ID
docker ps

# Open shell (replace CONTAINER_ID with scheduler ID)
docker exec -it CONTAINER_ID bash

# Inside container:
airflow dags unpause sec_filing_pipeline
airflow dags trigger sec_filing_pipeline --conf '{"target_date": "2026-01-30"}'
exit
```

---

## Part 5: Monitor Execution

### 5.1 In Airflow UI

1. Click **sec_filing_pipeline**
2. Open the latest DAG run (by time)
3. Use **Graph View** to see task status:
   - Green = Success
   - Orange = Running
   - Red = Failed
   - Light blue = Queued

### 5.2 Task Order

1. **discover_filings** – Fetches SEC daily index, filters by form type
2. **download_target_forms** – Downloads PREM14A, S-4, 425, etc.
3. **download_8k_filings** – Downloads all 8-K filings
4. **parse_filter_8k** – Parses 8-Ks, keeps only those with items 1.01, 2.01, 9.01
5. **store_filings** – Writes all target filings to MongoDB

### 5.3 View Task Logs

Click a task → **Log** to see stdout/stderr.

---

## Part 6: Verify MongoDB Population

### 6.1 MongoDB Compass

1. Connect: `mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/`
2. Open database: **MnA_filings** (or your `MONGODB_DATABASE`)
3. Open collection: **raw_filings** (or your `MONGODB_COLLECTION_NAME`)
4. Confirm documents appear with `accession_number`, `raw_filing`, etc.

### 6.2 Document Structure

Each document includes:
- `accession_number`, `form_type`, `cik`, `company_name`, `filing_date`
- `raw_filing` – Full primary HTML content
- `filing_path`, `primary_html_path`, `exhibits`, `manifest`
- For 8-K: `has_target_items`, `target_items_found`, `parsed_items`
- `stored_at`, `updated_at`

### 6.3 Test MongoDB Connection (Optional)

```powershell
docker exec CONTAINER_ID python /opt/airflow/scripts/test_mongodb_connection.py
```

Replace `CONTAINER_ID` with the airflow-scheduler container ID.

---

## Part 7: Useful Commands

### 7.1 DAG Management

```powershell
# Unpause DAG
docker-compose exec airflow-webserver airflow dags unpause sec_filing_pipeline

# Pause DAG
docker-compose exec airflow-webserver airflow dags pause sec_filing_pipeline

# List DAG runs
docker-compose exec airflow-webserver airflow dags list-runs -d sec_filing_pipeline
```

### 7.2 Logs

```powershell
# Scheduler logs (real-time)
docker-compose logs -f airflow-scheduler

# Webserver logs
docker-compose logs -f airflow-webserver

# All logs
docker-compose logs -f
```

### 7.3 Restart After Code Changes

```powershell
docker-compose down
docker-compose up -d
```

Or restart only Airflow:

```powershell
docker-compose restart airflow-webserver airflow-scheduler
```

### 7.4 Stop Everything

```powershell
# Stop containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop, remove containers, and delete volumes (resets data)
docker-compose down -v
```

---

## Part 8: Test Individual Tasks (Optional)

To run tasks one by one (e.g. for debugging):

```powershell
# Get scheduler container ID
docker ps

# Open container shell
docker exec -it CONTAINER_ID bash

# Run tasks (use same date; downstream tasks get empty input when run alone)
airflow tasks test sec_filing_pipeline discover_filings 2026-01-31
airflow tasks test sec_filing_pipeline download_target_forms 2026-01-31
airflow tasks test sec_filing_pipeline download_8k_filings 2026-01-31
airflow tasks test sec_filing_pipeline parse_filter_8k 2026-01-31
airflow tasks test sec_filing_pipeline store_filings 2026-01-31

exit
```

---

## Part 9: Troubleshooting

| Issue | Solution |
|-------|----------|
| **DAG not appearing** | Run `docker-compose exec airflow-webserver airflow dags list-import-errors` and fix reported errors |
| **"Read-only file system"** | Restart with `docker-compose down && docker-compose up -d` so `DEALMINER_DATA_DIR` is applied |
| **MongoDB auth failed** | Check username/password and IP whitelist in Atlas Network Access |
| **CLI JSON error (PowerShell)** | Use UI trigger or escaped JSON: `--conf "{\"target_date\": \"2026-01-30\"}"` |
| **Port 8080 in use** | Stop the other service or change the port in `docker-compose.yml` |
| **Containers unhealthy** | Inspect `docker-compose logs [service-name]` and resolve the reported errors |

---

## Quick Reference: Full Run From Scratch

```powershell
cd C:\code\DealMiner

# First time only:
docker-compose up --build airflow-init

# Start services
docker-compose up -d

# Wait ~60 seconds, then trigger (UI preferred)
# Or via CLI:
docker-compose exec airflow-webserver airflow dags unpause sec_filing_pipeline
docker-compose exec airflow-webserver airflow dags trigger sec_filing_pipeline --conf "{\"target_date\": \"2026-01-30\"}"

# Monitor at http://localhost:8080
# Verify data in MongoDB Compass
```
