SET DEFINE OFF

PROMPT Applying migration: refresh reporting views...

PROMPT Refreshing view V_QUESTION_OVERVIEW...
-- 回答数按 ACTIVE 回答实时统计，避免软删除回答后仍显示旧计数。
CREATE OR REPLACE VIEW v_question_overview AS
SELECT
    q.question_id,
    q.user_id,
    u.username,
    u.nickname AS author_nickname,
    q.category_id,
    c.category_name,
    q.title,
    q.ask_time,
    q.status,
    q.accepted_answer_id,
    q.view_count,
    q.favorite_count,
    NVL(answer_stats.answer_count, 0) AS answer_count,
    NVL(tag_stats.tag_count, 0) AS tag_count,
    NVL(image_stats.image_count, 0) AS image_count,
    ROUND(
        LEAST(q.favorite_count, 30) * 0.25
        + LEAST(NVL(answer_stats.answer_count, 0), 20) * 0.35
        + LEAST(q.view_count, 200) * 0.015
        + CASE
              WHEN q.ask_time >= SYSDATE - 3 THEN 2.5
              WHEN q.ask_time >= SYSDATE - 7 THEN 2
              WHEN q.ask_time >= SYSDATE - 30 THEN 1
              WHEN q.ask_time >= SYSDATE - 90 THEN 0.3
              ELSE 0
          END,
        2
    ) AS activity_score
FROM questions q
JOIN users u
  ON u.user_id = q.user_id
JOIN categories c
  ON c.category_id = q.category_id
LEFT JOIN (
    -- 这里不直接读取 QUESTIONS.ANSWER_COUNT，防止历史冗余计数未校准。
    SELECT
        question_id,
        COUNT(*) AS answer_count
    FROM answers
    WHERE status = 'ACTIVE'
    GROUP BY question_id
) answer_stats
  ON answer_stats.question_id = q.question_id
LEFT JOIN (
    SELECT
        qt.question_id,
        COUNT(*) AS tag_count
    FROM question_tags qt
    JOIN tags t
      ON t.tag_id = qt.tag_id
     AND t.status = 'ACTIVE'
    GROUP BY qt.question_id
) tag_stats
  ON tag_stats.question_id = q.question_id
LEFT JOIN (
    SELECT
        owner_id AS question_id,
        COUNT(*) AS image_count
    FROM media_assets
    WHERE owner_type = 'QUESTION'
      AND status = 'ACTIVE'
    GROUP BY owner_id
) image_stats
  ON image_stats.question_id = q.question_id
WHERE q.status <> 'DELETED';

PROMPT Refreshing view V_HOT_QUESTIONS...
CREATE OR REPLACE VIEW v_hot_questions AS
SELECT
    question_id,
    user_id,
    username,
    author_nickname,
    category_id,
    category_name,
    title,
    ask_time,
    status,
    view_count,
    favorite_count,
    answer_count,
    tag_count,
    image_count,
    activity_score AS hot_score
FROM v_question_overview
WHERE status IN ('OPEN', 'RESOLVED');

PROMPT Creating view V_QUESTION_TAG_DETAIL...
CREATE OR REPLACE VIEW v_question_tag_detail AS
SELECT
    q.question_id,
    q.title,
    q.status AS question_status,
    q.user_id AS author_user_id,
    u.username AS author_username,
    u.nickname AS author_nickname,
    q.category_id,
    c.category_name,
    qt.tag_id,
    t.tag_name,
    t.source AS tag_source,
    t.status AS tag_status,
    qt.source AS binding_source,
    qt.confidence_score,
    qt.create_time AS binding_time
FROM question_tags qt
JOIN questions q
  ON q.question_id = qt.question_id
JOIN users u
  ON u.user_id = q.user_id
JOIN categories c
  ON c.category_id = q.category_id
JOIN tags t
  ON t.tag_id = qt.tag_id
WHERE q.status <> 'DELETED';

PROMPT Creating view V_USER_ACTIVITY_SUMMARY...
CREATE OR REPLACE VIEW v_user_activity_summary AS
SELECT
    u.user_id,
    u.username,
    u.nickname,
    u.role,
    u.status,
    u.register_time,
    u.last_login_time,
    NVL(q_stats.total_questions, 0) AS total_questions,
    NVL(q_stats.open_questions, 0) AS open_questions,
    NVL(q_stats.resolved_questions, 0) AS resolved_questions,
    NVL(a_stats.total_answers, 0) AS total_answers,
    NVL(a_stats.manual_answers, 0) AS manual_answers,
    NVL(c_stats.active_comments, 0) AS active_comments,
    NVL(f_stats.total_favorites, 0) AS total_favorites,
    NVL(b_stats.total_browses, 0) AS total_browses,
    NVL(s_stats.total_searches, 0) AS total_searches,
    NVL(p_stats.profile_tag_count, 0) AS profile_tag_count,
    NVL(p_stats.total_profile_weight, 0) AS total_profile_weight,
    NVL(r_stats.active_recommendations, 0) AS active_recommendations
FROM users u
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_questions,
        COUNT(CASE WHEN status = 'OPEN' THEN 1 END) AS open_questions,
        COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END) AS resolved_questions
    FROM questions
    WHERE status <> 'DELETED'
    GROUP BY user_id
) q_stats
  ON q_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_answers,
        COUNT(CASE WHEN answer_type = 'MANUAL' THEN 1 END) AS manual_answers
    FROM answers
    WHERE user_id IS NOT NULL
    GROUP BY user_id
) a_stats
  ON a_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS active_comments
    FROM answer_comments
    WHERE status = 'ACTIVE'
    GROUP BY user_id
) c_stats
  ON c_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_favorites
    FROM favorites
    GROUP BY user_id
) f_stats
  ON f_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_browses
    FROM browse_history
    GROUP BY user_id
) b_stats
  ON b_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS total_searches
    FROM search_history
    GROUP BY user_id
) s_stats
  ON s_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS profile_tag_count,
        ROUND(SUM(weight), 2) AS total_profile_weight
    FROM user_tag_profile
    GROUP BY user_id
) p_stats
  ON p_stats.user_id = u.user_id
LEFT JOIN (
    SELECT
        user_id,
        COUNT(*) AS active_recommendations
    FROM recommendations
    WHERE status = 'ACTIVE'
    GROUP BY user_id
) r_stats
  ON r_stats.user_id = u.user_id;

PROMPT Creating view V_MEDIA_ASSET_DETAIL...
CREATE OR REPLACE VIEW v_media_asset_detail AS
SELECT
    m.media_id,
    m.uploader_user_id,
    uploader.username AS uploader_username,
    uploader.nickname AS uploader_nickname,
    m.owner_type,
    m.owner_id,
    CASE
        WHEN m.owner_type = 'QUESTION' THEN q.title
        WHEN m.owner_type = 'ANSWER' THEN answer_q.title
        WHEN m.owner_type = 'USER_AVATAR' THEN owner_user.username
        ELSE NULL
    END AS owner_title,
    m.file_name,
    m.original_file_name,
    m.mime_type,
    m.file_ext,
    m.file_size,
    m.public_url,
    m.sort_order,
    m.status,
    m.create_time,
    m.update_time,
    m.delete_time
FROM media_assets m
JOIN users uploader
  ON uploader.user_id = m.uploader_user_id
LEFT JOIN questions q
  ON m.owner_type = 'QUESTION'
 AND q.question_id = m.owner_id
LEFT JOIN answers a
  ON m.owner_type = 'ANSWER'
 AND a.answer_id = m.owner_id
LEFT JOIN questions answer_q
  ON answer_q.question_id = a.question_id
LEFT JOIN users owner_user
  ON m.owner_type = 'USER_AVATAR'
 AND owner_user.user_id = m.owner_id;

PROMPT Creating view V_CHAT_FOLLOWUP_SUMMARY...
CREATE OR REPLACE VIEW v_chat_followup_summary AS
SELECT
    cs.session_id,
    cs.user_id,
    u.username,
    u.nickname,
    cs.question_id,
    q.title AS question_title,
    cs.seed_answer_id,
    cs.start_time,
    cs.end_time,
    cs.status,
    COUNT(cm.message_id) AS message_count,
    COUNT(CASE WHEN cm.sender_type = 'USER' THEN 1 END) AS user_message_count,
    COUNT(CASE WHEN cm.sender_type = 'AI' THEN 1 END) AS ai_message_count,
    MAX(cm.send_time) AS last_message_time
FROM chat_session cs
JOIN users u
  ON u.user_id = cs.user_id
JOIN questions q
  ON q.question_id = cs.question_id
LEFT JOIN chat_message cm
  ON cm.session_id = cs.session_id
GROUP BY
    cs.session_id,
    cs.user_id,
    u.username,
    u.nickname,
    cs.question_id,
    q.title,
    cs.seed_answer_id,
    cs.start_time,
    cs.end_time,
    cs.status;

COMMIT;

PROMPT Reporting views refreshed successfully.
