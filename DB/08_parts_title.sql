-- パーツ（note.parts）にタイトル列を追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/08_parts_title.sql

alter table note.parts
    add column if not exists title text not null default '';
