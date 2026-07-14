# Note API 仕様書

## 1. 概要

| 項目 | 内容 |
|------|------|
| フレームワーク | FastAPI（Python、型ヒント付き） |
| 認証 | JWT（HttpOnly Cookie）。詳細は `JWT_USERNAME_TECH_SPEC.md` |
| アカウント ID | JWT の `username` で `accounts.username` を検索し、得た `accounts.id` を `aid` とする |
| ベースパス（アプリ内） | `/`（Nginx 経由では例: `/api/note/`） |

**共通ルール**

- 追加・更新対象は **自身の `aid` のレコードのみ**。
- 対象レコードが自身の `aid` に存在しない場合は **処理異常**（`result: false` と理由を返す）。
- 認証エラー（Cookie なし・JWT 不正・`username` 不備・該当アカウントなし）は **HTTP 401**。

**仕様書の更新**

- バックエンドに **新規エンドポイントを追加・変更したら、本書（`API_NOTE_SPEC.md`）も同時に更新する**。
- 更新内容: セクション 4 の一覧表、セクション 5 の詳細（Input / Output / 処理 / 失敗理由）、必要ならセクション 6 の補足。
- フロントエンドから新規に呼び出す API も、実装前後で本書と整合させる。

---

## 2. 環境変数

### 2.1 DB（`.env`）

| 変数 | 初期値例 |
|------|----------|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `tamtdb` |
| `DB_USER` | `tamtuser` |
| `DB_PASSWORD` | （`.env` 参照） |

### 2.2 JWT（認証 API と同一値を使用）

| 変数 | 説明 |
|------|------|
| `SECRET_KEY` | JWT 署名検証用秘密鍵 |
| `ALGORITHM` | 既定 `HS256` |
| `COOKIE_NAME` | 既定 `access_token` |
| `CORS_ORIGINS` | カンマ区切りオリジン（任意） |

### 2.3 デバッグ（開発環境のみ）

| 変数 | 説明 |
|------|------|
| `DEBUG` | `true` のとき JWT 検証を行わず、`DEBUG_AID` を `aid` として使う |
| `DEBUG_AID` | `DEBUG=true` 時の `aid`。既定 `1`（DB 参照なし） |
| `PARTS_MAX_REVISIONS` | パーツ置き換え時に保持する過去世代数（`jpeg` / `png` / `binary`）。既定 `3` |

**本番では `DEBUG` を `false` にするか未設定にすること。**

---

## 3. レスポンス形式

### 3.1 一覧・取得系（A 系）

HTTP **200**。本文は各 API の Output 定義に従う。エラー時は HTTP **400** 等と `detail`、または業務エラーを本文で返す（実装では存在しない ID は HTTP 404）。

### 3.2 操作系（B・C・D 系）

HTTP **200**。本文は共通形式:

```json
{
  "result": true,
  "reason": null
}
```

失敗時:

```json
{
  "result": false,
  "reason": "異常理由の文字列"
}
```

---

## 4. エンドポイント一覧

| ID | メソッド | パス | 概要 |
|----|----------|------|------|
| A-1 | POST | `/items/list` | フォルダ内アイテム一覧 |
| A-2 | POST | `/files/get` | ファイル詳細取得 |
| B-1 | POST | `/folders/create` | フォルダ作成 |
| B-2 | POST | `/folders/delete` | フォルダ削除 |
| B-3 | POST | `/folders/undelete` | フォルダ削除解除 |
| B-4 | POST | `/folders/rename` | フォルダ名変更 |
| B-5 | POST | `/folders/move` | フォルダ移動 |
| B-6 | POST | `/folders/swap-order` | フォルダ表示順入れ替え |
| C-1 | POST | `/files/create` | ファイル作成 |
| C-2 | POST | `/files/delete` | ファイル削除 |
| C-3 | POST | `/files/undelete` | ファイル削除解除 |
| C-4 | POST | `/files/rename` | ファイル名変更 |
| C-5 | POST | `/files/move` | ファイル移動 |
| C-6 | POST | `/files/swap-order` | ファイル表示順入れ替え |
| D-1 | POST | `/parts/create` | パーツ作成 |
| D-2 | POST | `/parts/delete` | パーツ削除 |
| D-3 | POST | `/parts/undelete` | パーツ削除解除 |
| D-4 | POST | `/parts/update` | パーツ編集 |
| D-5 | POST | `/parts/swap-order` | パーツ表示順入れ替え |
| D-6 | POST | `/parts/revision/get` | パーツ過去世代の取得（ダウンロード用） |
| E-1 | POST | `/table/get` | 表の取得 |
| E-2 | POST | `/table/cells/update` | セル更新 |
| E-3 | POST | `/table/cells/paste` | セルペースト |
| E-4 | POST | `/table/rows/insert` | 行挿入 |
| E-5 | POST | `/table/rows/delete` | 行削除 |
| E-6 | POST | `/table/cols/insert` | 列挿入 |
| E-7 | POST | `/table/cols/delete` | 列削除 |
| E-8 | POST | `/table/title/update` | 表タイトル更新 |
| E-9 | POST | `/table/col-width/update` | 列幅更新 |
| F-1 | POST | `/checklist/get` | チェックリスト取得 |
| F-2 | POST | `/checklist/title/update` | タイトル更新 |
| F-3 | POST | `/checklist/categories/create` | カテゴリ作成 |
| F-4 | POST | `/checklist/categories/update` | カテゴリ名更新 |
| F-5 | POST | `/checklist/categories/delete` | カテゴリ削除（論理） |
| F-6 | POST | `/checklist/categories/reorder` | カテゴリ並び替え |
| F-7 | POST | `/checklist/items/create` | チェック項目作成 |
| F-8 | POST | `/checklist/items/update` | チェック項目更新 |
| F-9 | POST | `/checklist/items/delete` | チェック項目削除（論理） |
| F-10 | POST | `/checklist/items/move` | チェック項目移動／並び替え |
| — | GET | `/health` | 稼働確認（認証不要） |

---

## 5. API 詳細

### A-1. アイテム一覧取得

**POST** `/items/list`

指定フォルダ直下の子フォルダ・ファイル一覧を返す。

**Input**

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `folder_id` | integer \| null | はい | 対象フォルダ ID。`null` のとき `parent IS NULL` のフォルダを列挙（ルート直下） |
| `include_deleted` | boolean | はい | `true` なら削除済みも含む。`false` なら `deleted_number = 0` のみ |

**Output**

```json
{
  "parent": { "id": 1, "name": "フォルダ名" },
  "folder": [
    { "id": 2, "dorder": 1, "name": "子フォルダ", "is_del": false }
  ],
  "file": [
    { "id": 3, "dorder": 1, "title": "メモ", "is_del": false }
  ]
}
```

| フィールド | 説明 |
|------------|------|
| `parent.id` | 対象フォルダ ID（`folder_id` が `null` のときは `null`） |
| `parent.name` | 対象フォルダ名（ルート一覧時は `null`） |
| `folder[].is_del` | 自身が削除済み、または祖先フォルダのいずれかが削除済みなら `true` |
| `file[].is_del` | 自身が削除済み、または所属フォルダ（祖先を含む）が削除済みなら `true` |

**処理:** `aid` 取得後、`note.folder`（`parent = folder_id`）と `note.file`（`belong = folder_id`）を検索。`folder_id` 指定時は当該フォルダが自アカウントに存在することを確認。

**ルート直下:** `folder_id = null` のときファイルは存在しない（`file` は常に空配列）。

**削除の連鎖表示:** フォルダ論理削除時、子フォルダ・配下ファイルの DB レコードは変更しない。一覧取得時に、祖先が削除済みの子要素は `is_del: true` とし、`include_deleted = false` のときは一覧から除外する。

---

### A-2. ファイル取得

**POST** `/files/get`

**Input**

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `file_id` | integer | はい | 対象ファイル ID |
| `include_deleted` | boolean | いいえ | 既定 `false`。`true` なら削除済みパーツも含む |

**Output**

```json
{
  "id": 1,
  "belong": { "id": 2, "name": "所属フォルダ名" },
  "title": "タイトル",
  "parts": [
    {
      "id": 10,
      "dorder": 1,
      "ptype": "binary",
      "data": "...",
      "filename": "memo.pdf",
      "title": "",
      "markers": [],
      "image_scale": 1.0,
      "is_del": false,
      "revisions": [
        {
          "id": 3,
          "revision_number": 2,
          "filename": "memo_old.pdf",
          "ptype": "binary",
          "created_at": "2026-06-15 12:00:00"
        }
      ]
    }
  ]
}
```

| フィールド | 説明 |
|------------|------|
| `parts[].filename` | 現在世代のファイル名（`jpeg` / `png` / `binary` で使用） |
| `parts[].title` | 表示用タイトル（`jpeg` / `png` で使用。任意。空文字可） |
| `parts[].markers` | 画像マーカー配列（`jpeg` / `png` で使用。各要素: `id`, `kind`=`house`/`number`, `x`/`y`（0〜1）, `text`, 番号時は `number`） |
| `parts[].image_scale` | 表示倍率（`jpeg` / `png` で使用。`1.0` = 100%。範囲 0.25〜4.0） |
| `parts[].revisions` | 過去世代の一覧（メタデータのみ。`data` は含まない）。`jpeg` / `png` / `binary` のみ |

**処理:** 自アカウントのファイル・所属フォルダ・パーツを取得。削除済みファイルも取得可。パーツは `include_deleted` に従いフィルタし、`dorder` 昇順で返す。各パーツに `is_del`（`is_deleted` の反映）を含む。

---

### B-1. フォルダ作成

**POST** `/folders/create`

**Input:** `{ "parent_id": N | null, "name": "aaa" }`

**Output:** `{ "result": true/false, "reason": "..." }`

**処理**

- `dorder` = 同一 `parent_id`（同一 `aid`）の最大値 + 1（0 件なら 1）
- `deleted_number` = 0
- 同一 `(aid, parent_id, deleted_number=0, name)` が既存なら `result: false`

---

### B-2. フォルダ削除

**POST** `/folders/delete`

**Input:** `{ "folder_id": n }`

**処理:** 対象フォルダの `deleted_number` を、同一 `(aid, parent, name)` の最大 `deleted_number` + 1 に更新。未削除（`deleted_number = 0`）のレコードのみ対象。

---

### B-3. フォルダ削除解除

**POST** `/folders/undelete`

**Input:** `{ "folder_id": n }`

**処理:** `deleted_number` を 0 に更新。同一 `(aid, parent, name)` で `deleted_number = 0` の別レコードがあれば `result: false`。`dorder` が同一 `(aid, parent)` 内の他レコードと衝突する場合は最大値 + 1 に再採番する。

---

### B-4. フォルダ名リネーム

**POST** `/folders/rename`

**Input:** `{ "folder_id": N, "name": "aaaa" }`

**処理:** `name` を更新。同一 `(aid, parent, deleted_number=0, name)` の重複があれば `result: false`。対象は未削除フォルダ。

---

### B-5. フォルダ移動

**POST** `/folders/move`

**Input**

```json
{
  "folder_id": 1,
  "old_parent_id": 2,
  "new_parent_id": 3
}
```

**処理**

1. 対象フォルダが自アカウントかつ `parent = old_parent_id` であることを確認
2. 移動先 `(aid, new_parent_id, deleted_number=0, name)` に同名があれば `result: false`
3. `parent` を `new_parent_id` に更新
4. `dorder` を移動先親での最大値 + 1 に再採番

---

### B-6. フォルダ表示順入れ替え

**POST** `/folders/swap-order`

**Input:** `{ "parent_id": n0, "folder_id_1": n1, "folder_id_2": n2 }`

**処理:** 同一 `parent_id` 配下の 2 フォルダの `dorder` を入れ替え。いずれも自アカウント・未削除であること。

---

### C-1. ファイル作成

**POST** `/files/create`

**Input:** `{ "folder_id": N, "title": "aaa" }`

**処理:** B-1 と同様。`belong = folder_id`、`dorder` は同一フォルダ内最大 + 1、`deleted_number = 0`。タイトル重複時は `result: false`。

---

### C-2. ファイル削除

**POST** `/files/delete`

**Input:** `{ "file_id": N }`

**処理:** `deleted_number` を同一 `(aid, belong, title)` の最大 + 1 に更新。

---

### C-3. ファイル削除解除

**POST** `/files/undelete`

**Input:** `{ "file_id": n }`

**処理:** `deleted_number = 0`。同一 `(aid, belong, title)` で `deleted_number = 0` の別レコードがあれば `result: false`。`dorder` が同一 `(aid, belong)` 内の他レコードと衝突する場合は最大値 + 1 に再採番する。

---

### C-4. ファイル名リネーム

**POST** `/files/rename`

**Input:** `{ "file_id": N, "name": "aaaa" }`  
（DB カラムは `title`。API 入力名は `name`）

**処理:** `title` を更新。同一 `(aid, belong, deleted_number=0, title)` 重複時は `result: false`。

---

### C-5. ファイル移動

**POST** `/files/move`

**Input:** `{ "file_id": n0, "old_parent_id": n1, "new_parent_id": n2 }`

**処理:** B-5 と同様。`belong` を `new_parent_id` に更新。`old_parent_id` は現在の `belong` と一致することを確認。

---

### C-6. ファイル表示順入れ替え

**POST** `/files/swap-order`

**Input:** `{ "parent_id": n0, "file_id_1": n1, "file_id_2": n2 }`  
（`parent_id` はフォルダ ID = ファイルの `belong`）

**処理:** 同一フォルダ内 2 ファイルの `dorder` を入れ替え。

---

### D-1. パーツ作成

**POST** `/parts/create`

**Input:** `{ "file_id": n, "type": "md", "data": "...", "filename": "optional", "title": "optional" }`

- `type`（API）→ DB の `ptype`。許容値: `jpeg` / `png` / `text` / `tex` / `md` / `binary` / `url` / `action` / `table` / `checklist`
- `jpeg` / `png` / `binary` のとき `data` は Base64 文字列
- `jpeg` / `png` / `binary` のとき **`filename` 必須**（空不可）
- `jpeg` / `png` のとき **`title` 任意**（表示用。省略時は空文字）
- `jpeg` / `png` のとき **`markers` 任意**（画像上のマーカー配列。省略時は空配列）
- `jpeg` / `png` のとき **`image_scale` 任意**（表示倍率。省略時は `1.0`。範囲 0.25〜4.0）
- `action`（行動予定）のとき `data` は **JSON 文字列**（構造は [D-4a](#d-4a-行動予定-action-の-data-形式)）
- `table`（表）のとき **`data` は空文字**。サーバーが `note.table` を作成し、`parts.data` にその ID を格納する（初期 5×5）
- `checklist`（チェックリスト）のとき **`data` は空文字**。サーバーが `note.checklist` を作成し、`parts.data` にその ID を格納する（初期はタイトル空・カテゴリ／項目なし）

**処理:** `dorder` = 同一ファイル内最大 + 1、`is_deleted = false`、`filename`・`title` を保存。`jpeg` / `png` 以外では `title` は空文字に正規化する。`action` のときは data の JSON 構造を検証する。`table` のときは [D-4b](#d-4b-表-table) を参照。`checklist` のときは [D-4c](#d-4c-チェックリスト-checklist) を参照。

---

### D-2. パーツ削除

**POST** `/parts/delete`

**Input:** `{ "parts_id": n }`

**処理:** `is_deleted = true`

---

### D-3. パーツ削除解除

**POST** `/parts/undelete`

**Input:** `{ "parts_id": n }`

**処理:** `is_deleted = false`

---

### D-4. パーツ編集

**POST** `/parts/update`

**Input:** `{ "parts_id": n, "type": "t2", "data": "d2", "filename": "name.bin", "title": "optional" }`

- `filename` 省略時は既存値を維持
- `title` 省略時は既存値を維持（`jpeg` / `png` のみ有効。他種別では空文字に正規化）
- `markers` 省略時は既存値を維持（`jpeg` / `png` のみ有効。他種別では空配列に正規化。画像データの差し替え時はリセット）
- `image_scale` 省略時は既存値を維持（`jpeg` / `png` のみ有効。他種別では `1.0` に正規化）
- `jpeg` / `png` / `binary` では **`filename` 必須**（省略時は既存値が空ならエラー）

**処理:** `ptype`・`data`・`filename`・`title` を更新。`jpeg` / `png` / `binary` で **画像データ・種別・filename** が変わる場合、更新前の状態を `note.parts_revision` に保存し、`PARTS_MAX_REVISIONS` を超える古い世代を削除する（`title` の変更のみでは世代は増えない）。`action` のときは data の JSON 構造を検証する。

---

### D-4a. 行動予定（`action`）の data 形式

`ptype` / `type` が `action` のとき、`data` は次の JSON オブジェクトを文字列化したもの。

```json
{
  "points": [
    { "place": "東京駅", "time": "9:00" },
    { "place": "新宿", "arrive": "10:00", "depart": "10:30" },
    { "place": "渋谷", "time": "14:00" }
  ],
  "legs": [
    { "memo": "山手線", "note": "快速利用\n2号車から乗車" },
    { "memo": "" }
  ]
}
```

| フィールド | 説明 |
|------------|------|
| `points` | 地点の配列（1 件以上） |
| `points[0]` | **地点1（任意）** — `place`（場所）・`time`（時刻）は任意。時刻は自由記述 |
| `points[i]`（i ≥ 1） | **地点2以降（任意）** — `place` および `time` または `arrive` / `depart` は任意。空の地点は末尾のみ省略可（地点1が空でも地点2以降があれば地点1の空レコードを保持し経由メモの対応を維持） |
| `points[i].time` | 単一時刻（地点2以降）。`arrive` / `depart` と同時指定不可 |
| `points[i].arrive` | 到着時刻（地点2以降・任意） |
| `points[i].depart` | 出発時刻（地点2以降・任意） |
| `legs` | 経由メモの配列。長さは **`points.length - 1`** |
| `legs[j].memo` | 地点 j+1 → j+2 間のメモ（任意・空文字可・1行想定） |
| `legs[j].note` | 経由メモの補足（任意・空文字可・**複数行可**。改行は `\n`） |

**検証ルール（API）**

- 地点1: `place`・`time` は任意（空白のみは不可の判定は「内容あり」チェックに含める）
- パーツ全体: 地点または経由メモ（`memo` / `note`）のいずれか **1件以上** の入力が必要
- `place`・`legs[].memo`・`legs[].note`: 文中・先頭の空白は保持する。クライアント保存時は **末尾空白のみ削除**（`trimEnd` / `rstrip`）
- 地点2以降: 全フィールド空の地点は無視（末尾の空地点のみ）
- `legs` の件数は有効な `points` の件数 − 1 と一致すること
- 地点2以降で `time` と `arrive` / `depart` を同時に指定しないこと

---

### D-4b. 表（`table`）

`ptype` / `type` が `table` のとき、`parts.data` には **`note.table.id` の文字列**を格納する。セルデータは `note.table_cell` に保持する。

**パーツ作成時:** `data` は空。サーバーが `note.table`（5 行 × 5 列）を作成し、生成 ID を `parts.data` に保存する。

**セル項目**

| 項目 | 説明 |
|------|------|
| `x`, `y` | 1 始まりの列・行 |
| `cell_type` | `string` / `date` / `time` / `datetime` / `number` |
| `input_value` | 入力値。`=` 始まりは数式 |
| `display_format` | 型に応じた表示形式 |
| `display_value` | サーバー算出済み表示値 |
| `text_align` | 表示位置（`左寄せ` / `中央寄せ` / `右寄せ`） |

**数式:** `Cell(x,y)` 参照（`$` で絶対座標）、四則演算 `+ - * /`、括弧、`If` / `And` / `Or` / `Not` と比較（`=` `>` `<`）。詳細は `NOTE_SPEC.md`。循環参照は `#CYCLE!`。

**型と数式:** 数値型は数式の結果を数値として表示。文字列型は文字列、日付型は日付、時刻型は時刻、日時型は日時として表示。いずれも結果の型がセル型と一致しない場合は `#VALUE!`。

---

### D-4c. チェックリスト（`checklist`）

`ptype` / `type` が `checklist` のとき、`parts.data` には **`note.checklist.id` の文字列**を格納する。

**パーツ作成時:** `data` は空。サーバーが `note.checklist`（タイトル空）を作成し、生成 ID を `parts.data` に保存する。初期はカテゴリ・項目なし。

**構造**

| 要素 | 説明 |
|------|------|
| タイトル | チェックリスト全体。空なら UI 非表示 |
| カテゴリ | 名称を自由入力。同名不可（生存行）。無名カテゴリ（`name=''`）は最大1つ。見出しは付けず項目のみ表示 |
| チェック項目 | タイトルとチェック状態。属するカテゴリを持つ |

**論理削除:** カテゴリ／項目の削除は `is_deleted=true`。カテゴリ削除時は配下項目も論理削除。復元 API は提供しない。詳細 API は [5c](#5c-チェックリスト-apif-系)。

---

### D-5. パーツ表示順入れ替え

**POST** `/parts/swap-order`

同一ファイル内の 2 パーツの `dorder` を入れ替える。フロントエンドのパーツ一覧で ↑ / ↓ 操作時に使用。

**Input**

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `file_id` | integer | はい | 対象ファイル ID |
| `parts_id_1` | integer | はい | 入れ替え対象パーツ ID（1 件目） |
| `parts_id_2` | integer | はい | 入れ替え対象パーツ ID（2 件目） |

**Output:** 操作系共通形式（`{ "result": true/false, "reason": "..." }`）

**処理**

1. `parts_id_1`・`parts_id_2` がいずれも自アカウント・同一 `file_id`・`is_deleted = false` であることを確認
2. 2 件の `dorder` を入れ替え（ユニーク制約 `(aid, file, dorder)` 回避のため一時値 `-1` を経由）

**失敗例（`result: false`）**

| `reason` 例 | 条件 |
|-------------|------|
| `指定されたパーツが見つかりません` | いずれかの ID が存在しない、別ファイル、削除済み、または他アカウント |

---

### D-6. パーツ過去世代取得

**POST** `/parts/revision/get`

過去世代の `data` を含む完全な内容を返す（ダウンロード用）。

**Input:** `{ "revision_id": n }`

**Output**

```json
{
  "id": 3,
  "parts_id": 10,
  "revision_number": 2,
  "filename": "memo_old.pdf",
  "ptype": "binary",
  "data": "...",
  "created_at": "2026-06-15 12:00:00"
}
```

**処理:** 自アカウントの `note.parts_revision` を取得。存在しない ID は HTTP 404。

---

## 5b. 表 API（E 系）

### E-1. 表取得

**POST** `/table/get`

**Input:** `{ "table_id": n }`

**Output**

```json
{
  "table_id": 1,
  "title": "売上表",
  "row_count": 5,
  "col_count": 5,
  "col_widths": [
    { "x": 1, "width_px": 120 }
  ],
  "cells": [
    {
      "x": 1,
      "y": 1,
      "cell_type": "number",
      "input_value": "=1+2",
      "display_format": "整数",
      "display_value": "3",
      "text_align": "左寄せ"
    }
  ]
}
```

値のあるセルのみ返す（スパース）。

---

### E-2. セル更新

**POST** `/table/cells/update`

**Input:** `{ "table_id", "x", "y", "cell_type"?, "input_value"?, "display_format"?, "text_align"? }`

**処理:** セルを upsert または `input_value` 空で削除。全セルの `display_value` を再計算して DB 更新。

**Output:** E-1 と同形式（更新後の全セル）

---

### E-3. セルペースト

**POST** `/table/cells/paste`

**Input:** `{ "table_id", "x", "y", "source_input_value", "source_cell_type", "source_display_format", "offset_x", "offset_y" }`

**処理:** 参照式の相対座標をオフセット分ずらしてから E-2 相当の更新を行う。

---

### E-4〜E-7. 行・列の挿入／削除

| ID | パス | Input |
|----|------|-------|
| E-4 | `/table/rows/insert` | `{ "table_id", "at_row" }` |
| E-5 | `/table/rows/delete` | `{ "table_id", "at_row" }` |
| E-6 | `/table/cols/insert` | `{ "table_id", "at_col" }` |
| E-7 | `/table/cols/delete` | `{ "table_id", "at_col" }` |

**処理:** セル座標と数式内 `Cell()` 参照を自動調整。`display_value` を再計算。

---

### E-8. 表タイトル更新

**POST** `/table/title/update`

**Input:** `{ "table_id", "title" }`

**処理:** `note.table.title` を更新する。セル内容は変更しない。

**Output:** E-1 と同形式

---

### E-9. 列幅更新

**POST** `/table/col-width/update`

**Input:** `{ "table_id", "x", "width_px" }`

- `x` … 列位置（1 始まり）
- `width_px` … 32〜480 の整数。`null` でその列の個別指定を解除（既定幅に戻す）

**処理:** `note.table_col_width` を更新する。列の挿入・削除時は列幅も座標に合わせてずらす。

**Output:** E-1 と同形式

---

## 5c. チェックリスト API（F 系）

### F-1. 取得

**POST** `/checklist/get`

**Input:** `{ "checklist_id": n }`

**Output**

```json
{
  "checklist_id": 1,
  "title": "買い物",
  "categories": [
    {
      "id": 10,
      "name": "",
      "is_unnamed": true,
      "dorder": 0,
      "items": [
        { "id": 100, "title": "牛乳", "is_checked": false, "dorder": 0 }
      ]
    },
    {
      "id": 11,
      "name": "日用品",
      "is_unnamed": false,
      "dorder": 1,
      "items": []
    }
  ]
}
```

削除済みカテゴリ／項目は含まない。無名カテゴリが無い場合は配列に現れない。

---

### F-2. タイトル更新

**POST** `/checklist/title/update` — `{ "checklist_id", "title" }`

---

### F-3〜F-6. カテゴリ

| ID | パス | Input |
|----|------|-------|
| F-3 | `/checklist/categories/create` | `{ "checklist_id", "name" }`（空不可・重複不可） |
| F-4 | `/checklist/categories/update` | `{ "checklist_id", "category_id", "name" }` |
| F-5 | `/checklist/categories/delete` | `{ "checklist_id", "category_id" }`（配下項目も論理削除） |
| F-6 | `/checklist/categories/reorder` | `{ "checklist_id", "ordered_ids": [..] }`（生存カテゴリ ID の全件並び） |

---

### F-7〜F-10. チェック項目

| ID | パス | Input |
|----|------|-------|
| F-7 | `/checklist/items/create` | `{ "checklist_id", "category_id"?, "title"? }`（`category_id` 省略／null は無名カテゴリへ。無ければ作成） |
| F-8 | `/checklist/items/update` | `{ "checklist_id", "item_id", "title"?, "is_checked"? }` |
| F-9 | `/checklist/items/delete` | `{ "checklist_id", "item_id" }` |
| F-10 | `/checklist/items/move` | `{ "checklist_id", "item_id", "to_category_id", "to_index" }` |

ミューテーション系の Output はいずれも F-1 と同形式。

---

## 6. 仕様レビュー（矛盾・抜け・本実装での補足）

元仕様をレビューした結果を記載する。

### 6.1 用語・カラム名の不一致

| 箇所 | 問題 | 本仕様での扱い |
|------|------|----------------|
| C-2, C-3 | 処理説明が「`aid, parent, title`」だが DB は `belong` | **`belong` を正**とする |
| C-4 | 入力が `name`、DB は `title` | 入力キーは `name`、DB 更新は `title` |
| B-5, C-5 | `parent` 更新手順の記載なし | **`parent` / `belong` の更新と dorder 再採番**を追加 |

### 6.2 処理内容の抜け（元仕様に無かったが実装に必要）

| 項目 | 補足内容 |
|------|----------|
| C-1 | `dorder` 採番・`deleted_number=0`・重複チェック（B-1 と同様） |
| D-1 | `dorder` 採番・`is_deleted=false` |
| B-5, C-5 | 現在の親が `old_parent_id` と一致するかの検証 |
| B-6, C-6, D-5 | 2 件が同一親／同一ファイル配下かの検証 |
| HTTP | メソッド・パスが未定義 → 本書で定義 |
| 認証失敗 | HTTP 401（`result` 形式ではない） |

### 6.3 確定したプロダクト判断

| 項目 | 決定内容 |
|------|----------|
| ルート（A-1） | ルート直下にファイルは存在しない。`folder_id = null` 時の `file` は空配列 |
| フォルダ削除と子要素 | DB 上は子をそのまま残す。一覧取得時、祖先が削除済みなら子は `is_del: true`（`include_deleted=false` なら除外） |
| A-2 パーツ | `include_deleted` で削除済みパーツの含否を指定。各パーツに `is_del` を付与 |
| A-2 削除済みファイル | 取得可 |
| B-3 / C-3 復元 | `dorder` 衝突時は最大値 + 1 に再採番 |

### 6.4 その他の実装補足

| 項目 | 内容 |
|------|------|
| パーツの `type` バリデーション | ドメイン型外の値を API で拒否する |
| D-5 フロント利用 | ファイル詳細画面でパーツ ↑ / ↓ により隣接 2 件の `parts_id` を指定して呼び出す |
| Nginx パスプレフィックス | `/api/note/` 等はデプロイ設定に依存。アプリ内パスは上表のとおり |

---

## 7. 関連ドキュメント

| ファイル | 内容 |
|----------|------|
| `DB_NOTE_SPEC.md` | DB スキーマ詳細 |
| `JWT_USERNAME_TECH_SPEC.md` | JWT・Cookie 認証 |
| `API_LOGIN_SPEC.md` | ログイン API・共通 JWT 検証 |
