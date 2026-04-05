SET DEFINE OFF

PROMPT Applying migration: add answers.user_id for manual community answers...

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_tab_cols
     WHERE table_name = 'ANSWERS'
       AND column_name = 'USER_ID';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE answers ADD (user_id NUMBER)';
        DBMS_OUTPUT.PUT_LINE('Added ANSWERS.USER_ID column.');
    END IF;
END;
/

UPDATE answers a
   SET user_id = (
       SELECT q.user_id
         FROM questions q
        WHERE q.question_id = a.question_id
   )
 WHERE a.answer_type = 'MANUAL'
   AND a.user_id IS NULL;

UPDATE answers
   SET provider_name = NULL,
       model_name = NULL
 WHERE answer_type = 'MANUAL'
   AND (provider_name IS NOT NULL OR model_name IS NOT NULL);

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'ANSWERS'
       AND constraint_name = 'FK_ANSWERS_USER';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE '
            ALTER TABLE answers
            ADD CONSTRAINT fk_answers_user
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        ';
        DBMS_OUTPUT.PUT_LINE('Added FK_ANSWERS_USER.');
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
       AND constraint_name = 'CK_ANSWERS_USER_PRESENCE';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE '
            ALTER TABLE answers
            ADD CONSTRAINT ck_answers_user_presence CHECK (
                (answer_type = ''MANUAL'' AND user_id IS NOT NULL)
                OR (answer_type IN (''AI'', ''SYSTEM'') AND user_id IS NULL)
            )
        ';
        DBMS_OUTPUT.PUT_LINE('Added CK_ANSWERS_USER_PRESENCE.');
    END IF;
END;
/

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_indexes
     WHERE table_name = 'ANSWERS'
       AND index_name = 'IDX_ANSWERS_USER_ID';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX idx_answers_user_id ON answers (user_id)';
        DBMS_OUTPUT.PUT_LINE('Added IDX_ANSWERS_USER_ID.');
    END IF;
END;
/

COMMIT;

PROMPT Migration completed successfully.
