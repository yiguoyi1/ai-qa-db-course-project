-- procedures.sql
-- Business procedures and functions for the AI QA system

SET DEFINE OFF

CREATE OR REPLACE PACKAGE qa_app_pkg AS
    -- 同步问题统计字段：浏览数、收藏数、回答数。
    -- 主要由触发器调用，也可以在数据修复时手动调用。
    PROCEDURE sync_question_statistics(
        p_question_id IN questions.question_id%TYPE
    );

    -- 同步回答质量统计：点赞数、点踩数和平均评分。
    PROCEDURE refresh_answer_feedback_stats(
        p_answer_id IN answers.answer_id%TYPE
    );

    -- 重建用户标签画像：根据提问、回答、收藏、浏览、反馈、评论和搜索行为计算标签权重。
    PROCEDURE rebuild_user_tag_profile(
        p_user_id IN users.user_id%TYPE
    );

    -- 计算单个问题对某个用户的推荐分。
    -- 分数综合用户画像、相似兴趣、热度、新鲜度、浏览惩罚和负反馈惩罚。
    FUNCTION get_recommendation_score(
        p_user_id     IN users.user_id%TYPE,
        p_question_id IN questions.question_id%TYPE
    ) RETURN NUMBER;

    -- 生成用户推荐列表：将高分候选写入 recommendations 表。
    PROCEDURE generate_recommendations(
        p_user_id IN users.user_id%TYPE,
        p_limit   IN PLS_INTEGER DEFAULT 10
    );
END qa_app_pkg;
/

CREATE OR REPLACE PACKAGE BODY qa_app_pkg AS
    -- 从明细表重新聚合问题统计，避免 questions 中的冗余计数字段长期偏离真实数据。
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
                      AND status = 'ACTIVE'
               )
         WHERE question_id = p_question_id;
    END sync_question_statistics;

    -- 从 answer_feedback 明细表重新聚合回答质量指标。
    -- 点赞/点踩用于排序和展示，avg_rating 用于衡量回答质量。
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

    -- 用户画像构建逻辑：
    -- 1. 先清空该用户旧画像。
    -- 2. 从多种行为来源汇总标签权重。
    -- 3. 近期行为权重更高，长期历史行为保留较低权重。
    -- 4. 负反馈会降低相关标签贡献，最终只保留正权重画像。
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
               LEAST(ROUND(SUM(src.weight), 2), 99.99) AS total_weight,
               SYSDATE
          FROM (
                SELECT qt.tag_id,
                       ROUND(
                           5 * CASE
                                   WHEN q.ask_time >= SYSDATE - 7 THEN 1
                                   WHEN q.ask_time >= SYSDATE - 30 THEN 0.75
                                   WHEN q.ask_time >= SYSDATE - 90 THEN 0.45
                                   ELSE 0.20
                               END,
                           2
                       ) AS weight
                  FROM questions q
                  JOIN question_tags qt
                    ON qt.question_id = q.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE q.user_id = p_user_id
                   AND q.status <> 'DELETED'

                UNION ALL

                SELECT qt.tag_id,
                       ROUND(
                           4.5 * CASE
                                     WHEN a.generate_time >= SYSDATE - 7 THEN 1
                                     WHEN a.generate_time >= SYSDATE - 30 THEN 0.75
                                     WHEN a.generate_time >= SYSDATE - 90 THEN 0.45
                                     ELSE 0.20
                                 END,
                           2
                       ) AS weight
                 FROM answers a
                 JOIN question_tags qt
                   ON qt.question_id = a.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE a.user_id = p_user_id
                   AND a.answer_type = 'MANUAL'
                   AND a.status = 'ACTIVE'

                UNION ALL

                SELECT qt.tag_id,
                       ROUND(
                           6 * CASE
                                   WHEN f.favorite_time >= SYSDATE - 7 THEN 1
                                   WHEN f.favorite_time >= SYSDATE - 30 THEN 0.80
                                   WHEN f.favorite_time >= SYSDATE - 90 THEN 0.50
                                   ELSE 0.25
                               END,
                           2
                       ) AS weight
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
                           (
                               CASE
                                   WHEN NVL(b.duration, 0) < 5 THEN 0.30
                                   ELSE 1
                               END
                               + LEAST(NVL(b.duration, 0), 300) / 200
                               + LEAST(NVL(b.click_depth, 1), 5) / 5
                           )
                           * CASE
                                 WHEN b.browse_time >= SYSDATE - 7 THEN 1
                                 WHEN b.browse_time >= SYSDATE - 30 THEN 0.70
                                 WHEN b.browse_time >= SYSDATE - 90 THEN 0.40
                                 ELSE 0.15
                             END,
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
                           (
                               CASE
                                   WHEN af.is_like = 'Y' THEN 4
                                   ELSE -3
                               END
                               + CASE
                                     WHEN af.rating >= 4 THEN af.rating * 0.80
                                     WHEN af.rating <= 2 THEN -1 * (3 - NVL(af.rating, 0)) * 1.20
                                     ELSE 0
                                 END
                           )
                           * CASE
                                 WHEN af.feedback_time >= SYSDATE - 7 THEN 1
                                 WHEN af.feedback_time >= SYSDATE - 30 THEN 0.75
                                 WHEN af.feedback_time >= SYSDATE - 90 THEN 0.45
                                 ELSE 0.20
                             END,
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
                   AND a.status = 'ACTIVE'

                UNION ALL

                SELECT qt.tag_id,
                       ROUND(
                           1.8 * CASE
                                     WHEN ac.create_time >= SYSDATE - 7 THEN 1
                                     WHEN ac.create_time >= SYSDATE - 30 THEN 0.70
                                     WHEN ac.create_time >= SYSDATE - 90 THEN 0.40
                                     ELSE 0.15
                                 END,
                           2
                       ) AS weight
                  FROM answer_comments ac
                  JOIN answers a
                    ON a.answer_id = ac.answer_id
                  JOIN question_tags qt
                    ON qt.question_id = a.question_id
                  JOIN tags t
                    ON t.tag_id = qt.tag_id
                   AND t.status = 'ACTIVE'
                 WHERE ac.user_id = p_user_id
                   AND ac.status = 'ACTIVE'
                   AND a.status = 'ACTIVE'

                UNION ALL

                SELECT t.tag_id,
                       ROUND(
                           0.8 * CASE
                                     WHEN sh.search_time >= SYSDATE - 7 THEN 1
                                     WHEN sh.search_time >= SYSDATE - 30 THEN 0.65
                                     WHEN sh.search_time >= SYSDATE - 90 THEN 0.35
                                     ELSE 0.10
                                 END,
                           2
                       ) AS weight
                  FROM search_history sh
                  JOIN tags t
                    ON t.status = 'ACTIVE'
                   AND (
                           INSTR(LOWER(sh.keyword), LOWER(t.tag_name)) > 0
                           OR INSTR(LOWER(t.tag_name), LOWER(TRIM(sh.keyword))) > 0
                           OR INSTR(REPLACE(LOWER(sh.keyword), ' ', '-'), LOWER(t.tag_name)) > 0
                           OR INSTR(LOWER(t.tag_name), REPLACE(LOWER(TRIM(sh.keyword)), ' ', '-')) > 0
                       )
                 WHERE sh.user_id = p_user_id
                   AND LENGTH(TRIM(sh.keyword)) >= 2
               ) src
         GROUP BY src.tag_id
        HAVING SUM(src.weight) > 0;
    END rebuild_user_tag_profile;

    -- 推荐分计算逻辑：
    -- 用户画像匹配是主分；相似用户收藏、问题热度和新鲜度加分；
    -- 已浏览问题和低分/点踩反馈会扣分，避免重复或不感兴趣内容反复推荐。
    FUNCTION get_recommendation_score(
        p_user_id     IN users.user_id%TYPE,
        p_question_id IN questions.question_id%TYPE
    ) RETURN NUMBER IS
        l_score NUMBER := 0;
    BEGIN
        SELECT ROUND(
                   GREATEST(
                       LEAST(NVL(SUM(utp.weight), 0), 40)
                       + (
                             SELECT ROUND(LEAST(COUNT(DISTINCT f2.user_id) * 0.70, 5), 2)
                               FROM favorites f2
                              WHERE f2.question_id = q.question_id
                                AND f2.user_id <> p_user_id
                                AND EXISTS (
                                        SELECT 1
                                          FROM user_tag_profile me
                                          JOIN user_tag_profile peer
                                            ON peer.user_id = f2.user_id
                                           AND peer.tag_id = me.tag_id
                                         WHERE me.user_id = p_user_id
                                    )
                         )
                       + LEAST(q.favorite_count, 30) * 0.25
                       + LEAST(q.answer_count, 20) * 0.35
                       + LEAST(q.view_count, 200) * 0.015
                       + CASE
                             WHEN q.ask_time >= SYSDATE - 3 THEN 2.5
                             WHEN q.ask_time >= SYSDATE - 7 THEN 2
                             WHEN q.ask_time >= SYSDATE - 30 THEN 1
                             WHEN q.ask_time >= SYSDATE - 90 THEN 0.3
                             ELSE 0
                         END
                       - (
                             SELECT CASE
                                        WHEN COUNT(*) = 0 THEN 0
                                        ELSE LEAST(1.5 + COUNT(*) * 0.50, 5)
                                    END
                               FROM browse_history b
                              WHERE b.user_id = p_user_id
                                AND b.question_id = q.question_id
                         )
                       - (
                             SELECT CASE
                                        WHEN COUNT(*) = 0 THEN 0
                                        ELSE 5
                                    END
                               FROM answer_feedback af
                               JOIN answers a
                                 ON a.answer_id = af.answer_id
                              WHERE af.user_id = p_user_id
                                AND a.question_id = q.question_id
                                AND a.status = 'ACTIVE'
                                AND (
                                        af.is_like = 'N'
                                        OR NVL(af.rating, 5) <= 2
                                    )
                         ),
                       0
                   ),
                   2
               ) AS score
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
         GROUP BY q.question_id,
                  q.favorite_count,
                  q.answer_count,
                  q.view_count,
                  q.ask_time;

        RETURN NVL(l_score, 0);
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RETURN 0;
    END get_recommendation_score;

    -- 批量生成 HYBRID 推荐：
    -- 先过期旧推荐，再根据画像匹配、相似兴趣、热度、新鲜度和惩罚项生成新推荐。
    -- diversity_penalty 用于避免同一标签下的问题过度集中。
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
           AND rec_type IN ('TAG_BASED', 'POPULARITY', 'HYBRID')
           AND status = 'ACTIVE';

        FOR rec IN (
            SELECT question_id,
                   score,
                   matched_tag_count,
                   profile_score,
                   similar_interest_score,
                   popularity_score,
                   freshness_score,
                   browse_penalty,
                   feedback_penalty,
                   diversity_penalty
              FROM (
                    SELECT final_ranked.question_id,
                           final_ranked.score,
                           final_ranked.matched_tag_count,
                           final_ranked.profile_score,
                           final_ranked.similar_interest_score,
                           final_ranked.popularity_score,
                           final_ranked.freshness_score,
                           final_ranked.browse_penalty,
                           final_ranked.feedback_penalty,
                           final_ranked.diversity_penalty,
                           ROW_NUMBER() OVER (
                               ORDER BY final_ranked.score DESC, final_ranked.question_id DESC
                           ) AS rn
                      FROM (
                            SELECT diversified.question_id,
                                   ROUND(
                                       GREATEST(
                                           diversified.raw_score - diversified.diversity_penalty,
                                           0
                                       ),
                                       2
                                   ) AS score,
                                   diversified.matched_tag_count,
                                   diversified.profile_score,
                                   diversified.similar_interest_score,
                                   diversified.popularity_score,
                                   diversified.freshness_score,
                                   diversified.browse_penalty,
                                   diversified.feedback_penalty,
                                   diversified.diversity_penalty
                              FROM (
                                    SELECT scored.*,
                                           CASE
                                               WHEN scored.tag_rank <= 2 THEN 0
                                               ELSE LEAST((scored.tag_rank - 2) * 1.5, 6)
                                           END AS diversity_penalty
                                      FROM (
                                            SELECT raw_scored.*,
                                                   ROW_NUMBER() OVER (
                                                       PARTITION BY NVL(raw_scored.primary_tag_id, -1)
                                                       ORDER BY raw_scored.raw_score DESC,
                                                                raw_scored.question_id DESC
                                                   ) AS tag_rank
                                              FROM (
                                                    SELECT base.question_id,
                                                           base.primary_tag_id,
                                                           base.matched_tag_count,
                                                           base.profile_score,
                                                           base.similar_interest_score,
                                                           base.popularity_score,
                                                           base.freshness_score,
                                                           base.browse_penalty,
                                                           base.feedback_penalty,
                                                           ROUND(
                                                               base.profile_score
                                                               + base.similar_interest_score
                                                               + base.popularity_score
                                                               + base.freshness_score
                                                               - base.browse_penalty
                                                               - base.feedback_penalty,
                                                               2
                                                           ) AS raw_score
                                                      FROM (
                                                            SELECT candidate.question_id,
                                                                   candidate.primary_tag_id,
                                                                   candidate.matched_tag_count,
                                                                   LEAST(candidate.profile_score, 40) AS profile_score,
                                                                   candidate.similar_interest_score,
                                                                   candidate.popularity_score,
                                                                   candidate.freshness_score,
                                                                   candidate.browse_penalty,
                                                                   candidate.feedback_penalty
                                                              FROM (
                                                                    SELECT q.question_id,
                                                                           MIN(CASE
                                                                                   WHEN utp.tag_id IS NOT NULL THEN utp.tag_id
                                                                               END) AS primary_tag_id,
                                                                           COUNT(utp.tag_id) AS matched_tag_count,
                                                                           ROUND(NVL(SUM(utp.weight), 0), 2) AS profile_score,
                                                                           (
                                                                               SELECT ROUND(LEAST(COUNT(DISTINCT f2.user_id) * 0.70, 5), 2)
                                                                                 FROM favorites f2
                                                                                WHERE f2.question_id = q.question_id
                                                                                  AND f2.user_id <> p_user_id
                                                                                  AND EXISTS (
                                                                                          SELECT 1
                                                                                            FROM user_tag_profile me
                                                                                            JOIN user_tag_profile peer
                                                                                              ON peer.user_id = f2.user_id
                                                                                             AND peer.tag_id = me.tag_id
                                                                                           WHERE me.user_id = p_user_id
                                                                                      )
                                                                           ) AS similar_interest_score,
                                                                           ROUND(
                                                                               LEAST(q.favorite_count, 30) * 0.25
                                                                               + LEAST(q.answer_count, 20) * 0.35
                                                                               + LEAST(q.view_count, 200) * 0.015,
                                                                               2
                                                                           ) AS popularity_score,
                                                                           CASE
                                                                               WHEN q.ask_time >= SYSDATE - 3 THEN 2.5
                                                                               WHEN q.ask_time >= SYSDATE - 7 THEN 2
                                                                               WHEN q.ask_time >= SYSDATE - 30 THEN 1
                                                                               WHEN q.ask_time >= SYSDATE - 90 THEN 0.3
                                                                               ELSE 0
                                                                           END AS freshness_score,
                                                                           (
                                                                               SELECT CASE
                                                                                          WHEN COUNT(*) = 0 THEN 0
                                                                                          ELSE LEAST(1.5 + COUNT(*) * 0.50, 5)
                                                                                      END
                                                                                 FROM browse_history b
                                                                                WHERE b.user_id = p_user_id
                                                                                  AND b.question_id = q.question_id
                                                                           ) AS browse_penalty,
                                                                           (
                                                                               SELECT CASE
                                                                                          WHEN COUNT(*) = 0 THEN 0
                                                                                          ELSE 5
                                                                                      END
                                                                                 FROM answer_feedback af
                                                                                 JOIN answers a
                                                                                   ON a.answer_id = af.answer_id
                                                                                WHERE af.user_id = p_user_id
                                                                                  AND a.question_id = q.question_id
                                                                                  AND a.status = 'ACTIVE'
                                                                                  AND (
                                                                                          af.is_like = 'N'
                                                                                          OR NVL(af.rating, 5) <= 2
                                                                                      )
                                                                           ) AS feedback_penalty
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
                                                                              q.view_count,
                                                                              q.ask_time
                                                                   ) candidate
                                                           ) base
                                                   ) raw_scored
                                           ) scored
                                   ) diversified
                           ) final_ranked
                     WHERE final_ranked.score > 0
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
                'HYBRID',
                CASE
                    WHEN rec.matched_tag_count > 0 THEN 'USER_TAG_PROFILE'
                    WHEN rec.similar_interest_score > 0 THEN 'USER_ACTION'
                    ELSE 'POPULARITY'
                END,
                'Hybrid: tags=' || rec.matched_tag_count
                    || ', profile=' || TO_CHAR(rec.profile_score)
                    || ', similar=' || TO_CHAR(rec.similar_interest_score)
                    || ', popularity=' || TO_CHAR(rec.popularity_score)
                    || ', freshness=' || TO_CHAR(rec.freshness_score)
                    || ', penalty=' || TO_CHAR(rec.browse_penalty + rec.feedback_penalty + rec.diversity_penalty),
                rec.score,
                SYSDATE,
                'ACTIVE'
            );
        END LOOP;
    END generate_recommendations;
END qa_app_pkg;
/
