-- パーツ種別 action（行動予定）の追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/03_parts_type_action.sql

alter domain note.parts_type drop constraint if exists parts_type_check;

alter domain note.parts_type add constraint parts_type_check
    check (value in ('jpeg', 'png', 'text', 'tex', 'md', 'binary', 'url', 'action'));
