-- triggers.sql
-- Triggers for statistics maintenance and log synchronization

SET DEFINE OFF

CREATE OR REPLACE TRIGGER trg_answers_sync_question_stats
FOR INSERT OR UPDATE OF question_id OR DELETE ON answers
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
            qa_app_pkg.sync_question_statistics(g_question_ids(i));
        END LOOP;
    END AFTER STATEMENT;
END trg_answers_sync_question_stats;
/

CREATE OR REPLACE TRIGGER trg_favorites_sync_question_stats
FOR INSERT OR UPDATE OF question_id OR DELETE ON favorites
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
            qa_app_pkg.sync_question_statistics(g_question_ids(i));
        END LOOP;
    END AFTER STATEMENT;
END trg_favorites_sync_question_stats;
/

CREATE OR REPLACE TRIGGER trg_browse_history_sync_question_stats
FOR INSERT OR UPDATE OF question_id OR DELETE ON browse_history
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
            qa_app_pkg.sync_question_statistics(g_question_ids(i));
        END LOOP;
    END AFTER STATEMENT;
END trg_browse_history_sync_question_stats;
/

CREATE OR REPLACE TRIGGER trg_answer_feedback_refresh_stats
FOR INSERT OR UPDATE OF answer_id, is_like, rating OR DELETE ON answer_feedback
COMPOUND TRIGGER
    TYPE t_number_list IS TABLE OF NUMBER INDEX BY PLS_INTEGER;
    g_answer_ids t_number_list;
    g_count      PLS_INTEGER := 0;

    PROCEDURE add_answer_id(
        p_answer_id IN NUMBER
    ) IS
        l_exists BOOLEAN := FALSE;
    BEGIN
        IF p_answer_id IS NULL THEN
            RETURN;
        END IF;

        FOR i IN 1 .. g_count LOOP
            IF g_answer_ids(i) = p_answer_id THEN
                l_exists := TRUE;
                EXIT;
            END IF;
        END LOOP;

        IF NOT l_exists THEN
            g_count := g_count + 1;
            g_answer_ids(g_count) := p_answer_id;
        END IF;
    END add_answer_id;

    AFTER EACH ROW IS
    BEGIN
        IF INSERTING OR UPDATING THEN
            add_answer_id(:NEW.answer_id);
        END IF;

        IF DELETING OR UPDATING THEN
            add_answer_id(:OLD.answer_id);
        END IF;
    END AFTER EACH ROW;

    AFTER STATEMENT IS
    BEGIN
        FOR i IN 1 .. g_count LOOP
            qa_app_pkg.refresh_answer_feedback_stats(g_answer_ids(i));
        END LOOP;
    END AFTER STATEMENT;
END trg_answer_feedback_refresh_stats;
/

CREATE OR REPLACE TRIGGER trg_login_log_update_last_login
AFTER INSERT ON login_log
FOR EACH ROW
BEGIN
    IF :NEW.result = 'SUCCESS' THEN
        UPDATE users
           SET last_login_time = :NEW.login_time
         WHERE user_id = :NEW.user_id;
    END IF;
END trg_login_log_update_last_login;
/
