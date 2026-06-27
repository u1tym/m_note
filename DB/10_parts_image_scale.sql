-- パーツ（note.parts）に画像表示倍率列を追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/10_parts_image_scale.sql

alter table note.parts
    add column if not exists image_scale real not null default 1.0;
