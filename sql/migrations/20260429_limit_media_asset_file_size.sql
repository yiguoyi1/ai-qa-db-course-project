-- 20260429_limit_media_asset_file_size.sql
-- Enforce the 50MB upload limit at the database metadata layer.

SET DEFINE OFF

PROMPT Applying migration: limit media asset file size to 50MB...

DECLARE
    l_exists NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO l_exists
      FROM user_constraints
     WHERE table_name = 'MEDIA_ASSETS'
       AND constraint_name = 'CK_MEDIA_ASSETS_FILE_SIZE';

    IF l_exists > 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE media_assets DROP CONSTRAINT ck_media_assets_file_size';
    END IF;
END;
/

ALTER TABLE media_assets
ADD CONSTRAINT ck_media_assets_file_size
    CHECK (file_size BETWEEN 0 AND 52428800);

COMMIT;

PROMPT Migration completed successfully.
