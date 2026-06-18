-- パーツ種別 table（表）と note.table / note.table_cell の追加（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/04_parts_type_table.sql

alter domain note.parts_type drop constraint if exists parts_type_check;

alter domain note.parts_type add constraint parts_type_check
    check (value in ('jpeg', 'png', 'text', 'tex', 'md', 'binary', 'url', 'action', 'table'));

create table if not exists note."table" (
    id         serial primary key,
    aid        integer not null,
    row_count  integer not null default 5 check (row_count >= 1),
    col_count  integer not null default 5 check (col_count >= 1),

    constraint fk_note_table_aid
        foreign key (aid)
        references accounts(id)
);

create table if not exists note.table_cell (
    id             serial primary key,
    table_id       integer not null,
    x              integer not null check (x >= 1),
    y              integer not null check (y >= 1),
    cell_type      text not null check (cell_type in ('string', 'date', 'time', 'datetime', 'number')),
    input_value    text not null,
    display_format text not null default '',
    display_value  text not null default '',

    constraint fk_note_table_cell_table
        foreign key (table_id)
        references note."table"(id)
        on delete cascade,

    constraint uq_note_table_cell_position
        unique (table_id, x, y)
);

create index if not exists ix_note_table_cell_table_id
    on note.table_cell (table_id);
