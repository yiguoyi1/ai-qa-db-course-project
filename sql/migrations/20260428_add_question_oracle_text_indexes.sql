-- Optional Oracle Text indexes for faster keyword search.
-- Apply this migration as APP_USER, then set SEARCH_USE_ORACLE_TEXT=true.

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_indexes
     WHERE index_name = 'IDX_QUESTIONS_TITLE_TEXT';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_questions_title_text
                ON questions(title)
                INDEXTYPE IS CTXSYS.CONTEXT
                PARAMETERS ('SYNC (ON COMMIT)')
        ]';
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_indexes
     WHERE index_name = 'IDX_QUESTIONS_CONTENT_TEXT';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_questions_content_text
                ON questions(content)
                INDEXTYPE IS CTXSYS.CONTEXT
                PARAMETERS ('SYNC (ON COMMIT)')
        ]';
    END IF;
END;
/
