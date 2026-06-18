-- 表セルに表示位置（text_align）を追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/05_table_cell_text_align.sql

alter table note.table_cell
    add column if not exists text_align text not null default '左寄せ';

alter table note.table_cell drop constraint if exists ck_note_table_cell_text_align;

alter table note.table_cell add constraint ck_note_table_cell_text_align
    check (text_align in ('左寄せ', '中央寄せ', '右寄せ'));
