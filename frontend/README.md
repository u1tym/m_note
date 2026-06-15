# メモ管理フロントエンド

Vue 3 + TypeScript + Vite。スマホ向け UI を前提としています。

## 環境変数

| 変数 | 説明 |
|------|------|
| `VITE_NOTE_ORIGIN` | Note API の起点。例: `/api/note` |
| `VITE_LOGIN_ORIGIN` | 認証 API の起点。例: `/api/auth` |
| `VITE_LOGIN_PAGE_URL` | 未ログイン時のリダイレクト先 |
| `VITE_MENU_PAGE_URL` | 戻るボタンの遷移先（例: `/mobile/login/#/menu`） |
| `VITE_SKIP_SESSION_EXTEND` | `true` のとき NOTE API 前の `POST /refresh` をスキップ（デバッグ用） |
| `VITE_NOTE_PROXY_TARGET` | 開発時プロキシ先（既定 `http://127.0.0.1:8000`） |

### デバッグ（`.env.development`）

**既定は Vite プロキシ**（`03_note_frontend.txt` の CORS 回避方針どおり）。

```env
VITE_NOTE_ORIGIN=/api/note
VITE_NOTE_PROXY_TARGET=http://127.0.0.1:8000
VITE_SKIP_SESSION_EXTEND=true
```

| 方式 | `VITE_NOTE_ORIGIN` | CORS |
|------|-------------------|------|
| プロキシ（既定） | `/api/note` | **不要**（ブラウザ → Vite が同一オリジン） |
| 直接接続（代替） | `http://127.0.0.1:8000` | **必要**（`CORS_ORIGINS` にフロントのオリジンを追加） |

プロキシ先は **`http://127.0.0.1:8000`** を使ってください。`localhost` は Windows で IPv6 になり ETIMEDOUT することがあります。

**ETIMEDOUT が出る場合:** Note API が 8000 で起動しているか確認してください（プロキシはあくまで Vite → バックエンドの中継です）。

```powershell
uvicorn note_api.app.main:app --reload --host 127.0.0.1 --port 8000
```

ローカル開発ではバックエンド `.env` に `DEBUG=true` / `DEBUG_AID=1` を設定すると Cookie なしで試せます。

### 本番（`.env.production`）

- `VITE_NOTE_ORIGIN=/api/note`
- `VITE_LOGIN_ORIGIN=/api/auth`
- NOTE API 呼び出し前に `POST {VITE_LOGIN_ORIGIN}/refresh` で JWT 更新
- 401 時は `VITE_LOGIN_PAGE_URL` へリダイレクト

## 開発

```powershell
cd frontend
npm install
npm run dev
```

Note API（別ターミナル、リポジトリルート）:

```powershell
uvicorn note_api.app.main:app --reload --host 127.0.0.1 --port 8000
```

ローカル開発ではバックエンド `.env` に `DEBUG=true` と `DEBUG_AID=1` を設定すると、認証 Cookie なしで API を試せます（`backend/dot.env` 参照）。

### たまに `ETIMEDOUT 127.0.0.1:8000` が出る場合

`ETIMEDOUT` は **その瞬間に TCP 接続できなかった** エラーです（API の処理が遅いこととは別）。

よくある原因:

- **uvicorn `--reload` の再起動** … ファイル保存直後は数秒つながらない
- **バックエンド停止** … ターミナルを閉じた、エラーで落ちた
- **大きなパーツ POST** … 接続後の待ちはプロキシ 120 秒に延長済み

フロントは一時的な接続失敗を **最大 2 回リトライ** します。Vite を再起動して変更を反映してください。

## 機能

- フォルダツリー（作成・リネーム・移動・論理削除）
- ファイル（作成・リネーム・移動・論理削除）— ルート直下には不可
- パーツ（作成・更新・論理削除）、Markdown / TeX プレビュー

## API 仕様

- [API_NOTE_SPEC.md](../API_NOTE_SPEC.md)
- [API_LOGIN_SPEC.md](../API_LOGIN_SPEC.md)
