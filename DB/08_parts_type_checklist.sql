-- パーツ種別 checklist と note.checklist / category / item（既存 DB 向け）
-- 実行例: psql -h localhost -U tamtuser -d tamtdb -f DB/08_parts_type_checklist.sql

alter domain note.parts_type drop constraint if exists parts_type_check;

alter domain note.parts_type add constraint parts_type_check
    check (value in (
        'jpeg', 'png', 'text', 'tex', 'md', 'binary', 'url', 'action', 'table', 'checklist'
    ));

create table if not exists note.checklist (
    id    serial primary key,
    aid   integer not null,
    title text not null default '',

    constraint fk_note_checklist_aid
        foreign key (aid) references accounts(id)
);

create table if not exists note.checklist_category (
    id           serial primary key,
    checklist_id integer not null,
    name         text not null default '',
    dorder       integer not null default 0,
    is_deleted   boolean not null default false,

    constraint fk_note_checklist_category_checklist
        foreign key (checklist_id)
        references note.checklist(id)
        on delete cascade
);

create unique index if not exists uq_note_checklist_category_name_alive
    on note.checklist_category (checklist_id, name)
    where is_deleted = false;

create index if not exists ix_note_checklist_category_checklist_id
    on note.checklist_category (checklist_id);

create table if not exists note.checklist_item (
    id           serial primary key,
    checklist_id integer not null,
    category_id  integer not null,
    title        text not null default '',
    is_checked   boolean not null default false,
    dorder       integer not null default 0,
    is_deleted   boolean not null default false,

    constraint fk_note_checklist_item_checklist
        foreign key (checklist_id)
        references note.checklist(id)
        on delete cascade,

    constraint fk_note_checklist_item_category
        foreign key (category_id)
        references note.checklist_category(id)
        on delete cascade
);

create index if not exists ix_note_checklist_item_checklist_id
    on note.checklist_item (checklist_id);

create index if not exists ix_note_checklist_item_category_id
    on note.checklist_item (category_id);
