SET DEFINE OFF

PROMPT Applying migration: standardize question categories...

DECLARE
    PROCEDURE ensure_category(
        p_category_name IN VARCHAR2,
        p_description   IN VARCHAR2
    ) IS
    BEGIN
        UPDATE categories
           SET description = p_description,
               status = 'ACTIVE'
         WHERE category_name = p_category_name;

        IF SQL%ROWCOUNT = 0 THEN
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

    PROCEDURE merge_or_rename_category(
        p_old_name    IN VARCHAR2,
        p_new_name    IN VARCHAR2,
        p_description IN VARCHAR2
    ) IS
        l_old_category_id categories.category_id%TYPE;
        l_new_category_id categories.category_id%TYPE;
    BEGIN
        SELECT category_id
          INTO l_old_category_id
          FROM categories
         WHERE category_name = p_old_name;

        BEGIN
            SELECT category_id
              INTO l_new_category_id
              FROM categories
             WHERE category_name = p_new_name;

            UPDATE questions
               SET category_id = l_new_category_id
             WHERE category_id = l_old_category_id;

            UPDATE categories
               SET description = 'Merged into ' || p_new_name,
                   status = 'INACTIVE'
             WHERE category_id = l_old_category_id;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                UPDATE categories
                   SET category_name = p_new_name,
                       description = p_description,
                       status = 'ACTIVE'
                 WHERE category_id = l_old_category_id;
        END;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            NULL;
    END merge_or_rename_category;
BEGIN
    merge_or_rename_category(
        p_old_name    => 'oracle',
        p_new_name    => UNISTR('\6280\672F\5F00\53D1'),
        p_description => 'Programming, databases, development tools, and engineering practice.'
    );

    merge_or_rename_category(
        p_old_name    => 'ai',
        p_new_name    => UNISTR('\4EBA\5DE5\667A\80FD'),
        p_description => 'AI tools, model usage, prompts, and automation scenarios.'
    );

    ensure_category(UNISTR('\6280\672F\5F00\53D1'), 'Programming, databases, development tools, and engineering practice.');
    ensure_category(UNISTR('\4EBA\5DE5\667A\80FD'), 'AI tools, model usage, prompts, and automation scenarios.');
    ensure_category(UNISTR('\5B66\4E60\6559\80B2'), 'Learning methods, exams, courses, languages, and education planning.');
    ensure_category(UNISTR('\804C\573A\53D1\5C55'), 'Career growth, workplace communication, job search, and productivity.');
    ensure_category(UNISTR('\751F\6D3B\65B9\5F0F'), 'Daily life, habits, relationships, and practical experience sharing.');
    ensure_category(UNISTR('\5065\5EB7\8FD0\52A8'), 'Fitness, exercise, sleep, nutrition, and health management.');
    ensure_category(UNISTR('\65C5\884C\6237\5916'), 'Travel planning, outdoor activities, city walks, and equipment.');
    ensure_category(UNISTR('\7F8E\98DF\70F9\996A'), 'Cooking, baking, drinks, restaurants, and food choices.');
    ensure_category(UNISTR('\5BB6\5C45\6570\7801'), 'Home improvement, digital devices, smart home, and maintenance.');
    ensure_category(UNISTR('\8D22\7ECF\7406\8D22'), 'Personal finance, budgeting, saving, and consumption decisions.');
    ensure_category(UNISTR('\6587\5316\5A31\4E50'), 'Movies, music, reading, games, and leisure activities.');
    ensure_category(UNISTR('\521B\4F5C\8BBE\8BA1'), 'Writing, photography, illustration, design, and handmade creation.');
    ensure_category(UNISTR('\5176\4ED6\95EE\9898'), 'Questions that do not clearly belong to another category.');

    UPDATE categories
       SET status = 'INACTIVE',
           description = 'Internal or smoke-test category hidden from public publishing.'
     WHERE category_name IN (
               'database',
               TO_CHAR(UNISTR('\516C\7F51\5FEB\7167\6807\7B7E\6CBB\7406'))
           )
        OR category_name LIKE 'zz_admin_smoke_%';

    COMMIT;
END;
/

PROMPT Question categories standardized.
