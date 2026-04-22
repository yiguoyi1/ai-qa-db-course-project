SET DEFINE OFF

PROMPT Applying migration: add questions.accepted_answer_id for accepted answers...

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_tab_cols
     WHERE table_name = 'QUESTIONS'
       AND column_name = 'ACCEPTED_ANSWER_ID';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE questions ADD (accepted_answer_id NUMBER)';
        DBMS_OUTPUT.PUT_LINE('Added QUESTIONS.ACCEPTED_ANSWER_ID column.');
    END IF;
END;
/

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'QUESTIONS'
       AND constraint_name = 'FK_QUESTIONS_ACCEPTED_ANSWER';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE '
            ALTER TABLE questions
            ADD CONSTRAINT fk_questions_accepted_answer
            FOREIGN KEY (accepted_answer_id) REFERENCES answers (answer_id)
        ';
        DBMS_OUTPUT.PUT_LINE('Added FK_QUESTIONS_ACCEPTED_ANSWER.');
    END IF;
END;
/

COMMIT;

PROMPT Migration completed successfully.
