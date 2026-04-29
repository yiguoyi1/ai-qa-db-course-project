SET DEFINE OFF

PROMPT Applying migration: add DELETED status for questions...

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'QUESTIONS'
       AND constraint_name = 'CK_QUESTIONS_STATUS';

    IF l_exists > 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE questions DROP CONSTRAINT ck_questions_status';
    END IF;
END;
/

ALTER TABLE questions
ADD CONSTRAINT ck_questions_status
    CHECK (status IN ('OPEN', 'RESOLVED', 'CLOSED', 'ARCHIVED', 'DELETED'));

COMMIT;

PROMPT Migration completed successfully.
