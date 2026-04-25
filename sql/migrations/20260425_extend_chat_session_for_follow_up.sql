SET DEFINE OFF

PROMPT Extending CHAT_SESSION for follow-up conversations...

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_tab_columns
     WHERE table_name = 'CHAT_SESSION'
       AND column_name = 'QUESTION_ID';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE chat_session ADD (question_id NUMBER)';
        DBMS_OUTPUT.PUT_LINE('Added CHAT_SESSION.QUESTION_ID.');
    END IF;

    SELECT COUNT(*)
      INTO v_count
      FROM user_tab_columns
     WHERE table_name = 'CHAT_SESSION'
       AND column_name = 'SEED_ANSWER_ID';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE chat_session ADD (seed_answer_id NUMBER)';
        DBMS_OUTPUT.PUT_LINE('Added CHAT_SESSION.SEED_ANSWER_ID.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_constraints
     WHERE table_name = 'CHAT_SESSION'
       AND constraint_name = 'FK_CHAT_SESSION_QUESTION';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE '
            ALTER TABLE chat_session
            ADD CONSTRAINT fk_chat_session_question
                FOREIGN KEY (question_id) REFERENCES questions (question_id)
        ';
        DBMS_OUTPUT.PUT_LINE('Added FK_CHAT_SESSION_QUESTION.');
    END IF;

    SELECT COUNT(*)
      INTO v_count
      FROM user_constraints
     WHERE table_name = 'CHAT_SESSION'
       AND constraint_name = 'FK_CHAT_SESSION_SEED_ANSWER';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE '
            ALTER TABLE chat_session
            ADD CONSTRAINT fk_chat_session_seed_answer
                FOREIGN KEY (question_id, seed_answer_id)
                REFERENCES answers (question_id, answer_id)
        ';
        DBMS_OUTPUT.PUT_LINE('Added FK_CHAT_SESSION_SEED_ANSWER.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_tables
     WHERE table_name = 'CHAT_SESSION';

    IF v_count = 1 THEN
        EXECUTE IMMEDIATE '
            UPDATE chat_session
               SET question_id = question_id
             WHERE 1 = 0
        ';
    END IF;
END;
/

DECLARE
    v_null_rows NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_null_rows
      FROM chat_session
     WHERE question_id IS NULL
        OR seed_answer_id IS NULL;

    IF v_null_rows = 0 THEN
        BEGIN
            EXECUTE IMMEDIATE 'ALTER TABLE chat_session MODIFY (question_id NOT NULL)';
            DBMS_OUTPUT.PUT_LINE('Set CHAT_SESSION.QUESTION_ID NOT NULL.');
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('Skipped NOT NULL on QUESTION_ID: ' || SQLERRM);
        END;

        BEGIN
            EXECUTE IMMEDIATE 'ALTER TABLE chat_session MODIFY (seed_answer_id NOT NULL)';
            DBMS_OUTPUT.PUT_LINE('Set CHAT_SESSION.SEED_ANSWER_ID NOT NULL.');
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('Skipped NOT NULL on SEED_ANSWER_ID: ' || SQLERRM);
        END;
    ELSE
        DBMS_OUTPUT.PUT_LINE('Existing CHAT_SESSION rows without anchors detected; NOT NULL constraint skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_indexes
     WHERE table_name = 'CHAT_SESSION'
       AND index_name = 'IDX_CHAT_SESSION_QUESTION_ID';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX idx_chat_session_question_id ON chat_session (question_id)';
        DBMS_OUTPUT.PUT_LINE('Added IDX_CHAT_SESSION_QUESTION_ID.');
    END IF;

    SELECT COUNT(*)
      INTO v_count
      FROM user_indexes
     WHERE table_name = 'CHAT_SESSION'
       AND index_name = 'IDX_CHAT_SESSION_SEED_ANSWER_ID';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX idx_chat_session_seed_answer_id ON chat_session (seed_answer_id)';
        DBMS_OUTPUT.PUT_LINE('Added IDX_CHAT_SESSION_SEED_ANSWER_ID.');
    END IF;
END;
/

PROMPT CHAT_SESSION follow-up extension completed.
