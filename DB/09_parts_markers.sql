-- パーツ（note.parts）に画像マーカー列を追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/09_parts_markers.sql

alter table note.parts
    add column if not exists markers text not null default '[]';
