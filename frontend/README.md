# メモ管理フロントエンド

Vue 3 + TypeScript + Vite。スマホ向け UI を前提としています。

## 環境変数

| 変数 | 説明 |
|------|------|
| `VITE_NOTE_ORIGIN` | Note API の起点。例: `/api/note` |
| `VITE_LOGIN_ORIGIN` | 認証 API の起点。例: `/api/auth` |
| `VITE_LOGIN_PAGE_URL` | 未ログイン時のリダイレクト先 |
| `VITE_MENU_PAGE_URL` | 戻るボタンの遷移先。**`#` を含む場合は値を `"..."` で囲む**（例: `"/mobile/login/#/menu"`） |
| `VITE_SKIP_SESSION_EXTEND` | `true` のとき NOTE API 前の `POST /refresh` をスキップ（デバッグ用） |
| `VITE_NOTE_PROXY_TARGET` | 開発時プロキシ先（既定 `http://127.0.0.1:8000`） |
| `VITE_BASE_PATH` | 本番の公開パス（例: `/mobile/notes/`、末尾スラッシュ必須） |

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
- `VITE_BASE_PATH=/mobile/notes/`（nginx の `location` と一致させる）
- NOTE API 呼び出し前に `POST {VITE_LOGIN_ORIGIN}/refresh` で JWT 更新
- 401 時は `VITE_LOGIN_PAGE_URL` へリダイレクト

#### ビルドと nginx

```powershell
cd frontend
cp .env.production.example .env.production   # 必要に応じて編集
npm run build
# dist/ をサーバへ配置
```

nginx 例（`dist` を `/var/www/notes/dist` に置いた場合）:

```nginx
location /mobile/notes/ {
    alias /var/www/notes/dist/;
    try_files $uri $uri/ /mobile/notes/index.html;
}
```

**画面が真っ白なとき**

1. ブラウザの開発者ツール → **Network** で `assets/*.js` が 404 になっていないか
2. **Console** に JS エラーがないか
3. `VITE_BASE_PATH` と nginx の `location` が一致しているか
4. ルーターが `createWebHistory(import.meta.env.BASE_URL)` になっているか（`base` だけ設定してもルーター未設定だと真っ白になる）

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
