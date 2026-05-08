# Constraints and Rules

## Primary Keys

- All core tables use a single-column primary key.
- `QUESTION_TAGS` uses `QT_ID` as the primary key and also enforces uniqueness on `(QUESTION_ID, TAG_ID)`.

## Unique Constraints

- `USERS.USERNAME` must be unique.
- `CATEGORIES.CATEGORY_NAME` must be unique.
- `TAGS.TAG_NAME` must be unique.
- `QUESTION_TAGS (QUESTION_ID, TAG_ID)` must be unique.
- `FAVORITES (USER_ID, QUESTION_ID)` must be unique.
- `ANSWER_FEEDBACK (ANSWER_ID, USER_ID)` must be unique.
- `USER_TAG_PROFILE (USER_ID, TAG_ID)` must be unique.
- `ANSWERS (QUESTION_ID, ANSWER_ID)` must be unique to support accepted-answer ownership checks.

## Foreign Keys

- `USERS.AVATAR_MEDIA_ID -> MEDIA_ASSETS.MEDIA_ID`
- `MEDIA_ASSETS.UPLOADER_USER_ID -> USERS.USER_ID`
- `TAGS.CREATE_USER_ID -> USERS.USER_ID`
- `QUESTIONS.USER_ID -> USERS.USER_ID`
- `QUESTIONS.CATEGORY_ID -> CATEGORIES.CATEGORY_ID`
- `QUESTIONS (QUESTION_ID, ACCEPTED_ANSWER_ID) -> ANSWERS (QUESTION_ID, ANSWER_ID)`
- `ANSWERS.QUESTION_ID -> QUESTIONS.QUESTION_ID`
- `ANSWERS.USER_ID -> USERS.USER_ID`
- `QUESTION_TAGS.QUESTION_ID -> QUESTIONS.QUESTION_ID`
- `QUESTION_TAGS.TAG_ID -> TAGS.TAG_ID`
- `ANSWER_FEEDBACK.ANSWER_ID -> ANSWERS.ANSWER_ID`
- `ANSWER_FEEDBACK.USER_ID -> USERS.USER_ID`
- `ANSWER_COMMENTS.ANSWER_ID -> ANSWERS.ANSWER_ID`
- `ANSWER_COMMENTS.USER_ID -> USERS.USER_ID`
- `ANSWER_COMMENTS.PARENT_COMMENT_ID -> ANSWER_COMMENTS.COMMENT_ID`
- `ANSWER_COMMENTS.ROOT_COMMENT_ID -> ANSWER_COMMENTS.COMMENT_ID`
- `ANSWER_COMMENTS.REPLY_TO_USER_ID -> USERS.USER_ID`
- `FAVORITES.USER_ID -> USERS.USER_ID`
- `FAVORITES.QUESTION_ID -> QUESTIONS.QUESTION_ID`
- `BROWSE_HISTORY.USER_ID -> USERS.USER_ID`
- `BROWSE_HISTORY.QUESTION_ID -> QUESTIONS.QUESTION_ID`
- `SEARCH_HISTORY.USER_ID -> USERS.USER_ID`
- `RECOMMENDATIONS.USER_ID -> USERS.USER_ID`
- `RECOMMENDATIONS.QUESTION_ID -> QUESTIONS.QUESTION_ID`
- `USER_TAG_PROFILE.USER_ID -> USERS.USER_ID`
- `USER_TAG_PROFILE.TAG_ID -> TAGS.TAG_ID`
- `CHAT_SESSION.USER_ID -> USERS.USER_ID`
- `CHAT_MESSAGE.SESSION_ID -> CHAT_SESSION.SESSION_ID`
- `AI_PROMPT_LOG.QUESTION_ID -> QUESTIONS.QUESTION_ID`
- `LOGIN_LOG.USER_ID -> USERS.USER_ID`
- `OPERATION_LOG.USER_ID -> USERS.USER_ID`

## Status, Type, and Result Rules

- `USERS.ROLE` in `('USER', 'ADMIN')`
- `USERS.STATUS` in `('ACTIVE', 'INACTIVE', 'LOCKED', 'DISABLED')`
- `CATEGORIES.STATUS` in `('ACTIVE', 'INACTIVE')`
- `TAGS.SOURCE` in `('SYSTEM', 'USER', 'AI', 'ADMIN')`
- `TAGS.STATUS` in `('ACTIVE', 'PENDING', 'DISABLED')`
- `QUESTIONS.STATUS` in `('OPEN', 'RESOLVED', 'CLOSED', 'ARCHIVED', 'DELETED')`
- `QUESTION_TAGS.SOURCE` in `('USER_SELECTED', 'USER_CREATED', 'AI_MATCHED', 'AI_CREATED', 'ADMIN_ADJUSTED')`
- `ANSWERS.ANSWER_TYPE` in `('AI', 'MANUAL', 'SYSTEM')`
- `ANSWERS.STATUS` in `('ACTIVE', 'HIDDEN', 'DELETED')`
- `ANSWERS.DELETE_TIME` is `NULL` or not earlier than `ANSWERS.GENERATE_TIME`
- `MEDIA_ASSETS.OWNER_TYPE` in `('USER_AVATAR', 'QUESTION', 'ANSWER')`
- `MEDIA_ASSETS.STATUS` in `('ACTIVE', 'DELETED')`
- `ANSWER_COMMENTS.STATUS` in `('ACTIVE', 'HIDDEN', 'DELETED')`
- `ANSWER_FEEDBACK.IS_LIKE` in `('Y', 'N')`
- `RECOMMENDATIONS.REC_TYPE` in `('TAG_BASED', 'POPULARITY', 'HYBRID', 'MANUAL')`
- `RECOMMENDATIONS.REC_SOURCE` in `('USER_TAG_PROFILE', 'POPULARITY', 'USER_ACTION', 'ADMIN_RULE', 'MANUAL')` or `NULL`
- `RECOMMENDATIONS.STATUS` in `('ACTIVE', 'EXPIRED', 'DISMISSED')`
- `CHAT_SESSION.STATUS` in `('OPEN', 'CLOSED', 'ARCHIVED')`
- `CHAT_MESSAGE.SENDER_TYPE` in `('USER', 'AI', 'SYSTEM')`
- `LOGIN_LOG.RESULT` in `('SUCCESS', 'FAILURE', 'LOCKED')`

## Numeric Range Rules

- `QUESTIONS.VIEW_COUNT >= 0`
- `QUESTIONS.FAVORITE_COUNT >= 0`
- `QUESTIONS.ANSWER_COUNT >= 0`
- `ANSWERS.CONFIDENCE_SCORE` is `NULL` or between `0` and `100`
- `QUESTION_TAGS.CONFIDENCE_SCORE` is `NULL` or between `0` and `100`
- `ANSWERS.LIKE_COUNT >= 0`
- `ANSWERS.DISLIKE_COUNT >= 0`
- `ANSWERS.AVG_RATING` is `NULL` or between `0` and `5`
- `MEDIA_ASSETS.FILE_SIZE` is between `0` and `52428800` bytes (`50MB`)
- `MEDIA_ASSETS.SORT_ORDER >= 1`
- `ANSWER_COMMENTS.COMMENT_LEVEL >= 1`
- `ANSWER_COMMENTS.REPLY_COUNT >= 0`
- `ANSWER_FEEDBACK.RATING` is `NULL` or between `0` and `5`
- `BROWSE_HISTORY.DURATION >= 0`
- `BROWSE_HISTORY.CLICK_DEPTH >= 1`
- `RECOMMENDATIONS.REC_SCORE >= 0`
- `USER_TAG_PROFILE.WEIGHT >= 0`
- `AI_PROMPT_LOG.TOKEN_USAGE >= 0`

## Time Rules

- `CHAT_SESSION.END_TIME` must be `NULL` or greater than or equal to `START_TIME`
- `MEDIA_ASSETS.DELETE_TIME` must be `NULL` or greater than or equal to `CREATE_TIME`
- `ANSWER_COMMENTS.DELETE_TIME` must be `NULL` or greater than or equal to `CREATE_TIME`

## Accepted Answer Rules

- A question may have zero or one accepted answer through `QUESTIONS.ACCEPTED_ANSWER_ID`.
- Accepted answers must belong to the same question. This is enforced by the composite foreign key from `QUESTIONS (QUESTION_ID, ACCEPTED_ANSWER_ID)` to `ANSWERS (QUESTION_ID, ANSWER_ID)`.
- Accepting an answer changes the question status to `RESOLVED`.
- Only the question author or an active administrator can accept an answer.
- `SYSTEM` answers must not be accepted.

## Answer Source Rules

- `MANUAL` answers must carry a real `USER_ID`.
- `AI` and `SYSTEM` answers must keep `USER_ID = NULL`.
- `MANUAL` answers currently represent community user replies.
- Answer deletion uses soft delete by setting `ANSWERS.STATUS = 'DELETED'`; normal answer lists, answer counts, feedback, comments, images, and AI follow-up only operate on `ACTIVE` answers.
- Accepted answers cannot be deleted before changing the accepted answer, to avoid hiding the answer referenced by `QUESTIONS.ACCEPTED_ANSWER_ID`.

## Tag Source Rules

- User-selected existing tags are recorded as `QUESTION_TAGS.SOURCE = 'USER_SELECTED'`.
- User-created or user-entered custom tags are recorded as `TAGS.SOURCE = 'USER'` and `QUESTION_TAGS.SOURCE = 'USER_CREATED'`.
- AI-matched existing tags are recorded as `QUESTION_TAGS.SOURCE = 'AI_MATCHED'`.
- AI-created tags are recorded as `TAGS.SOURCE = 'AI'` and `QUESTION_TAGS.SOURCE = 'AI_CREATED'`.
- Disabled tags must not be returned by public tag listing APIs or attached to new questions.

## Comment and Reply Rules

- Comments are attached to `ANSWERS`, not directly to `QUESTIONS`.
- Top-level comments use `PARENT_COMMENT_ID = NULL`.
- Reply comments must reference a parent comment that belongs to the same `ANSWER_ID`.
- `ROOT_COMMENT_ID` identifies the root comment thread for both top-level comments and replies.
- New comments are only allowed when the related question status is `OPEN` or `RESOLVED`.
- Replies are only allowed against comments in `ACTIVE` status.
- Users are allowed to reply to their own comments.
- Comment editing is not supported in the current version.
- Comment deletion uses soft delete instead of physical delete.
- Deleting a comment does not cascade to child replies.
- When listing comments, deleted top-level comments are displayed as `原评论已删除`.
- When listing comments, deleted replies are displayed as `原回复已删除`.
- Only the comment author can delete the comment in the current implementation.

## Admin Governance Rules

- The current project uses `USERS.ROLE = 'ADMIN'` to represent administrator identity.
- Admin permissions are based on role checks in the application layer and do not rely on a separate admin table.
- Only `ACTIVE` admin users can execute admin APIs.
- Admin operations should be recorded in `OPERATION_LOG`.
- Admins may query `LOGIN_LOG` and `OPERATION_LOG`.
- Admins may create and update `CATEGORIES`.
- Admins may update `USERS.STATUS` and `USERS.ROLE` for other users.
- The current admin implementation must not remove the last active admin account.
- Admins must not demote their own current account from `ADMIN` to `USER`.
- Admins must not deactivate their own current account.
- Admins may update `QUESTIONS.STATUS`.
- Admins currently moderate comments by setting `ANSWER_COMMENTS.STATUS` to `HIDDEN` or back to `ACTIVE`.
- Admins do not force-delete comments in the current implementation.
- When listing comments, `HIDDEN` comments should display an administrator-hidden placeholder instead of the original content.

## Media Rules

- `MEDIA_ASSETS` stores both media metadata and image binaries.
- `MEDIA_ASSETS.FILE_CONTENT` stores image content as an Oracle `BLOB`.
- `USER_AVATAR` media is linked from `USERS.AVATAR_MEDIA_ID`.
- `QUESTION` media belongs to a question through `OWNER_ID = QUESTIONS.QUESTION_ID`.
- `ANSWER` media belongs to an answer through `OWNER_ID = ANSWERS.ANSWER_ID`.
- Media deletion uses soft delete by setting `STATUS = 'DELETED'` and `DELETE_TIME`.
- The current MVP supports user avatars, question images, and answer images. Comment images are reserved for a later phase.
