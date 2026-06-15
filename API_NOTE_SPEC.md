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

**Input:** `{ "file_id": n, "type": "md", "data": "...", "filename": "optional" }`

- `type`（API）→ DB の `ptype`
- `jpeg` / `png` / `binary` のとき `data` は Base64 文字列
- `jpeg` / `png` / `binary` のとき **`filename` 必須**（空不可）

**処理:** `dorder` = 同一ファイル内最大 + 1、`is_deleted = false`、`filename` を保存。

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

**Input:** `{ "parts_id": n, "type": "t2", "data": "d2", "filename": "name.bin" }`

- `filename` 省略時は既存値を維持
- `jpeg` / `png` / `binary` では **`filename` 必須**（省略時は既存値が空ならエラー）

**処理:** `ptype`・`data`・`filename` を更新。`jpeg` / `png` / `binary` で内容が変わる場合、更新前の状態を `note.parts_revision` に保存し、`PARTS_MAX_REVISIONS` を超える古い世代を削除する。

---

### D-5. パーツ表示順入れ替え

**POST** `/parts/swap-order`

**Input:** `{ "file_id": n0, "parts_id_1": n1, "parts_id_2": n2 }`

**処理:** 同一ファイル内 2 パーツの `dorder` を入れ替え（未削除であること）。

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
| Nginx パスプレフィックス | `/api/note/` 等はデプロイ設定に依存。アプリ内パスは上表のとおり |

---

## 7. 関連ドキュメント

| ファイル | 内容 |
|----------|------|
| `DB_NOTE_SPEC.md` | DB スキーマ詳細 |
| `JWT_USERNAME_TECH_SPEC.md` | JWT・Cookie 認証 |
| `API_LOGIN_SPEC.md` | ログイン API・共通 JWT 検証 |
