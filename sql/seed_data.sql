-- seed_data.sql
-- Persistent demo data for the AI QA application schema

SET DEFINE OFF

PROMPT Loading persistent demo data...

DECLARE
    l_owner_user_id     NUMBER;
    l_reader_user_id    NUMBER;
    l_oracle_category   NUMBER;
    l_ai_category       NUMBER;
    l_oracle_tag        NUMBER;
    l_docker_tag        NUMBER;
    l_deepseek_tag      NUMBER;
    l_recommend_tag     NUMBER;
    l_question_1_id     NUMBER;
    l_question_2_id     NUMBER;
    l_answer_1_id       NUMBER;
    l_question_1_title  VARCHAR2(200 CHAR) := UNISTR('\5982\4F55\5728 Docker \4E2D\7A33\5B9A\8FD0\884C Oracle 26ai\FF1F');
    l_question_1_body   VARCHAR2(500 CHAR) := UNISTR('\6211\5DF2\7ECF\5B89\88C5\4E86 Docker Desktop\FF0C\60F3\628A Oracle 26ai \8DD1\8D77\6765\5E76\957F\671F\4FDD\7559\6570\636E\FF0C\5E94\8BE5\6CE8\610F\54EA\4E9B\914D\7F6E\FF1F');
    l_question_2_title  VARCHAR2(200 CHAR) := UNISTR('\5982\4F55\7528 DeepSeek API \63A5\5165\5355\8F6E\95EE\7B54\FF1F');
    l_question_2_body   VARCHAR2(500 CHAR) := UNISTR('\6211\5DF2\7ECF\6709 DeepSeek API Key\FF0C\60F3\5728\540E\7AEF\5B8C\6210\4E00\6B21\63D0\95EE\3001\8C03\7528\6A21\578B\548C\56DE\7B54\843D\5E93\FF0C\6700\5C0F\95ED\73AF\5E94\8BE5\600E\4E48\8BBE\8BA1\FF1F');
    l_answer_1_body     VARCHAR2(1000 CHAR) := UNISTR('\5EFA\8BAE\4F18\5148\4F7F\7528 Docker Compose \56FA\5B9A\7AEF\53E3\3001\6570\636E\5377\548C\73AF\5883\53D8\91CF\FF0C\5E76\5728\9996\6B21\542F\52A8\540E\901A\8FC7\5065\5EB7\68C0\67E5\786E\8BA4\6570\636E\5E93\72B6\6001\3002\6570\636E\957F\671F\4FDD\7559\5E94\4F9D\8D56\6302\8F7D\5377\FF0C\800C\4E0D\662F\4E34\65F6\5BB9\5668\6587\4EF6\7CFB\7EDF\3002');
    l_answer_2_body     VARCHAR2(1000 CHAR) := UNISTR('\6700\5C0F\95ED\73AF\5EFA\8BAE\5305\62EC\95EE\9898\5165\5E93\3001\8C03\7528 DeepSeek\3001\56DE\7B54\5165\5E93\3001Prompt \65E5\5FD7\8BB0\5F55\548C\95EE\9898\8BE6\60C5\63A5\53E3\3002');
    l_feedback_comment  VARCHAR2(500 CHAR) := UNISTR('\8FD9\6761\56DE\7B54\9002\5408\505A\8BFE\7A0B\6F14\793A\3002');

    PROCEDURE ensure_user(
        p_username      IN VARCHAR2,
        p_password_hash IN VARCHAR2,
        p_nickname      IN VARCHAR2,
        p_email         IN VARCHAR2
    ) IS
        l_count NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO l_count
          FROM users
         WHERE username = p_username;

        IF l_count = 0 THEN
            INSERT INTO users (
                username,
                password_hash,
                nickname,
                email,
                role,
                status
            ) VALUES (
                p_username,
                p_password_hash,
                p_nickname,
                p_email,
                'USER',
                'ACTIVE'
            );
        END IF;
    END ensure_user;

    PROCEDURE ensure_category(
        p_category_name IN VARCHAR2,
        p_description   IN VARCHAR2
    ) IS
        l_count NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO l_count
          FROM categories
         WHERE category_name = p_category_name;

        IF l_count = 0 THEN
            INSERT INTO categories (
                category_name,
                description,
                status
            ) VALUES (
                p_category_name,
                p_description,
                'ACTIVE'
            );
        END IF;
    END ensure_category;

    PROCEDURE ensure_tag(
        p_tag_name IN VARCHAR2
    ) IS
        l_count NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO l_count
          FROM tags
         WHERE tag_name = p_tag_name;

        IF l_count = 0 THEN
            INSERT INTO tags (tag_name)
            VALUES (p_tag_name);
        END IF;
    END ensure_tag;

    FUNCTION get_user_id(
        p_username IN VARCHAR2
    ) RETURN NUMBER IS
        l_user_id NUMBER;
    BEGIN
        SELECT user_id
          INTO l_user_id
          FROM users
         WHERE username = p_username;

        RETURN l_user_id;
    END get_user_id;

    FUNCTION get_category_id(
        p_category_name IN VARCHAR2
    ) RETURN NUMBER IS
        l_category_id NUMBER;
    BEGIN
        SELECT category_id
          INTO l_category_id
          FROM categories
         WHERE category_name = p_category_name;

        RETURN l_category_id;
    END get_category_id;

    FUNCTION get_tag_id(
        p_tag_name IN VARCHAR2
    ) RETURN NUMBER IS
        l_tag_id NUMBER;
    BEGIN
        SELECT tag_id
          INTO l_tag_id
          FROM tags
         WHERE tag_name = p_tag_name;

        RETURN l_tag_id;
    END get_tag_id;

    FUNCTION get_question_id(
        p_username IN VARCHAR2,
        p_title    IN VARCHAR2
    ) RETURN NUMBER IS
        l_question_id NUMBER;
    BEGIN
        SELECT q.question_id
          INTO l_question_id
          FROM questions q
          JOIN users u
            ON u.user_id = q.user_id
         WHERE u.username = p_username
           AND q.title = p_title;

        RETURN l_question_id;
    END get_question_id;

    FUNCTION get_answer_id(
        p_question_id IN NUMBER,
        p_answer_type IN VARCHAR2
    ) RETURN NUMBER IS
        l_answer_id NUMBER;
    BEGIN
        SELECT answer_id
          INTO l_answer_id
          FROM answers
         WHERE question_id = p_question_id
           AND answer_type = p_answer_type
           AND ROWNUM = 1;

        RETURN l_answer_id;
    END get_answer_id;

BEGIN
    -- Reset the dedicated demo dataset so rerunning the script repairs existing
    -- seed rows, including any previously garbled Chinese content.
    DELETE FROM recommendations
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM user_tag_profile
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM login_log
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM answer_feedback
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM favorites
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM browse_history
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM search_history
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM operation_log
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username IN ('demo_reader', 'demo_owner')
     );

    DELETE FROM ai_prompt_log
     WHERE question_id IN (
        SELECT question_id
          FROM questions
         WHERE user_id IN (
            SELECT user_id
              FROM users
             WHERE username = 'demo_owner'
         )
     );

    DELETE FROM question_tags
     WHERE question_id IN (
        SELECT question_id
          FROM questions
         WHERE user_id IN (
            SELECT user_id
              FROM users
             WHERE username = 'demo_owner'
         )
     );

    UPDATE questions
       SET accepted_answer_id = NULL
     WHERE accepted_answer_id IS NOT NULL
       AND user_id IN (
        SELECT user_id
          FROM users
         WHERE username = 'demo_owner'
     );

    DELETE FROM answers
     WHERE question_id IN (
        SELECT question_id
          FROM questions
         WHERE user_id IN (
            SELECT user_id
              FROM users
             WHERE username = 'demo_owner'
         )
     );

    DELETE FROM questions
     WHERE user_id IN (
        SELECT user_id
          FROM users
         WHERE username = 'demo_owner'
     );

    COMMIT;

    ensure_user(
        p_username      => 'demo_owner',
        p_password_hash => 'demo_owner_hash',
        p_nickname      => 'Demo Owner',
        p_email         => 'demo_owner@example.com'
    );

    ensure_user(
        p_username      => 'demo_reader',
        p_password_hash => 'demo_reader_hash',
        p_nickname      => 'Demo Reader',
        p_email         => 'demo_reader@example.com'
    );

    ensure_category(
        p_category_name => 'oracle',
        p_description   => 'Oracle database related questions'
    );

    ensure_category(
        p_category_name => 'ai',
        p_description   => 'AI API and prompt engineering questions'
    );

    ensure_tag('oracle');
    ensure_tag('docker');
    ensure_tag('deepseek');
    ensure_tag('recommendation');

    l_owner_user_id   := get_user_id('demo_owner');
    l_reader_user_id  := get_user_id('demo_reader');
    l_oracle_category := get_category_id('oracle');
    l_ai_category     := get_category_id('ai');
    l_oracle_tag      := get_tag_id('oracle');
    l_docker_tag      := get_tag_id('docker');
    l_deepseek_tag    := get_tag_id('deepseek');
    l_recommend_tag   := get_tag_id('recommendation');

    INSERT INTO questions (
        user_id,
        category_id,
        title,
        content,
        status
    )
    SELECT
        l_owner_user_id,
        l_oracle_category,
        l_question_1_title,
        l_question_1_body,
        'OPEN'
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM questions
         WHERE user_id = l_owner_user_id
           AND title = l_question_1_title
     );

    INSERT INTO questions (
        user_id,
        category_id,
        title,
        content,
        status
    )
    SELECT
        l_owner_user_id,
        l_ai_category,
        l_question_2_title,
        l_question_2_body,
        'OPEN'
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM questions
         WHERE user_id = l_owner_user_id
           AND title = l_question_2_title
     );

    l_question_1_id := get_question_id('demo_owner', l_question_1_title);
    l_question_2_id := get_question_id('demo_owner', l_question_2_title);

    INSERT INTO question_tags (question_id, tag_id)
    SELECT l_question_1_id, l_oracle_tag
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM question_tags
         WHERE question_id = l_question_1_id
           AND tag_id = l_oracle_tag
     );

    INSERT INTO question_tags (question_id, tag_id)
    SELECT l_question_1_id, l_docker_tag
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM question_tags
         WHERE question_id = l_question_1_id
           AND tag_id = l_docker_tag
     );

    INSERT INTO question_tags (question_id, tag_id)
    SELECT l_question_2_id, l_deepseek_tag
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM question_tags
         WHERE question_id = l_question_2_id
           AND tag_id = l_deepseek_tag
     );

    INSERT INTO question_tags (question_id, tag_id)
    SELECT l_question_2_id, l_recommend_tag
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM question_tags
         WHERE question_id = l_question_2_id
           AND tag_id = l_recommend_tag
     );

    INSERT INTO answers (
        question_id,
        user_id,
        answer_type,
        provider_name,
        content,
        model_name
    )
    SELECT
        l_question_1_id,
        NULL,
        'AI',
        'DeepSeek',
        l_answer_1_body,
        'deepseek-chat'
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM answers
         WHERE question_id = l_question_1_id
           AND answer_type = 'AI'
     );

    INSERT INTO answers (
        question_id,
        user_id,
        answer_type,
        provider_name,
        content,
        model_name
    )
    SELECT
        l_question_2_id,
        l_owner_user_id,
        'MANUAL',
        NULL,
        l_answer_2_body,
        NULL
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM answers
         WHERE question_id = l_question_2_id
           AND answer_type = 'MANUAL'
     );

    l_answer_1_id := get_answer_id(l_question_1_id, 'AI');

    INSERT INTO favorites (
        user_id,
        question_id
    )
    SELECT
        l_reader_user_id,
        l_question_1_id
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM favorites
         WHERE user_id = l_reader_user_id
           AND question_id = l_question_1_id
     );

    INSERT INTO browse_history (
        user_id,
        question_id,
        duration,
        click_depth
    )
    SELECT
        l_reader_user_id,
        l_question_1_id,
        180,
        3
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM browse_history
         WHERE user_id = l_reader_user_id
           AND question_id = l_question_1_id
     );

    INSERT INTO answer_feedback (
        answer_id,
        user_id,
        is_like,
        rating,
        comment_text
    )
    SELECT
        l_answer_1_id,
        l_reader_user_id,
        'Y',
        4.5,
        l_feedback_comment
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM answer_feedback
         WHERE answer_id = l_answer_1_id
           AND user_id = l_reader_user_id
     );

    INSERT INTO login_log (
        user_id,
        result
    )
    SELECT
        l_reader_user_id,
        'SUCCESS'
      FROM dual
     WHERE NOT EXISTS (
        SELECT 1
          FROM login_log
         WHERE user_id = l_reader_user_id
           AND result = 'SUCCESS'
     );

    COMMIT;

    qa_app_pkg.rebuild_user_tag_profile(l_reader_user_id);
    qa_app_pkg.generate_recommendations(l_reader_user_id, 10);
    COMMIT;
END;
/

PROMPT Persistent demo data loaded successfully.
