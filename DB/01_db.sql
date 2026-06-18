create schema note;

create domain note.parts_type as text
    check (value in ('jpeg', 'png', 'text', 'tex', 'md', 'binary', 'url', 'action', 'table'))
;

-- フォルダ管理
--
-- deleted_number
--     値0     = 削除されていない状態
--     値1以上 = 削除されている状態
-- 削除処理
--     aid, parent, nameでのdeleted_number最大値+1の値で、deleted_numberを更新する
create table note.folder (
    id             serial  primary key,        -- 主キー
    aid            integer not null,           -- アカウントID
    parent         integer null,               -- 親フォルダの主キー
    name           text    not null,           -- フォルダ名称
    dorder         integer not null,           -- 表示順
    
    deleted_number integer not null default 0, -- 削除番号

    -- アカウントID 外部キー
    constraint fk_note_folder_aid
        foreign key (aid)
        references accounts(id),

    -- 親フォルダ 外部キー
    constraint fk_note_folder_parent
        foreign key (parent)
        references note.folder(id),

    -- フォルダ名称 唯一性
    constraint uq_note_folder_name
        unique (aid, parent, deleted_number, name),

    -- 表示順 唯一性
    constraint uq_note_folder_dorder
        unique (aid, parent, dorder)
);

-- ファイル管理
--
-- deleted_number
--     値0     = 削除されていない状態
--     値1以上 = 削除されている状態
-- 削除処理
--     aid, parent, titleでのdeleted_number最大値+1の値で、deleted_numberを更新する
create table note.file (
    id             serial   primary key,       -- 主キー
    aid            integer  not null,          -- アカウントID
    
    belong         integer not null,           -- 所属フォルダ
    title          text    not null,           -- ファイルタイトル
    dorder         integer not null,           -- 表示順
    
    deleted_number integer not null default 0, -- 削除番号

    -- アカウントID 外部キー
    constraint fk_note_file_aid
        foreign key (aid)
        references accounts(id),

    -- 所属フォルダ 外部キー
    constraint fk_note_file_belong
        foreign key (belong)
        references note.folder(id),

    -- タイトル 唯一性
    constraint uq_note_file_title
        unique (aid, belong, deleted_number, title),

    -- 表示順 唯一性
    constraint uq_note_file_dorder
        unique (aid, belong, dorder)
);

-- ファイルパーツ
create table note.parts (
    id  serial primary key,                   -- 主キー
    aid integer not null,                     -- アカウントID

    file       integer not null,              -- 所属ファイル
    dorder     integer not null,              -- 表示順
    is_deleted bool not null,                 -- 削除フラグ

    ptype      note.parts_type not null,
    data       text            not null,
    filename   text            not null default '',

    constraint fk_note_parts_aid
        foreign key (aid)
        references accounts(id),
    constraint fk_note_parts_file
        foreign key (file)
        references note.file(id),
    constraint uq_note_parts_dorder
        unique (aid, file, dorder)
);

-- パーツの過去世代（置き換え前のスナップショット）
create table note.parts_revision (
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

create index ix_note_parts_revision_parts_id
    on note.parts_revision (parts_id, revision_number desc);

-- 表パーツ（table）
create table note."table" (
    id         serial primary key,
    aid        integer not null,
    row_count  integer not null default 5 check (row_count >= 1),
    col_count  integer not null default 5 check (col_count >= 1),
    title      text not null default '',

    constraint fk_note_table_aid
        foreign key (aid)
        references accounts(id)
);

create table note.table_cell (
    id             serial primary key,
    table_id       integer not null,
    x              integer not null check (x >= 1),
    y              integer not null check (y >= 1),
    cell_type      text not null check (cell_type in ('string', 'date', 'time', 'datetime', 'number')),
    input_value    text not null,
    display_format text not null default '',
    display_value  text not null default '',
    text_align     text not null default '左寄せ'
        check (text_align in ('左寄せ', '中央寄せ', '右寄せ')),

    constraint fk_note_table_cell_table
        foreign key (table_id)
        references note."table"(id)
        on delete cascade,

    constraint uq_note_table_cell_position
        unique (table_id, x, y)
);

create index ix_note_table_cell_table_id
    on note.table_cell (table_id);

    