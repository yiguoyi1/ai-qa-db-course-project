-- views.sql
-- Reporting and presentation views for the AI QA system

SET DEFINE OFF

PROMPT Creating view V_QUESTION_OVERVIEW...
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
    q.answer_count,
    NVL(tag_stats.tag_count, 0) AS tag_count,
    NVL(image_stats.image_count, 0) AS image_count,
    ROUND(
        LEAST(q.favorite_count, 20) * 0.30
        + LEAST(q.answer_count, 10) * 0.40
        + LEAST(q.view_count, 100) * 0.02
        + CASE
              WHEN q.ask_time >= SYSDATE - 7 THEN 2
              WHEN q.ask_time >= SYSDATE - 30 THEN 1
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

PROMPT Creating view V_HOT_QUESTIONS...
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

PROMPT Creating view V_ANSWER_QUALITY_SUMMARY...
CREATE OR REPLACE VIEW v_answer_quality_summary AS
SELECT
    a.answer_id,
    a.question_id,
    q.title AS question_title,
    q.status AS question_status,
    a.user_id,
    u.username AS author_username,
    u.nickname AS author_nickname,
    a.answer_type,
    a.provider_name,
    a.generate_time,
    a.like_count,
    a.dislike_count,
    a.avg_rating,
    CASE
        WHEN q.accepted_answer_id = a.answer_id THEN 'Y'
        ELSE 'N'
    END AS is_accepted,
    NVL(comment_stats.comment_count, 0) AS active_comment_count,
    NVL(feedback_stats.feedback_count, 0) AS feedback_count
FROM answers a
JOIN questions q
  ON q.question_id = a.question_id
LEFT JOIN users u
  ON u.user_id = a.user_id
LEFT JOIN (
    SELECT
        answer_id,
        COUNT(*) AS comment_count
    FROM answer_comments
    WHERE status = 'ACTIVE'
    GROUP BY answer_id
) comment_stats
  ON comment_stats.answer_id = a.answer_id
LEFT JOIN (
    SELECT
        answer_id,
        COUNT(*) AS feedback_count
    FROM answer_feedback
    GROUP BY answer_id
) feedback_stats
  ON feedback_stats.answer_id = a.answer_id
WHERE q.status <> 'DELETED';

PROMPT Creating view V_USER_TAG_PROFILE_DETAIL...
CREATE OR REPLACE VIEW v_user_tag_profile_detail AS
SELECT
    utp.profile_id,
    utp.user_id,
    u.username,
    u.nickname,
    utp.tag_id,
    t.tag_name,
    t.source AS tag_source,
    utp.weight,
    utp.update_time,
    RANK() OVER (
        PARTITION BY utp.user_id
        ORDER BY utp.weight DESC, utp.tag_id
    ) AS profile_rank
FROM user_tag_profile utp
JOIN users u
  ON u.user_id = utp.user_id
JOIN tags t
  ON t.tag_id = utp.tag_id
 AND t.status = 'ACTIVE';

PROMPT Creating view V_ACTIVE_RECOMMENDATION_DETAIL...
CREATE OR REPLACE VIEW v_active_recommendation_detail AS
SELECT
    r.rec_id,
    r.user_id,
    target_user.username AS target_username,
    r.question_id,
    q.title,
    q.status AS question_status,
    q.category_id,
    c.category_name,
    q.user_id AS author_user_id,
    author_user.username AS author_username,
    r.rec_type,
    r.rec_source,
    r.rec_reason,
    r.rec_score,
    r.rec_time,
    r.status AS recommendation_status
FROM recommendations r
JOIN questions q
  ON q.question_id = r.question_id
JOIN users target_user
  ON target_user.user_id = r.user_id
JOIN users author_user
  ON author_user.user_id = q.user_id
JOIN categories c
  ON c.category_id = q.category_id
WHERE r.status = 'ACTIVE'
  AND q.status <> 'DELETED';

PROMPT Views created successfully.
