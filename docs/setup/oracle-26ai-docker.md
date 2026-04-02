# Oracle 26ai Docker Setup

This project now includes a Docker-based local Oracle 26ai environment for development on Windows with Docker Desktop.

## What is included

- `compose.yaml`: starts Oracle AI Database 26ai Free in Docker
- `.env.example`: sample environment variables for image tag, listener port, and credentials
- `docker/oracle/startup/01-create-app-user.sh`: creates an application user inside `FREEPDB1`
- `scripts/start-oracle26ai.ps1`: starts the container and waits for it to become ready
- `scripts/load-oracle-schema.ps1`: loads the repo schema files into the application schema
- `scripts/validate-oracle-schema.ps1`: creates a temporary validation schema and runs positive and negative checks

## Prerequisites

1. Install Docker Desktop with Linux containers enabled.
2. Sign in to Oracle Container Registry and accept the license terms for the Oracle Database Free image:
   `https://container-registry.oracle.com/ords/ocr/ba/database/free`
3. Run:

```powershell
docker login container-registry.oracle.com
```

## Quick start

1. Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

2. Edit `.env` and change at least:

- `ORACLE_PWD`
- `APP_USER_PASSWORD`

Use simple ASCII passwords with uppercase, lowercase, and digits. Avoid `"` if you want to use the helper scripts unchanged.

3. Start the database:

```powershell
.\scripts\start-oracle26ai.ps1
```

If your local PowerShell execution policy blocks scripts, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-oracle26ai.ps1
```

4. Load the project schema files:

```powershell
.\scripts\load-oracle-schema.ps1
```

## Default connection information

- Host: `localhost`
- Port: `1521`
- Service name: `FREEPDB1`
- SYS/SYSTEM/PDBADMIN password: `ORACLE_PWD` from `.env`
- Application user: `APP_USER` from `.env`

## Notes

- The compose file pins the image to `23.26.1.0`, which is the Oracle AI Database 26ai Free image tag currently listed in Oracle Container Registry.
- If you want a smaller image for quicker pulls, change `ORACLE_IMAGE_TAG` to `23.26.1.0-lite`.
- Oracle Database Free images ship with a pre-built database. Startup is fast, but if you mount a fresh data volume, first-time initialization can still take several minutes.
- The repo already includes working schema files for tables, procedures, and triggers.
- After schema changes, you can rerun `validate-oracle-schema.ps1` to verify compilation, constraints, trigger behavior, and recommendation logic.

## Useful commands

```powershell
docker compose up -d
docker compose logs -f oracle26ai
docker compose down
docker exec -it oracle26ai sqlplus system/<password>@//localhost:1521/FREEPDB1
```
