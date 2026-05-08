-- Add composite indexes for homepage list, tag sidebar, and recommendation queries.

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_indexes
     WHERE index_name = 'IDX_QUESTIONS_STATUS_ASK_QID';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_questions_status_ask_qid
                ON questions(status, ask_time DESC, question_id DESC)
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
     WHERE index_name = 'IDX_QUESTIONS_CAT_STATUS_ASK';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_questions_cat_status_ask
                ON questions(category_id, status, ask_time DESC, question_id DESC)
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
     WHERE index_name = 'IDX_QUESTION_TAGS_TAG_QUESTION';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_question_tags_tag_question
                ON question_tags(tag_id, question_id)
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
     WHERE index_name = 'IDX_RECS_USER_STATUS_SCORE';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_recs_user_status_score
                ON recommendations(user_id, status, rec_score DESC, rec_id DESC)
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
     WHERE index_name = 'IDX_TAGS_STATUS_NAME';

    IF v_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            CREATE INDEX idx_tags_status_name
                ON tags(status, tag_name)
        ]';
    END IF;
END;
/
