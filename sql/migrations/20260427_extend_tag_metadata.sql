SET DEFINE OFF

PROMPT Applying migration: extend tag metadata and question tag source...

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'TAGS'
       AND column_name = 'SOURCE';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD (source VARCHAR2(20 CHAR) DEFAULT 'SYSTEM')
        ]';
        EXECUTE IMMEDIATE q'[
            UPDATE tags
               SET source = 'SYSTEM'
             WHERE source IS NULL
        ]';
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            MODIFY (source NOT NULL)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'TAGS'
       AND column_name = 'STATUS';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD (status VARCHAR2(20 CHAR) DEFAULT 'ACTIVE')
        ]';
        EXECUTE IMMEDIATE q'[
            UPDATE tags
               SET status = 'ACTIVE'
             WHERE status IS NULL
        ]';
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            MODIFY (status NOT NULL)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'TAGS'
       AND column_name = 'DESCRIPTION';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD (description VARCHAR2(200 CHAR))
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'TAGS'
       AND column_name = 'CREATE_USER_ID';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD (create_user_id NUMBER)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'TAGS'
       AND column_name = 'CREATE_TIME';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD (create_time DATE DEFAULT SYSDATE)
        ]';
        EXECUTE IMMEDIATE q'[
            UPDATE tags
               SET create_time = SYSDATE
             WHERE create_time IS NULL
        ]';
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            MODIFY (create_time NOT NULL)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_constraints
     WHERE table_name = 'TAGS'
       AND constraint_name = 'FK_TAGS_CREATE_USER';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD CONSTRAINT fk_tags_create_user
            FOREIGN KEY (create_user_id) REFERENCES users (user_id)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_constraints
     WHERE table_name = 'TAGS'
       AND constraint_name = 'CK_TAGS_SOURCE';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD CONSTRAINT ck_tags_source
            CHECK (source IN ('SYSTEM', 'USER', 'AI', 'ADMIN'))
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_constraints
     WHERE table_name = 'TAGS'
       AND constraint_name = 'CK_TAGS_STATUS';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE tags
            ADD CONSTRAINT ck_tags_status
            CHECK (status IN ('ACTIVE', 'PENDING', 'DISABLED'))
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'QUESTION_TAGS'
       AND column_name = 'SOURCE';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            ADD (source VARCHAR2(30 CHAR) DEFAULT 'USER_SELECTED')
        ]';
        EXECUTE IMMEDIATE q'[
            UPDATE question_tags
               SET source = 'USER_SELECTED'
             WHERE source IS NULL
        ]';
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            MODIFY (source NOT NULL)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'QUESTION_TAGS'
       AND column_name = 'CONFIDENCE_SCORE';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            ADD (confidence_score NUMBER(5,2))
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_tab_columns
     WHERE table_name = 'QUESTION_TAGS'
       AND column_name = 'CREATE_TIME';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            ADD (create_time DATE DEFAULT SYSDATE)
        ]';
        EXECUTE IMMEDIATE q'[
            UPDATE question_tags
               SET create_time = SYSDATE
             WHERE create_time IS NULL
        ]';
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            MODIFY (create_time NOT NULL)
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_constraints
     WHERE table_name = 'QUESTION_TAGS'
       AND constraint_name = 'CK_QUESTION_TAGS_SOURCE';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            ADD CONSTRAINT ck_question_tags_source
            CHECK (source IN ('USER_SELECTED', 'USER_CREATED', 'AI_MATCHED', 'AI_CREATED', 'ADMIN_ADJUSTED'))
        ]';
    END IF;
END;
/

DECLARE
    l_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_count
      FROM user_constraints
     WHERE table_name = 'QUESTION_TAGS'
       AND constraint_name = 'CK_QUESTION_TAGS_CONFIDENCE';

    IF l_count = 0 THEN
        EXECUTE IMMEDIATE q'[
            ALTER TABLE question_tags
            ADD CONSTRAINT ck_question_tags_confidence
            CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 100))
        ]';
    END IF;
END;
/

COMMIT;

PROMPT Tag metadata migration completed.
