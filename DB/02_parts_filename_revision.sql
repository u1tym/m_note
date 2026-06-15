-- パーツのファイル名と世代管理（既存 DB 向けマイグレーション）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/02_parts_filename_revision.sql

alter table note.parts
    add column if not exists filename text not null default '';

create table if not exists note.parts_revision (
    id              serial primary key,
    aid             integer not null,
    parts_id        integer not null,
    revision_number integer not null,
    filename        text not null default '',
    ptype           note.parts_type not null,
    data            text not null,
    created_at      timestamp not null default now(),

    constraint fk_note_parts_revision_aid
        foreign key (aid) references accounts(id),
    constraint fk_note_parts_revision_parts
        foreign key (parts_id) references note.parts(id) on delete cascade,
    constraint uq_note_parts_revision_number
        unique (parts_id, revision_number)
);

create index if not exists ix_note_parts_revision_parts_id
    on note.parts_revision (parts_id, revision_number desc);
