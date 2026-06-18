# Note スキーマ DB 仕様書

## 1. 概要

| 項目 | 内容 |
|------|------|
| DBMS | PostgreSQL |
| スキーマ名 | `note` |
| 用途 | ノートアプリのフォルダ・ファイル・パーツ（コンテンツ断片）管理 |
| 関連テーブル | `public.accounts`（アカウントマスタ、別スキーマ） |

各レコードは **アカウント ID（`aid`）** でテナント分離される。API では JWT の `username` から `accounts.id` を解決し、その値を `aid` として利用する。

---

## 2. 接続情報

リポジトリルートの `.env` で指定する（認証 API と共通）。

| 環境変数 | 説明 | 初期値（例） |
|----------|------|----------------|
| `DB_HOST` | ホスト | `localhost` |
| `DB_PORT` | ポート | `5432` |
| `DB_NAME` | データベース名 | `tamtdb` |
| `DB_USER` | ユーザー名 | `tamtuser` |
| `DB_PASSWORD` | パスワード | （`.env` 参照） |

---

## 3. ドメイン型

### `note.parts_type`

テキスト型ドメイン。パーツの種別を表す。

| 値 | 意味 |
|----|------|
| `jpeg` | JPEG 画像（`data` は Base64 文字列） |
| `png` | PNG 画像（`data` は Base64 文字列） |
| `text` | プレーンテキスト |
| `tex` | TeX ソース |
| `md` | Markdown |
| `binary` | バイナリ（`data` は Base64 文字列） |
| `url` | URL 文字列 |
| `action` | 行動予定（`data` は JSON。時刻・地点・経由メモの構造） |
| `table` | 表（`data` は `note.table.id` の文字列） |

```sql
create domain note.parts_type as text
    check (value in ('jpeg', 'png', 'text', 'tex', 'md', 'binary', 'url', 'action', 'table'));
```

---

## 4. テーブル一覧

| テーブル | 説明 |
|----------|------|
| `note.folder` | フォルダ階層 |
| `note.file` | ファイル（フォルダに所属） |
| `note.parts` | ファイルを構成するパーツ |
| `note.table` | 表パーツの本体（行数・列数） |
| `note.table_cell` | 表のセル（スパース格納） |

---

## 5. `note.folder`（フォルダ）

### 5.1 カラム

| カラム | 型 | NULL | 既定値 | 説明 |
|--------|-----|------|--------|------|
| `id` | serial | NOT NULL | — | 主キー（フォルダ ID） |
| `aid` | integer | NOT NULL | — | アカウント ID → `accounts(id)` |
| `parent` | integer | NULL | — | 親フォルダ ID → `note.folder(id)`。`NULL` はルート直下 |
| `name` | text | NOT NULL | — | フォルダ名称 |
| `dorder` | integer | NOT NULL | — | 同一親内での表示順（昇順） |
| `deleted_number` | integer | NOT NULL | `0` | 削除番号（後述） |

### 5.2 制約

| 名前 | 種別 | 定義 |
|------|------|------|
| `fk_note_folder_aid` | FK | `aid` → `accounts(id)` |
| `fk_note_folder_parent` | FK | `parent` → `note.folder(id)` |
| `uq_note_folder_name` | UNIQUE | `(aid, parent, deleted_number, name)` |
| `uq_note_folder_dorder` | UNIQUE | `(aid, parent, dorder)` |

**注意:** `uq_note_folder_dorder` は `deleted_number` を含まない。削除済みレコードも表示順スロットを占有する。

### 5.3 `deleted_number` の意味

| 値 | 状態 |
|----|------|
| `0` | 未削除（有効） |
| `1` 以上 | 削除済み |

**論理削除時:** 同一 `(aid, parent, name)` における既存 `deleted_number` の最大値 + 1 をセットする。

**削除解除時:** `deleted_number` を `0` に戻す。ただし同一 `(aid, parent, name)` で `deleted_number = 0` の別レコードが既にある場合はエラー（API 側で拒否）。

---

## 6. `note.file`（ファイル）

### 6.1 カラム

| カラム | 型 | NULL | 既定値 | 説明 |
|--------|-----|------|--------|------|
| `id` | serial | NOT NULL | — | 主キー（ファイル ID） |
| `aid` | integer | NOT NULL | — | アカウント ID → `accounts(id)` |
| `belong` | integer | NOT NULL | — | 所属フォルダ ID → `note.folder(id)` |
| `title` | text | NOT NULL | — | ファイルタイトル |
| `dorder` | integer | NOT NULL | — | 同一フォルダ内での表示順 |
| `deleted_number` | integer | NOT NULL | `0` | 削除番号 |

### 6.2 制約

| 名前 | 種別 | 定義 |
|------|------|------|
| `fk_note_file_aid` | FK | `aid` → `accounts(id)` |
| `fk_note_file_belong` | FK | `belong` → `note.folder(id)` |
| `uq_note_file_title` | UNIQUE | `(aid, belong, deleted_number, title)` |
| `uq_note_file_dorder` | UNIQUE | `(aid, belong, dorder)` |

### 6.3 `deleted_number` の意味

フォルダと同様。論理削除キーは `(aid, belong, title)`（仕様書の「parent」は DB 上 `belong` に相当）。

---

## 7. `note.parts`（パーツ）

### 7.1 カラム

| カラム | 型 | NULL | 既定値 | 説明 |
|--------|-----|------|--------|------|
| `id` | serial | NOT NULL | — | 主キー（パーツ ID） |
| `aid` | integer | NOT NULL | — | アカウント ID → `accounts(id)` |
| `file` | integer | NOT NULL | — | 所属ファイル ID → `note.file(id)` |
| `dorder` | integer | NOT NULL | — | 同一ファイル内での表示順 |
| `is_deleted` | boolean | NOT NULL | — | 削除フラグ（`true` = 削除済み） |
| `ptype` | note.parts_type | NOT NULL | — | パーツ種別 |
| `data` | text | NOT NULL | — | 本文データ |
| `filename` | text | NOT NULL | `''` | ファイル名（`jpeg` / `png` / `binary` で使用。ダウンロード時の名前） |

### 7.2 制約

| 名前 | 種別 | 定義 |
|------|------|------|
| `fk_note_parts_aid` | FK | `aid` → `accounts(id)` |
| `fk_note_parts_file` | FK | `file` → `note.file(id)` |
| `uq_note_parts_dorder` | UNIQUE | `(aid, file, dorder)` |

パーツは `deleted_number` ではなく **`is_deleted` フラグ**で論理削除する（フォルダ・ファイルとは方式が異なる）。

`ptype = table` のとき、`data` には **`note.table.id` を10進文字列**で格納する。セル本体は `note.table_cell` にスパース格納する（値のないセルは行を持たない）。

---

## 8. `note.table`（表）

表パーツ 1 件につき 1 行。行数・列数を保持する。

| カラム | 型 | NULL | 既定値 | 説明 |
|--------|-----|------|--------|------|
| `id` | serial | NOT NULL | — | 主キー |
| `aid` | integer | NOT NULL | — | アカウント ID |
| `row_count` | integer | NOT NULL | `5` | 行数（1 以上） |
| `col_count` | integer | NOT NULL | `5` | 列数（1 以上） |
| `title` | text | NOT NULL | `''` | 表タイトル（パーツ表示時に表の上へ表示） |

---

## 9. `note.table_cell`（表セル）

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| `id` | serial | NOT NULL | 主キー |
| `table_id` | integer | NOT NULL | → `note.table(id)` ON DELETE CASCADE |
| `x` | integer | NOT NULL | 列位置（1 始まり） |
| `y` | integer | NOT NULL | 行位置（1 始まり） |
| `cell_type` | text | NOT NULL | `string` / `date` / `time` / `datetime` / `number` |
| `input_value` | text | NOT NULL | 入力値（`=` 始まりは数式） |
| `display_format` | text | NOT NULL | 表示形式（文字列型は未使用可） |
| `display_value` | text | NOT NULL | バックエンド算出済み表示値 |
| `text_align` | text | NOT NULL | 表示位置（`左寄せ` / `中央寄せ` / `右寄せ`、既定 `左寄せ`） |

| 名前 | 種別 | 定義 |
|------|------|------|
| `uq_note_table_cell_position` | UNIQUE | `(table_id, x, y)` |

**スパース格納:** 値のないセルは行を作らない。入力値を空にしたら行を削除する。

---

## 10. `note.parts_revision`（パーツ過去世代）

`jpeg` / `png` / `binary` パーツを **置き換え（update）** する直前に、変更前の内容をスナップショットとして保存する。保持件数は環境変数 `PARTS_MAX_REVISIONS`（既定 `3`）。超過分は古い世代から削除する。

### 8.1 カラム

| カラム | 型 | NULL | 説明 |
|--------|-----|------|------|
| `id` | serial | NOT NULL | 主キー（世代 ID。ダウンロード API で指定） |
| `aid` | integer | NOT NULL | アカウント ID |
| `parts_id` | integer | NOT NULL | 元パーツ ID → `note.parts(id)` |
| `revision_number` | integer | NOT NULL | パーツ内の世代番号（1 始まり、更新のたびに増加） |
| `filename` | text | NOT NULL | 当該世代のファイル名 |
| `ptype` | note.parts_type | NOT NULL | 当該世代の種別 |
| `data` | text | NOT NULL | 当該世代のデータ |
| `created_at` | timestamp | NOT NULL | スナップショット作成時刻 |

### 8.2 制約

| 名前 | 種別 | 定義 |
|------|------|------|
| `fk_note_parts_revision_aid` | FK | `aid` → `accounts(id)` |
| `fk_note_parts_revision_parts` | FK | `parts_id` → `note.parts(id)` ON DELETE CASCADE |
| `uq_note_parts_revision_number` | UNIQUE | `(parts_id, revision_number)` |

---

## 11. ER 概要

```
accounts (public)
    │
    ├──< note.folder (aid) ── parent ──> note.folder
    │
    ├──< note.file (aid) ── belong ──> note.folder
    │
    ├──< note.table (aid)
    │         └──< note.table_cell (table_id)
    │
    └──< note.parts (aid) ── file ──> note.file
              │ data → note.table.id (ptype=table)
              └──< note.parts_revision (parts_id)
```

---

## 12. 作成 DDL（参照用）

```sql
create schema if not exists note;

create domain note.parts_type as text
    check (value in ('jpeg', 'png', 'text', 'tex', 'md', 'binary', 'url', 'action', 'table'));

create table note.folder (
    id             serial  primary key,
    aid            integer not null,
    parent         integer null,
    name           text    not null,
    dorder         integer not null,
    deleted_number integer not null default 0,
    constraint fk_note_folder_aid
        foreign key (aid) references accounts(id),
    constraint fk_note_folder_parent
        foreign key (parent) references note.folder(id),
    constraint uq_note_folder_name
        unique (aid, parent, deleted_number, name),
    constraint uq_note_folder_dorder
        unique (aid, parent, dorder)
);

create table note.file (
    id             serial   primary key,
    aid            integer  not null,
    belong         integer not null,
    title          text    not null,
    dorder         integer not null,
    deleted_number integer not null default 0,
    constraint fk_note_file_aid
        foreign key (aid) references accounts(id),
    constraint fk_note_file_belong
        foreign key (belong) references note.folder(id),
    constraint uq_note_file_title
        unique (aid, belong, deleted_number, title),
    constraint uq_note_file_dorder
        unique (aid, belong, dorder)
);

create table note.parts (
    id         serial primary key,
    aid        integer not null,
    file       integer not null,
    dorder     integer not null,
    is_deleted bool not null,
    ptype      note.parts_type not null,
    data       text not null,
    constraint fk_note_parts_aid
        foreign key (aid) references accounts(id),
    constraint fk_note_parts_file
        foreign key (file) references note.file(id),
    constraint uq_note_parts_dorder
        unique (aid, file, dorder)
);
```

---

## 10. 設計上の注意（実装者向け）

1. **ルートフォルダ:** `parent IS NULL` のフォルダがツリー最上位。ファイルは `belong` が NOT NULL のため、常にいずれかのフォルダ配下に存在する。ルート直下にファイルは置けない。
2. **論理削除と子要素:** フォルダ削除時、子フォルダ・配下ファイルのレコードは変更しない。API 一覧取得時は、祖先フォルダが削除済み（`deleted_number > 0`）の子要素を削除扱い（`is_del: true`）とする。
3. **表示順の入れ替え:** `uq_*_dorder` 制約があるため、2 件の `dorder` を入れ替える際は一時値（負数等）を使うか、トランザクション内で順序を工夫する。
4. **削除解除時の dorder:** 復元（`deleted_number` を 0 に戻す）際、同一親内で `dorder` が衝突する場合は最大値 + 1 に再採番する。
5. **移動時:** 仕様上、移動先での名称重複チェックが必要。実装では `parent` / `belong` の更新と、移動先での `dorder` 再採番（最大値 + 1）を行う。
6. **アカウント整合:** すべての API 操作で `aid` が JWT 由来のアカウント ID と一致することを確認する。
