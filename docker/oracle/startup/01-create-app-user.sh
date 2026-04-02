#!/bin/bash

set -euo pipefail

APP_USER="${APP_USER:-AI_QA_APP}"
APP_USER_PASSWORD="${APP_USER_PASSWORD:-}"

if [[ -z "${APP_USER_PASSWORD}" ]]; then
  echo "APP_USER_PASSWORD is not set; skipping app user bootstrap."
  exit 0
fi

echo "Ensuring application user ${APP_USER} exists in FREEPDB1..."

sqlplus -s / as sysdba <<SQL
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;

DECLARE
  l_user_count NUMBER := 0;
BEGIN
  SELECT COUNT(*)
    INTO l_user_count
    FROM dba_users
   WHERE username = UPPER('${APP_USER}');

  IF l_user_count = 0 THEN
    EXECUTE IMMEDIATE q'[CREATE USER ${APP_USER} IDENTIFIED BY "${APP_USER_PASSWORD}"]';
  END IF;
END;
/

ALTER USER ${APP_USER}
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP
  QUOTA UNLIMITED ON USERS;

GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE SEQUENCE,
      CREATE PROCEDURE, CREATE TRIGGER
  TO ${APP_USER};

EXIT;
SQL

echo "Application user bootstrap completed."
