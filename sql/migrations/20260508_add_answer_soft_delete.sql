SET DEFINE OFF

PROMPT Applying migration: add soft delete fields for answers...

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_tab_cols
     WHERE table_name = 'ANSWERS'
       AND column_name = 'STATUS';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE answers
            ADD (status VARCHAR2(20 CHAR) DEFAULT 'ACTIVE' NOT NULL)
        ]';
        DBMS_OUTPUT.PUT_LINE('Added ANSWERS.STATUS column.');
    END IF;
END;
/

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_tab_cols
     WHERE table_name = 'ANSWERS'
       AND column_name = 'DELETE_TIME';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE answers ADD (delete_time DATE)';
        DBMS_OUTPUT.PUT_LINE('Added ANSWERS.DELETE_TIME column.');
    END IF;
END;
/

UPDATE answers
   SET status = 'ACTIVE'
 WHERE status IS NULL;

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'ANSWERS'
       AND constraint_name = 'CK_ANSWERS_STATUS';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE answers
            ADD CONSTRAINT ck_answers_status
            CHECK (status IN ('ACTIVE', 'HIDDEN', 'DELETED'))
        ]';
        DBMS_OUTPUT.PUT_LINE('Added CK_ANSWERS_STATUS.');
    END IF;
END;
/

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_indexes
     WHERE index_name = 'IDX_ANSWERS_STATUS';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX idx_answers_status ON answers (status)';
        DBMS_OUTPUT.PUT_LINE('Created IDX_ANSWERS_STATUS.');
    END IF;
END;
/

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'ANSWERS'
       AND constraint_name = 'CK_ANSWERS_DELETE_TIME';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE answers
            ADD CONSTRAINT ck_answers_delete_time
            CHECK (delete_time IS NULL OR delete_time >= generate_time)
        ]';
        DBMS_OUTPUT.PUT_LINE('Added CK_ANSWERS_DELETE_TIME.');
    END IF;
END;
/

CREATE OR REPLACE TRIGGER trg_answers_sync_question_stats
FOR INSERT OR UPDATE OF question_id, status OR DELETE ON answers
COMPOUND TRIGGER
    TYPE t_number_list IS TABLE OF NUMBER INDEX BY PLS_INTEGER;
    g_question_ids t_number_list;
    g_count        PLS_INTEGER := 0;

    PROCEDURE add_question_id(
        p_question_id IN NUMBER
    ) IS
        l_exists BOOLEAN := FALSE;
    BEGIN
        IF p_question_id IS NULL THEN
            RETURN;
        END IF;

        FOR i IN 1 .. g_count LOOP
            IF g_question_ids(i) = p_question_id THEN
                l_exists := TRUE;
                EXIT;
            END IF;
        END LOOP;

        IF NOT l_exists THEN
            g_count := g_count + 1;
            g_question_ids(g_count) := p_question_id;
        END IF;
    END add_question_id;

    AFTER EACH ROW IS
    BEGIN
        IF INSERTING OR UPDATING THEN
            add_question_id(:NEW.question_id);
        END IF;

        IF DELETING OR UPDATING THEN
            add_question_id(:OLD.question_id);
        END IF;
    END AFTER EACH ROW;

    AFTER STATEMENT IS
    BEGIN
        FOR i IN 1 .. g_count LOOP
            UPDATE questions q
               SET answer_count = (
                   SELECT COUNT(*)
                     FROM answers a
                    WHERE a.question_id = q.question_id
                      AND a.status = 'ACTIVE'
               )
             WHERE q.question_id = g_question_ids(i);
        END LOOP;
    END AFTER STATEMENT;
END trg_answers_sync_question_stats;
/

UPDATE questions q
   SET answer_count = (
       SELECT COUNT(*)
         FROM answers a
        WHERE a.question_id = q.question_id
          AND a.status = 'ACTIVE'
   );

PROMPT Refreshing answer-related reporting views...

CREATE OR REPLACE VIEW v_answer_quality_summary AS
SELECT
    a.answer_id,
    a.question_id,
    q.title AS question_title,
    q.status AS question_status,
    a.user_id,
    u.username AS author_username,
    u.nickname AS author_nickname,
    a.answer_type,
    a.provider_name,
    a.status AS answer_status,
    a.delete_time,
    a.generate_time,
    a.like_count,
    a.dislike_count,
    a.avg_rating,
    CASE
        WHEN q.accepted_answer_id = a.answer_id THEN 'Y'
        ELSE 'N'
    END AS is_accepted,
    NVL(comment_stats.comment_count, 0) AS active_comment_count,
    NVL(feedback_stats.feedback_count, 0) AS feedback_count
FROM answers a
JOIN questions q
  ON q.question_id = a.question_id
LEFT JOIN users u
  ON u.user_id = a.user_id
LEFT JOIN (
    SELECT
        answer_id,
        COUNT(*) AS comment_count
    FROM answer_comments
    WHERE status = 'ACTIVE'
    GROUP BY answer_id
) comment_stats
  ON comment_stats.answer_id = a.answer_id
LEFT JOIN (
    SELECT
        answer_id,
        COUNT(*) AS feedback_count
    FROM answer_feedback
    GROUP BY answer_id
) feedback_stats
  ON feedback_stats.answer_id = a.answer_id
WHERE q.status <> 'DELETED'
  AND a.status <> 'DELETED';

CREATE OR REPLACE VIEW v_user_activity_summary AS
SELECT
    u.user_id,
    u.username,
    u.nickname,
    u.role,
    u.status,
    u.register_time,
    u.last_login_time,
    NVL(q_stats.total_questions, 0) AS total_questions,
    NVL(q_stats.open_questions, 0) AS open_questions,
    NVL(q_stats.resolved_questions, 0) AS resolved_questions,
    NVL(a_stats.total_answers, 0) AS total_answers,
    NVL(a_stats.manual_answers, 0) AS manual_answers,
    NVL(c_stats.active_comments, 0) AS active_comments,
    NVL(f_stats.total_favorites, 0) AS total_favorites,
    NVL(b_stats.total_browses, 0) AS total_browses,
    NVL(s_stats.total_searches, 0) AS total_searches,
    NVL(p_stats.profile_tag_count, 0) AS profile_tag_count,
    NVL(p_stats.total_profile_weight, 0) AS total_profile_weight,
    NVL(r_stats.active_recommendations, 0) AS active_recommendations
FROM users u
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_questions,
        COUNT(CASE WHEN status = 'OPEN' THEN 1 END) AS open_questions,
        COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END) AS resolved_questions
    FROM questions
    WHERE status <> 'DELETED'
    GROUP BY user_id
) q_stats
  ON q_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_answers,
        COUNT(CASE WHEN answer_type = 'MANUAL' THEN 1 END) AS manual_answers
    FROM answers
    WHERE user_id IS NOT NULL
      AND status = 'ACTIVE'
    GROUP BY user_id
) a_stats
  ON a_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS active_comments
    FROM answer_comments
    WHERE status = 'ACTIVE'
    GROUP BY user_id
) c_stats
  ON c_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_favorites
    FROM favorites
    GROUP BY user_id
) f_stats
  ON f_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_browses
    FROM browse_history
    GROUP BY user_id
) b_stats
  ON b_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_searches
    FROM search_history
    GROUP BY user_id
) s_stats
  ON s_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS profile_tag_count,
        ROUND(SUM(weight), 2) AS total_profile_weight
    FROM user_tag_profile
    GROUP BY user_id
) p_stats
  ON p_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS active_recommendations
    FROM recommendations
    WHERE status = 'ACTIVE'
    GROUP BY user_id
) r_stats
  ON r_stats.user_id = u.user_id;

COMMIT;

PROMPT Migration completed successfully.
