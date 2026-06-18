-- 表の列幅（note.table_col_width）追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/07_table_col_width.sql

create table if not exists note.table_col_width (
    id         serial primary key,
    table_id   integer not null,
    x          integer not null check (x >= 1),
    width_px   integer not null check (width_px >= 32 and width_px <= 480),

    constraint fk_note_table_col_width_table
        foreign key (table_id)
        references note."table"(id)
        on delete cascade,

    constraint uq_note_table_col_width_position
        unique (table_id, x)
);

create index if not exists ix_note_table_col_width_table_id
    on note.table_col_width (table_id);
