[CmdletBinding()]
param(
    [string]$ContainerName = "oracle26ai",
    [string]$ServiceName = "FREEPDB1",
    [string]$TempUserPrefix = "QA_VAL",
    [string[]]$SqlFiles = @(
        "sql/create_tables.sql",
        "sql/procedures.sql",
        "sql/triggers.sql"
    )
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Wait-ContainerHealthy {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [int]$TimeoutSeconds = 300
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $status = docker inspect -f "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}" $Name 2>$null
        if ($LASTEXITCODE -eq 0) {
            $status = $status.Trim()
            if ($status -eq "healthy" -or $status -eq "running") {
                return
            }
        }

        Start-Sleep -Seconds 5
    }

    throw "Timed out waiting for container '$Name' to become healthy."
}

if (-not (Test-CommandExists -Name "docker")) {
    throw "Docker CLI is not installed or not on PATH."
}

Wait-ContainerHealthy -Name $ContainerName

$resolvedSqlFiles = @()
foreach ($sqlFile in $SqlFiles) {
    $resolvedPath = $sqlFile
    if (-not [System.IO.Path]::IsPathRooted($resolvedPath)) {
        $resolvedPath = Join-Path $RepoRoot $resolvedPath
    }

    if (-not (Test-Path -LiteralPath $resolvedPath)) {
        throw "SQL file not found: $resolvedPath"
    }

    $resolvedSqlFiles += $resolvedPath
}

$tempUser = ($TempUserPrefix + "_" + (Get-Date -Format "MMddHHmmss")).ToUpperInvariant()
$tempPassword = "QaVal123"

$rootSql = @"
WHENEVER SQLERROR EXIT SQL.SQLCODE
ALTER SESSION SET CONTAINER = FREEPDB1;
BEGIN
  EXECUTE IMMEDIATE 'DROP USER $tempUser CASCADE';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE <> -1918 THEN
      RAISE;
    END IF;
END;
/
CREATE USER $tempUser IDENTIFIED BY "$tempPassword";
ALTER USER $tempUser
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP
  QUOTA UNLIMITED ON USERS;
GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE SEQUENCE,
      CREATE PROCEDURE, CREATE TRIGGER
  TO $tempUser;
EXIT
"@

$validationSql = @"
WHENEVER SQLERROR EXIT SQL.SQLCODE
SET SERVEROUTPUT ON
SET PAGESIZE 200
SET LINESIZE 200
CONNECT $tempUser/"$tempPassword"@//localhost:1521/$ServiceName
@/tmp/create_tables.sql
@/tmp/procedures.sql
@/tmp/triggers.sql

PROMPT === INVALID OBJECTS ===
SELECT object_type, object_name, status
  FROM user_objects
 WHERE status <> 'VALID'
   AND object_type IN ('PACKAGE', 'PACKAGE BODY', 'TRIGGER', 'PROCEDURE', 'FUNCTION', 'VIEW')
 ORDER BY object_type, object_name;

PROMPT === COMPILATION ERRORS ===
SELECT type, name, line, position, text
  FROM user_errors
 ORDER BY name, sequence;

DECLARE
  l_error_count NUMBER;
BEGIN
  SELECT COUNT(*)
    INTO l_error_count
    FROM user_errors;

  IF l_error_count > 0 THEN
    RAISE_APPLICATION_ERROR(-20001, 'Compilation errors found: ' || l_error_count);
  END IF;
END;
/

DECLARE
  l_user_a_id         users.user_id%TYPE;
  l_user_b_id         users.user_id%TYPE;
  l_category_id       categories.category_id%TYPE;
  l_question_a_id     questions.question_id%TYPE;
  l_question_b_id     questions.question_id%TYPE;
  l_answer_id         answers.answer_id%TYPE;
  l_accepted_answer_id questions.accepted_answer_id%TYPE;
  l_question_status   questions.status%TYPE;
  l_view_count        questions.view_count%TYPE;
  l_favorite_count    questions.favorite_count%TYPE;
  l_answer_count      questions.answer_count%TYPE;
  l_like_count        answers.like_count%TYPE;
  l_dislike_count     answers.dislike_count%TYPE;
  l_avg_rating        answers.avg_rating%TYPE;
  l_profile_rows      NUMBER;
  l_total_weight      NUMBER;
  l_active_recs       NUMBER;
  l_expired_recs      NUMBER;
  l_rec_score         NUMBER;
  l_last_login_flag   VARCHAR2(20);

  PROCEDURE assert_number(
      p_label    IN VARCHAR2,
      p_actual   IN NUMBER,
      p_expected IN NUMBER
  ) IS
  BEGIN
      DBMS_OUTPUT.PUT_LINE(
          'CHECK ' || p_label
          || ' actual=' || NVL(TO_CHAR(p_actual), 'NULL')
          || ' expected=' || NVL(TO_CHAR(p_expected), 'NULL')
      );

      IF (p_actual IS NULL AND p_expected IS NOT NULL)
         OR (p_actual IS NOT NULL AND p_expected IS NULL)
         OR (p_actual <> p_expected) THEN
          RAISE_APPLICATION_ERROR(
              -20010,
              'Assertion failed for ' || p_label
          );
      END IF;
  END assert_number;

  PROCEDURE assert_text(
      p_label    IN VARCHAR2,
      p_actual   IN VARCHAR2,
      p_expected IN VARCHAR2
  ) IS
  BEGIN
      DBMS_OUTPUT.PUT_LINE(
          'CHECK ' || p_label
          || ' actual=' || NVL(p_actual, 'NULL')
          || ' expected=' || NVL(p_expected, 'NULL')
      );

      IF NVL(p_actual, '#NULL#') <> NVL(p_expected, '#NULL#') THEN
          RAISE_APPLICATION_ERROR(
              -20011,
              'Assertion failed for ' || p_label
          );
      END IF;
  END assert_text;
BEGIN
  DBMS_OUTPUT.PUT_LINE('=== POSITIVE PATH TESTS ===');

  INSERT INTO users (username, password_hash, nickname, email, role, status)
  VALUES ('user_a', 'hash_a', 'User A', 'user_a@example.com', 'USER', 'ACTIVE')
  RETURNING user_id INTO l_user_a_id;

  INSERT INTO users (username, password_hash, nickname, email, role, status)
  VALUES ('user_b', 'hash_b', 'User B', 'user_b@example.com', 'USER', 'ACTIVE')
  RETURNING user_id INTO l_user_b_id;

  INSERT INTO categories (category_name, description, status)
  VALUES ('database', 'Database category', 'ACTIVE');

  INSERT INTO tags (tag_name) VALUES ('oracle');
  INSERT INTO tags (tag_name) VALUES ('docker');

  SELECT category_id
    INTO l_category_id
    FROM categories
   WHERE category_name = 'database';

  INSERT INTO questions (user_id, category_id, title, content, status)
  VALUES (l_user_a_id, l_category_id, 'Question A', 'How to use Oracle 26ai with Docker?', 'OPEN')
  RETURNING question_id INTO l_question_a_id;

  INSERT INTO questions (user_id, category_id, title, content, status)
  VALUES (l_user_b_id, l_category_id, 'Question B', 'How to optimize Docker storage?', 'OPEN')
  RETURNING question_id INTO l_question_b_id;

  INSERT INTO question_tags (question_id, tag_id)
  SELECT l_question_a_id, t.tag_id
    FROM tags t
   WHERE t.tag_name = 'oracle';

  INSERT INTO question_tags (question_id, tag_id)
  SELECT l_question_b_id, t.tag_id
    FROM tags t
   WHERE t.tag_name = 'oracle';

  INSERT INTO question_tags (question_id, tag_id)
  SELECT l_question_b_id, t.tag_id
    FROM tags t
   WHERE t.tag_name = 'docker';

  INSERT INTO answers (question_id, answer_type, provider_name, content, model_name, confidence_score)
  VALUES (l_question_a_id, 'AI', 'OpenAI', 'Use the official Oracle container image.', 'gpt-5', 92.50)
  RETURNING answer_id INTO l_answer_id;

  INSERT INTO browse_history (user_id, question_id, duration, click_depth)
  VALUES (l_user_b_id, l_question_a_id, 180, 3);

  INSERT INTO favorites (user_id, question_id)
  VALUES (l_user_b_id, l_question_a_id);

  INSERT INTO answer_feedback (answer_id, user_id, is_like, rating, comment_text)
  VALUES (l_answer_id, l_user_b_id, 'Y', 4.5, 'Helpful answer');

  INSERT INTO login_log (user_id, result)
  VALUES (l_user_a_id, 'SUCCESS');

  COMMIT;

  SELECT view_count, favorite_count, answer_count
    INTO l_view_count, l_favorite_count, l_answer_count
    FROM questions
   WHERE question_id = l_question_a_id;

  assert_number('question_a.view_count', l_view_count, 1);
  assert_number('question_a.favorite_count', l_favorite_count, 1);
  assert_number('question_a.answer_count', l_answer_count, 1);

  SELECT like_count, dislike_count, avg_rating
    INTO l_like_count, l_dislike_count, l_avg_rating
    FROM answers
   WHERE answer_id = l_answer_id;

  assert_number('answer.like_count', l_like_count, 1);
  assert_number('answer.dislike_count', l_dislike_count, 0);
  assert_number('answer.avg_rating', l_avg_rating, 4.5);

  UPDATE questions
     SET accepted_answer_id = l_answer_id,
         status = 'RESOLVED'
   WHERE question_id = l_question_a_id;

  COMMIT;

  SELECT accepted_answer_id, status
    INTO l_accepted_answer_id, l_question_status
    FROM questions
   WHERE question_id = l_question_a_id;

  assert_number('question_a.accepted_answer_id', l_accepted_answer_id, l_answer_id);
  assert_text('question_a.status.after_accept', l_question_status, 'RESOLVED');

  qa_app_pkg.rebuild_user_tag_profile(l_user_a_id);
  qa_app_pkg.generate_recommendations(l_user_a_id, 5);

  SELECT COUNT(*), ROUND(NVL(SUM(weight), 0), 2)
    INTO l_profile_rows, l_total_weight
    FROM user_tag_profile
   WHERE user_id = l_user_a_id;

  assert_number('user_a.profile_rows', l_profile_rows, 1);
  assert_number('user_a.profile_weight', l_total_weight, 5);

  SELECT COUNT(*), MAX(rec_score)
    INTO l_active_recs, l_rec_score
    FROM recommendations
   WHERE user_id = l_user_a_id
     AND status = 'ACTIVE';

  assert_number('user_a.active_recommendations', l_active_recs, 1);
  assert_number('user_a.max_recommendation_score', l_rec_score, 5);

  SELECT CASE WHEN last_login_time IS NOT NULL THEN 'UPDATED' ELSE 'NULL' END
    INTO l_last_login_flag
    FROM users
   WHERE user_id = l_user_a_id;

  assert_text('user_a.last_login_time', l_last_login_flag, 'UPDATED');

  DBMS_OUTPUT.PUT_LINE('=== NEGATIVE CONSTRAINT TESTS ===');

  SAVEPOINT sp_dup_username;
  BEGIN
      INSERT INTO users (username, password_hash, role, status)
      VALUES ('user_a', 'dup_hash', 'USER', 'ACTIVE');
      RAISE_APPLICATION_ERROR(-20020, 'Duplicate username was allowed');
  EXCEPTION
      WHEN DUP_VAL_ON_INDEX THEN
          DBMS_OUTPUT.PUT_LINE('CHECK duplicate username rejected as expected');
          ROLLBACK TO sp_dup_username;
  END;

  SAVEPOINT sp_invalid_role;
  BEGIN
      INSERT INTO users (username, password_hash, role, status)
      VALUES ('bad_role_user', 'bad_hash', 'SUPER_ADMIN', 'ACTIVE');
      RAISE_APPLICATION_ERROR(-20021, 'Invalid role was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2290 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK invalid role rejected as expected');
          ROLLBACK TO sp_invalid_role;
  END;

  SAVEPOINT sp_invalid_question_status;
  BEGIN
      INSERT INTO questions (user_id, category_id, title, content, status)
      VALUES (l_user_a_id, l_category_id, 'Bad Status Question', 'bad status', 'UNKNOWN');
      RAISE_APPLICATION_ERROR(-20027, 'Invalid question status was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2290 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK invalid question status rejected as expected');
          ROLLBACK TO sp_invalid_question_status;
  END;

  SAVEPOINT sp_dup_favorite;
  BEGIN
      INSERT INTO favorites (user_id, question_id)
      VALUES (l_user_b_id, l_question_a_id);
      RAISE_APPLICATION_ERROR(-20022, 'Duplicate favorite was allowed');
  EXCEPTION
      WHEN DUP_VAL_ON_INDEX THEN
          DBMS_OUTPUT.PUT_LINE('CHECK duplicate favorite rejected as expected');
          ROLLBACK TO sp_dup_favorite;
  END;

  SAVEPOINT sp_invalid_rating;
  BEGIN
      INSERT INTO answer_feedback (answer_id, user_id, is_like, rating)
      VALUES (l_answer_id, l_user_a_id, 'Y', 6);
      RAISE_APPLICATION_ERROR(-20023, 'Invalid rating was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2290 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK invalid rating rejected as expected');
          ROLLBACK TO sp_invalid_rating;
  END;

  SAVEPOINT sp_invalid_answer_type;
  BEGIN
      INSERT INTO answers (question_id, answer_type, content)
      VALUES (l_question_a_id, 'BOT', 'bad answer type');
      RAISE_APPLICATION_ERROR(-20028, 'Invalid answer type was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2290 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK invalid answer type rejected as expected');
          ROLLBACK TO sp_invalid_answer_type;
  END;

  SAVEPOINT sp_invalid_fk;
  BEGIN
      INSERT INTO answers (question_id, answer_type, content)
      VALUES (-999, 'AI', 'should fail');
      RAISE_APPLICATION_ERROR(-20024, 'Invalid foreign key was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2291 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK invalid foreign key rejected as expected');
          ROLLBACK TO sp_invalid_fk;
  END;

  SAVEPOINT sp_cross_question_accept;
  BEGIN
      UPDATE questions
         SET accepted_answer_id = l_answer_id
       WHERE question_id = l_question_b_id;
      RAISE_APPLICATION_ERROR(-20030, 'Cross-question accepted answer was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2291 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK cross-question accepted answer rejected as expected');
          ROLLBACK TO sp_cross_question_accept;
  END;

  SAVEPOINT sp_dup_feedback;
  BEGIN
      INSERT INTO answer_feedback (answer_id, user_id, is_like, rating, comment_text)
      VALUES (l_answer_id, l_user_b_id, 'N', 1, 'Second feedback by same user');
      RAISE_APPLICATION_ERROR(-20026, 'Duplicate feedback was allowed');
  EXCEPTION
      WHEN DUP_VAL_ON_INDEX THEN
          DBMS_OUTPUT.PUT_LINE('CHECK duplicate feedback rejected as expected');
          ROLLBACK TO sp_dup_feedback;
  END;

  SAVEPOINT sp_invalid_login_result;
  BEGIN
      INSERT INTO login_log (user_id, result)
      VALUES (l_user_a_id, 'PENDING');
      RAISE_APPLICATION_ERROR(-20029, 'Invalid login result was allowed');
  EXCEPTION
      WHEN OTHERS THEN
          IF SQLCODE != -2290 THEN
              RAISE;
          END IF;
          DBMS_OUTPUT.PUT_LINE('CHECK invalid login result rejected as expected');
          ROLLBACK TO sp_invalid_login_result;
  END;

  DBMS_OUTPUT.PUT_LINE('=== TRIGGER UPDATE/DELETE TESTS ===');

  UPDATE browse_history
     SET question_id = l_question_b_id
   WHERE user_id = l_user_b_id
     AND question_id = l_question_a_id;

  COMMIT;

  SELECT view_count INTO l_view_count
    FROM questions
   WHERE question_id = l_question_a_id;
  assert_number('question_a.view_count.after_move', l_view_count, 0);

  SELECT view_count INTO l_view_count
    FROM questions
   WHERE question_id = l_question_b_id;
  assert_number('question_b.view_count.after_move', l_view_count, 1);

  DELETE FROM favorites
   WHERE user_id = l_user_b_id
     AND question_id = l_question_a_id;

  COMMIT;

  SELECT favorite_count INTO l_favorite_count
    FROM questions
   WHERE question_id = l_question_a_id;
  assert_number('question_a.favorite_count.after_delete', l_favorite_count, 0);

  UPDATE answer_feedback
     SET is_like = 'N',
         rating = 2
   WHERE answer_id = l_answer_id
     AND user_id = l_user_b_id;

  COMMIT;

  SELECT like_count, dislike_count, avg_rating
    INTO l_like_count, l_dislike_count, l_avg_rating
    FROM answers
   WHERE answer_id = l_answer_id;

  assert_number('answer.like_count.after_update', l_like_count, 0);
  assert_number('answer.dislike_count.after_update', l_dislike_count, 1);
  assert_number('answer.avg_rating.after_update', l_avg_rating, 2);

  DELETE FROM answer_feedback
   WHERE answer_id = l_answer_id
     AND user_id = l_user_b_id;

  COMMIT;

  SELECT like_count, dislike_count, avg_rating
    INTO l_like_count, l_dislike_count, l_avg_rating
    FROM answers
   WHERE answer_id = l_answer_id;

  assert_number('answer.like_count.after_delete', l_like_count, 0);
  assert_number('answer.dislike_count.after_delete', l_dislike_count, 0);

  IF l_avg_rating IS NOT NULL THEN
      RAISE_APPLICATION_ERROR(-20025, 'Expected avg_rating to become NULL after deleting all feedback');
  END IF;
  DBMS_OUTPUT.PUT_LINE('CHECK answer.avg_rating.after_delete actual=NULL expected=NULL');

  UPDATE questions
     SET accepted_answer_id = NULL,
         status = 'OPEN'
   WHERE question_id = l_question_a_id;

  COMMIT;

  DELETE FROM answers
   WHERE answer_id = l_answer_id;

  COMMIT;

  SELECT answer_count INTO l_answer_count
    FROM questions
   WHERE question_id = l_question_a_id;
  assert_number('question_a.answer_count.after_delete', l_answer_count, 0);

  DBMS_OUTPUT.PUT_LINE('=== PROCEDURE IDEMPOTENCY TESTS ===');

  qa_app_pkg.rebuild_user_tag_profile(l_user_a_id);
  qa_app_pkg.rebuild_user_tag_profile(l_user_a_id);

  SELECT COUNT(*), ROUND(NVL(SUM(weight), 0), 2)
    INTO l_profile_rows, l_total_weight
    FROM user_tag_profile
   WHERE user_id = l_user_a_id;

  assert_number('user_a.profile_rows.after_rebuild_twice', l_profile_rows, 1);
  assert_number('user_a.profile_weight.after_rebuild_twice', l_total_weight, 5);

  qa_app_pkg.generate_recommendations(l_user_a_id, 5);
  qa_app_pkg.generate_recommendations(l_user_a_id, 5);

  SELECT COUNT(*)
    INTO l_active_recs
    FROM recommendations
   WHERE user_id = l_user_a_id
     AND status = 'ACTIVE';

  SELECT COUNT(*)
    INTO l_expired_recs
    FROM recommendations
   WHERE user_id = l_user_a_id
     AND status = 'EXPIRED';

  assert_number('user_a.active_recommendations.after_rerun', l_active_recs, 1);
  assert_number('user_a.expired_recommendations.after_rerun', l_expired_recs, 2);

  l_rec_score := qa_app_pkg.get_recommendation_score(l_user_a_id, l_question_b_id);
  assert_number('get_recommendation_score', l_rec_score, 5.01);

  DBMS_OUTPUT.PUT_LINE('=== ALL VALIDATION CHECKS PASSED ===');
END;
/
EXIT
"@

$cleanupSql = @"
WHENEVER SQLERROR CONTINUE
ALTER SESSION SET CONTAINER = FREEPDB1;
DROP USER $tempUser CASCADE;
EXIT
"@

try {
    Write-Host "Creating temporary validation schema: $tempUser"
    $rootSql | docker exec -i $ContainerName sqlplus -s / as sysdba
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create temporary validation schema."
    }

    foreach ($sqlFile in $resolvedSqlFiles) {
        $fileName = Split-Path -Path $sqlFile -Leaf
        $containerPath = "${ContainerName}:/tmp/$fileName"
        Write-Host "Copying $sqlFile to container..."
        docker cp $sqlFile $containerPath
        if ($LASTEXITCODE -ne 0) {
            throw "docker cp failed for $sqlFile"
        }
    }

    Write-Host "Running Oracle schema validation..."
    $validationSql | docker exec -i $ContainerName sqlplus -L -s /nolog
    if ($LASTEXITCODE -ne 0) {
        throw "Oracle schema validation failed."
    }

    Write-Host "Oracle schema validation completed successfully."
}
finally {
    Write-Host "Cleaning up temporary validation schema..."
    $cleanupSql | docker exec -i $ContainerName sqlplus -s / as sysdba | Out-Null
}
