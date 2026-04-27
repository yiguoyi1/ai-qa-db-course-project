-- procedures.sql
-- Business procedures and functions for the AI QA system

SET DEFINE OFF

CREATE OR REPLACE PACKAGE qa_app_pkg AS
    PROCEDURE sync_question_statistics(
        p_question_id IN questions.question_id%TYPE
    );

    PROCEDURE refresh_answer_feedback_stats(
        p_answer_id IN answers.answer_id%TYPE
    );

    PROCEDURE rebuild_user_tag_profile(
        p_user_id IN users.user_id%TYPE
    );

    FUNCTION get_recommendation_score(
        p_user_id     IN users.user_id%TYPE,
        p_question_id IN questions.question_id%TYPE
    ) RETURN NUMBER;

    PROCEDURE generate_recommendations(
        p_user_id IN users.user_id%TYPE,
        p_limit   IN PLS_INTEGER DEFAULT 10
    );
END qa_app_pkg;
/

CREATE OR REPLACE PACKAGE BODY qa_app_pkg AS
    PROCEDURE sync_question_statistics(
        p_question_id IN questions.question_id%TYPE
    ) IS
    BEGIN
        IF p_question_id IS NULL THEN
            RETURN;
        END IF;

        UPDATE questions
           SET view_count = (
                   SELECT COUNT(*)
                     FROM browse_history
                    WHERE question_id = p_question_id
               ),
               favorite_count = (
                   SELECT COUNT(*)
                     FROM favorites
                    WHERE question_id = p_question_id
               ),
               answer_count = (
                   SELECT COUNT(*)
                     FROM answers
                    WHERE question_id = p_question_id
               )
         WHERE question_id = p_question_id;
    END sync_question_statistics;

    PROCEDURE refresh_answer_feedback_stats(
        p_answer_id IN answers.answer_id%TYPE
    ) IS
    BEGIN
        IF p_answer_id IS NULL THEN
            RETURN;
        END IF;

        UPDATE answers
           SET like_count = (
                   SELECT COUNT(*)
                     FROM answer_feedback
                    WHERE answer_id = p_answer_id
                      AND is_like = 'Y'
               ),
               dislike_count = (
                   SELECT COUNT(*)
                     FROM answer_feedback
                    WHERE answer_id = p_answer_id
                      AND is_like = 'N'
               ),
               avg_rating = (
                   SELECT ROUND(AVG(rating), 2)
                     FROM answer_feedback
                    WHERE answer_id = p_answer_id
                      AND rating IS NOT NULL
               )
         WHERE answer_id = p_answer_id;
    END refresh_answer_feedback_stats;

    PROCEDURE rebuild_user_tag_profile(
        p_user_id IN users.user_id%TYPE
    ) IS
    BEGIN
        IF p_user_id IS NULL THEN
            RETURN;
        END IF;

        DELETE FROM user_tag_profile
         WHERE user_id = p_user_id;

        INSERT INTO user_tag_profile (
            user_id,
            tag_id,
            weight,
            update_time
        )
        SELECT p_user_id,
               src.tag_id,
               ROUND(SUM(src.weight), 2) AS total_weight,
               SYSDATE
          FROM (
                SELECT qt.tag_id,
                       5 AS weight
                  FROM questions q
                  JOIN question_tags qt
                    ON qt.question_id = q.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE q.user_id = p_user_id

                UNION ALL

                SELECT qt.tag_id,
                       3 AS weight
                  FROM favorites f
                  JOIN question_tags qt
                    ON qt.question_id = f.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE f.user_id = p_user_id

                UNION ALL

                SELECT qt.tag_id,
                       ROUND(
                           1
                           + LEAST(NVL(b.duration, 0), 300) / 300
                           + LEAST(NVL(b.click_depth, 1), 5) / 5,
                           2
                       ) AS weight
                  FROM browse_history b
                  JOIN question_tags qt
                    ON qt.question_id = b.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE b.user_id = p_user_id

                UNION ALL

                SELECT qt.tag_id,
                       ROUND(
                           CASE
                               WHEN af.is_like = 'Y' THEN 2
                               ELSE 0.5
                           END
                           + NVL(af.rating, 0) / 2,
                           2
                       ) AS weight
                  FROM answer_feedback af
                  JOIN answers a
                    ON a.answer_id = af.answer_id
                  JOIN question_tags qt
                    ON qt.question_id = a.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE af.user_id = p_user_id
               ) src
         GROUP BY src.tag_id
        HAVING SUM(src.weight) > 0;
    END rebuild_user_tag_profile;

    FUNCTION get_recommendation_score(
        p_user_id     IN users.user_id%TYPE,
        p_question_id IN questions.question_id%TYPE
    ) RETURN NUMBER IS
        l_score NUMBER := 0;
    BEGIN
        SELECT ROUND(
                   NVL(SUM(utp.weight), 0)
                   + LEAST(q.favorite_count, 20) * 0.10
                   + LEAST(q.answer_count, 10) * 0.20
                   + LEAST(q.view_count, 100) * 0.01,
                   2
               )
          INTO l_score
          FROM questions q
          LEFT JOIN question_tags qt
            ON qt.question_id = q.question_id
          LEFT JOIN tags t
            ON t.tag_id = qt.tag_id
           AND t.status = 'ACTIVE'
          LEFT JOIN user_tag_profile utp
            ON utp.user_id = p_user_id
           AND utp.tag_id = t.tag_id
         WHERE q.question_id = p_question_id
         GROUP BY q.favorite_count, q.answer_count, q.view_count;

        RETURN NVL(l_score, 0);
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
    END get_recommendation_score;

    PROCEDURE generate_recommendations(
        p_user_id IN users.user_id%TYPE,
        p_limit   IN PLS_INTEGER DEFAULT 10
    ) IS
    BEGIN
        IF p_user_id IS NULL OR NVL(p_limit, 0) <= 0 THEN
            RETURN;
        END IF;

        UPDATE recommendations
           SET status = 'EXPIRED'
         WHERE user_id = p_user_id
           AND rec_type = 'TAG_BASED'
           AND status = 'ACTIVE';

        FOR rec IN (
            SELECT question_id,
                   score,
                   matched_tag_count
              FROM (
                    SELECT ranked.question_id,
                           ranked.score,
                           ranked.matched_tag_count,
                           ROW_NUMBER() OVER (
                               ORDER BY ranked.score DESC, ranked.question_id DESC
                           ) AS rn
                      FROM (
                            SELECT q.question_id,
                                   ROUND(
                                       NVL(SUM(utp.weight), 0)
                                       + LEAST(q.favorite_count, 20) * 0.10
                                       + LEAST(q.answer_count, 10) * 0.20
                                       + LEAST(q.view_count, 100) * 0.01,
                                       2
                                   ) AS score,
                                   COUNT(utp.tag_id) AS matched_tag_count
                              FROM questions q
                              LEFT JOIN question_tags qt
                                ON qt.question_id = q.question_id
                              LEFT JOIN tags t
                                ON t.tag_id = qt.tag_id
                               AND t.status = 'ACTIVE'
                              LEFT JOIN user_tag_profile utp
                                ON utp.user_id = p_user_id
                               AND utp.tag_id = t.tag_id
                             WHERE q.user_id <> p_user_id
                               AND q.status = 'OPEN'
                               AND NOT EXISTS (
                                       SELECT 1
                                         FROM favorites f
                                        WHERE f.user_id = p_user_id
                                          AND f.question_id = q.question_id
                                   )
                             GROUP BY q.question_id,
                                      q.user_id,
                                      q.status,
                                      q.favorite_count,
                                      q.answer_count,
                                      q.view_count
                           ) ranked
                     WHERE ranked.score > 0
                   )
             WHERE rn <= p_limit
             ORDER BY score DESC, question_id DESC
        ) LOOP
            INSERT INTO recommendations (
                user_id,
                question_id,
                rec_type,
                rec_source,
                rec_reason,
                rec_score,
                rec_time,
                status
            ) VALUES (
                p_user_id,
                rec.question_id,
                'TAG_BASED',
                'USER_TAG_PROFILE',
                CASE
                    WHEN rec.matched_tag_count > 0 THEN
                        'Matched ' || rec.matched_tag_count || ' tag(s) in user profile'
                    ELSE
                        'Recommended by popularity and activity'
                END,
                rec.score,
                SYSDATE,
                'ACTIVE'
            );
        END LOOP;
    END generate_recommendations;
END qa_app_pkg;
/
