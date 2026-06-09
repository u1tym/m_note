# Note API

ノートアプリ用の FastAPI バックエンドです。フォルダ・ファイル・パーツ（テキストや画像などの断片）を PostgreSQL で管理します。

認証は別サービス（認証 API）が発行する JWT を HttpOnly Cookie で受け取り、JWT の `username` からアカウント ID を解決して操作します。

---

## 前提

| 項目 | 内容 |
|------|------|
| Python | 3.11 以上を推奨 |
| DB | PostgreSQL（`note` スキーマ） |
| 認証 | 認証 API でログイン済みであること（Cookie に JWT がセットされていること） |

詳細な API・DB 仕様は以下を参照してください。

- [API_NOTE_SPEC.md](API_NOTE_SPEC.md) — API 仕様
- [DB_NOTE_SPEC.md](DB_NOTE_SPEC.md) — DB スキーマ
- [JWT_USERNAME_TECH_SPEC.md](JWT_USERNAME_TECH_SPEC.md) — JWT 認証
- [API_LOGIN_SPEC.md](API_LOGIN_SPEC.md) — ログイン API（認証サービス側）

---

## セットアップ

### 1. リポジトリのルートへ移動

```powershell
cd d:\githome\mobile\m_note
```

### 2. 仮想環境の作成と有効化（任意）

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

### 3. 依存パッケージのインストール

```powershell
pip install -r requirements.txt
```

### 4. 環境変数ファイル（`.env`）の作成

リポジトリルートに `.env` を置きます（`.gitignore` 対象のためリポジトリには含まれません）。

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tamtdb
DB_USER=tamtuser
DB_PASSWORD=TAMTTAMT

SECRET_KEY=change-me-in-production
ALGORITHM=HS256
COOKIE_NAME=access_token
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

| 変数 | 説明 |
|------|------|
| `DB_*` | PostgreSQL 接続情報 |
| `SECRET_KEY` | JWT 署名検証用秘密鍵（**認証 API と同一の値**） |
| `ALGORITHM` | JWT アルゴリズム（既定 `HS256`） |
| `COOKIE_NAME` | JWT を載せる Cookie 名（既定 `access_token`） |
| `CORS_ORIGINS` | ブラウザからアクセスする場合の許可オリジン（カンマ区切り） |

### 5. データベースの準備

PostgreSQL に `accounts` テーブル（認証用）と `note` スキーマが必要です。

DDL の参考:

- `for_human_memo/db.sql` — `note` スキーマの作成スクリプト
- `DB_NOTE_SPEC.md` — テーブル定義の説明

例（`psql` で実行）:

```powershell
psql -h localhost -U tamtuser -d tamtdb -f for_human_memo\db.sql
```

---

## サーバーの起動

リポジトリルートで実行します。

```powershell
uvicorn note_api.app.main:app --reload --host 0.0.0.0 --port 8000
```

起動後:

| URL | 内容 |
|-----|------|
| http://localhost:8000/health | 稼働確認（認証不要） |
| http://localhost:8000/docs | Swagger UI（開発用） |

`/health` の応答例:

```json
{ "status": "ok" }
```

Nginx 等でリバースプロキシする場合、アプリ内パスの前に `/api/note/` などのプレフィックスを付ける構成が一般的です（詳細は `API_NOTE_SPEC.md` 参照）。

---

## 認証の使い方

本 API は **JWT を発行しません**。認証 API でログインし、Cookie に JWT がセットされた状態でリクエストしてください。

1. 認証 API の `POST /login` でログインする
2. ブラウザが `access_token` Cookie を保持する
3. 本 API へ `credentials: 'include'`（または `withCredentials: true`）付きでリクエストする

JWT の `username` と DB の `accounts.username` を突合し、`accounts.id` をアカウント ID として各操作に使います。

認証エラー時は HTTP **401** が返ります。操作系 API（フォルダ作成など）の業務エラーは HTTP **200** で `result: false` となります。

---

## API の使い方

すべて **POST**（`/health` を除く）。リクエスト・レスポンスの JSON キーは [API_NOTE_SPEC.md](API_NOTE_SPEC.md) に準拠します。

### エンドポイント一覧

| ID | パス | 概要 |
|----|------|------|
| A-1 | `POST /items/list` | フォルダ内の子フォルダ・ファイル一覧 |
| A-2 | `POST /files/get` | ファイル詳細（パーツ含む） |
| B-1 | `POST /folders/create` | フォルダ作成 |
| B-2 | `POST /folders/delete` | フォルダ削除 |
| B-3 | `POST /folders/undelete` | フォルダ削除解除 |
| B-4 | `POST /folders/rename` | フォルダ名変更 |
| B-5 | `POST /folders/move` | フォルダ移動 |
| B-6 | `POST /folders/swap-order` | フォルダ表示順入れ替え |
| C-1 | `POST /files/create` | ファイル作成 |
| C-2 | `POST /files/delete` | ファイル削除 |
| C-3 | `POST /files/undelete` | ファイル削除解除 |
| C-4 | `POST /files/rename` | ファイル名変更 |
| C-5 | `POST /files/move` | ファイル移動 |
| C-6 | `POST /files/swap-order` | ファイル表示順入れ替え |
| D-1 | `POST /parts/create` | パーツ作成 |
| D-2 | `POST /parts/delete` | パーツ削除 |
| D-3 | `POST /parts/undelete` | パーツ削除解除 |
| D-4 | `POST /parts/update` | パーツ編集 |
| D-5 | `POST /parts/swap-order` | パーツ表示順入れ替え |

### curl の例

Cookie に JWT が入っている前提です（`-b` で Cookie ファイルを指定するか、ブラウザ経由で試してください）。

**フォルダ内一覧（A-1）**

```bash
curl -X POST http://localhost:8000/items/list \
  -H "Content-Type: application/json" \
  -b "access_token=YOUR_JWT_HERE" \
  -d "{\"folder_id\": 1, \"include_deleted\": false}"
```

**ファイル取得（A-2）**

```bash
curl -X POST http://localhost:8000/files/get \
  -H "Content-Type: application/json" \
  -b "access_token=YOUR_JWT_HERE" \
  -d "{\"file_id\": 1, \"include_deleted\": false}"
```

**フォルダ作成（B-1）**

```bash
curl -X POST http://localhost:8000/folders/create \
  -H "Content-Type: application/json" \
  -b "access_token=YOUR_JWT_HERE" \
  -d "{\"parent_id\": null, \"name\": \"メモ\"}"
```

**パーツ作成（D-1）**

```bash
curl -X POST http://localhost:8000/parts/create \
  -H "Content-Type: application/json" \
  -b "access_token=YOUR_JWT_HERE" \
  -d "{\"file_id\": 1, \"type\": \"md\", \"data\": \"# 見出し\"}"
```

`type` が `jpeg` / `png` / `binary` のとき、`data` は Base64 文字列を指定します。

### 操作系 API の応答

成功:

```json
{ "result": true, "reason": null }
```

失敗:

```json
{ "result": false, "reason": "同名のフォルダが既に存在します" }
```

---

## フロントエンドからの呼び出し（fetch）

```javascript
const res = await fetch("http://localhost:8000/items/list", {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ folder_id: 1, include_deleted: false }),
});
const data = await res.json();
```

`CORS_ORIGINS` にフロントのオリジンを登録し、`credentials: "include"` を付ける必要があります。

---

## プロジェクト構成

```
m_note/
├── README.md                 # 本ファイル
├── API_NOTE_SPEC.md          # API 仕様書
├── DB_NOTE_SPEC.md           # DB 仕様書
├── requirements.txt
├── .env                      # 環境変数（各自作成）
├── for_human_memo/
│   └── db.sql                # note スキーマ DDL
└── note_api/
    └── app/
        ├── main.py           # FastAPI エントリポイント
        ├── config.py         # 設定読み込み
        ├── database.py       # DB 接続
        ├── deps.py           # 認証・DB 依存注入
        ├── models.py         # SQLAlchemy モデル
        ├── schemas.py        # Pydantic スキーマ
        ├── security/
        │   └── jwt_verifier.py
        ├── services/
        │   └── note_service.py
        └── routers/
            ├── items.py
            ├── folders.py
            ├── files.py
            └── parts.py
```

---

## よくある操作の流れ

1. 認証 API でログインする
2. `POST /folders/create` でルートまたは子フォルダを作る（`parent_id: null` でルート直下）
3. `POST /files/create` でフォルダ内にファイルを作る
4. `POST /parts/create` でファイルにパーツ（本文・画像など）を追加する
5. `POST /items/list` でフォルダ内容を一覧表示する
6. `POST /files/get` でファイルとパーツの詳細を取得する

ルート直下（`folder_id: null`）にはフォルダのみ存在し、ファイルは常にいずれかのフォルダ配下に置きます。

---

## トラブルシューティング

| 症状 | 確認事項 |
|------|----------|
| `ModuleNotFoundError` | `pip install -r requirements.txt` を実行したか |
| `401 認証が必要です` | 認証 API でログイン済みか、Cookie が送信されているか |
| `401 無効なトークンです` | `.env` の `SECRET_KEY` が認証 API と一致しているか |
| DB 接続エラー | PostgreSQL が起動しているか、`.env` の接続情報が正しいか |
| CORS エラー | `CORS_ORIGINS` にフロントのオリジンが含まれているか、`credentials` が有効か |
| 制約違反（unique） | 同名フォルダ・ファイル、または表示順の衝突。仕様書の重複チェックを参照 |

---

## 開発メモ

- インポート確認: `python -c "from note_api.app.main import app; print(app.title)"`
- API の挙動変更時は `API_NOTE_SPEC.md` も合わせて更新してください
