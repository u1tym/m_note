-- 表（note.table）にタイトル列を追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/06_table_title.sql

alter table note."table"
    add column if not exists title text not null default '';
