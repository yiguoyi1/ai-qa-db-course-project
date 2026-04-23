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

UPDATE questions q
   SET accepted_answer_id = NULL,
       status = CASE
           WHEN q.status = 'RESOLVED' THEN 'OPEN'
           ELSE q.status
       END
 WHERE q.accepted_answer_id IS NOT NULL
   AND NOT EXISTS (
       SELECT 1
         FROM answers a
        WHERE a.answer_id = q.accepted_answer_id
          AND a.question_id = q.question_id
   );

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'ANSWERS'
       AND constraint_name = 'UQ_ANSWERS_QUESTION_ANSWER';

    IF l_exists = 0 THEN
        EXECUTE IMMEDIATE '
            ALTER TABLE answers
            ADD CONSTRAINT uq_answers_question_answer
            UNIQUE (question_id, answer_id)
        ';
        DBMS_OUTPUT.PUT_LINE('Added UQ_ANSWERS_QUESTION_ANSWER.');
    END IF;
END;
/

DECLARE
    l_column_signature VARCHAR2(200);
BEGIN
    SELECT LISTAGG(column_name, ',') WITHIN GROUP (ORDER BY position)
      INTO l_column_signature
      FROM user_cons_columns
     WHERE table_name = 'QUESTIONS'
       AND constraint_name = 'FK_QUESTIONS_ACCEPTED_ANSWER';

    IF l_column_signature IS NOT NULL
       AND l_column_signature <> 'QUESTION_ID,ACCEPTED_ANSWER_ID' THEN
        EXECUTE IMMEDIATE 'ALTER TABLE questions DROP CONSTRAINT fk_questions_accepted_answer';
        DBMS_OUTPUT.PUT_LINE('Dropped legacy FK_QUESTIONS_ACCEPTED_ANSWER.');
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
            FOREIGN KEY (question_id, accepted_answer_id)
            REFERENCES answers (question_id, answer_id)
        ';
        DBMS_OUTPUT.PUT_LINE('Added FK_QUESTIONS_ACCEPTED_ANSWER.');
    END IF;
END;
/

COMMIT;

PROMPT Migration completed successfully.
