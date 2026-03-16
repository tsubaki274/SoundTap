# SoundTap

SoundTap は、キーボード入力やマウス操作に応じて、ユーザーが設定した mp3 を再生する Windows 向けデスクトップアプリです。

GUI 設定画面は持たず、`config.toml` を編集して好きな音声ファイルを割り当てます。

## セットアップ

```bash
# uv を入れていない場合
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Python 3.11 を用意
uv python install 3.11

# 開発用依存を含めて同期
uv sync --dev
```

`.python-version` で Python 3.11 を固定しています。

## 実行

```bash
uv run soundtap
```

または互換用エントリポイントとして次でも起動できます。

```bash
uv run python main.py
```

起動すると、初回は設定フォルダに `config.toml` を自動生成し、タスクトレイに常駐します。

## 設定ファイル

設定ファイルはユーザー設定ディレクトリ配下に作成されます。

- Windows: `%APPDATA%/SoundTap/config.toml`
- 実際の既定保存先: `%LOCALAPPDATA%/SoundTap/SoundTap/config.toml`

設定例:

```toml
[app]
master_volume = 80
scroll_cooldown_ms = 150

[hotkeys]
起動/停止 = "<ctrl>+<alt>+s"
ミュート = "<ctrl>+<alt>+m"
設定再読み込み = "<ctrl>+<alt>+r"

[keyboard.default]
path = "C:/Sounds/type.mp3"
volume = 50

[keyboard.a]
path = "C:/Sounds/a.mp3"
volume = 100

[keyboard.enter]
path = "C:/Sounds/enter.mp3"
volume = 70

[keyboard.space]
path = "C:/Sounds/space.mp3"
volume = 60

[keyboard.escape]
path = "C:/Sounds/escape.mp3"
volume = 80

[keyboard.shift]
path = "C:/Sounds/shift.mp3"
volume = 60

[mouse.default]
path = "C:/Sounds/mouse.mp3"
volume = 50

[mouse.left]
path = "C:/Sounds/click.mp3"
volume = 50

[mouse.right]
path = "C:/Sounds/right.mp3"
volume = 60

[mouse.middle]
path = "C:/Sounds/middle.mp3"
volume = 50

[mouse.wheel_up]
path = "C:/Sounds/wheel-up.mp3"
volume = 40

[mouse.wheel_down]
path = "C:/Sounds/wheel-down.mp3"
volume = 40
```

### 設定ルール

- `master_volume` は全体音量で、`0` から `100` の範囲です
- `scroll_cooldown_ms` はホイール入力の連続再生を抑える間隔で、ミリ秒単位です。初期値は `150` です
- `hotkeys.toggle_enabled` は `開始/停止` の切替です。初期値は `Ctrl+Alt+S` です
- `hotkeys.toggle_mute` はミュート切替です。初期値は `Ctrl+Alt+M` です
- `hotkeys.reload_config` は設定再読み込みです。初期値は `Ctrl+Alt+R` です
- ホットキー設定が不正な場合、その項目は警告ログを出して既定値にフォールバックします
- `keyboard.default` を設定すると、すべてのキー入力に同じ音を一括適用できます
- `mouse.default` を設定すると、すべてのマウス入力に同じ音を一括適用できます
- 個別キー設定がある場合は、`keyboard.default` より個別設定を優先します
- 個別マウス設定がある場合は、`mouse.default` より個別設定を優先します
- キーボードは通常キーだけでなく、Enter、Space、Shift、Ctrl、Alt、Esc などの特殊キーにも反応します
- キー名は `a`、`b`、`1`、`enter`、`space`、`escape`、`shift`、`ctrl`、`alt` のように書けます
- マウスは `left`、`right`、`middle`、`wheel_up`、`wheel_down` を設定できます
- Windows パスを貼るときは `C:/Sounds/a.mp3` のように `/` を使うか、`C:\\Sounds\\a.mp3` のように `\\` を重ねて書いてください
- キーボードは押した瞬間の 1 回だけ反応し、押しっぱなしによるキーリピートは無視します
- マウスはクリックした瞬間だけ反応し、ホイールはクールダウン間隔をあけて反応します
- ミュート中は入力を検知しても音を再生しません

## デスクトップショートカットで起動する

`uv run` を毎回使いたくない場合は、Windows 向け `exe` を作ってショートカットを置く運用が簡単です。

```bash
uv run pyinstaller --clean SoundTap.spec
```

生成された `SoundTap.exe` を右クリックして「ショートカットの作成」を行い、デスクトップに置けばダブルクリックで起動できます。

起動後の操作はグローバルホットキーで行えます。

- `Ctrl+Alt+S`: 開始 / 停止
- `Ctrl+Alt+M`: ミュート切替
- `Ctrl+Alt+R`: 設定再読み込み

## トレイメニュー

タスクトレイから次の操作ができます。

- ミュート
- 開始
- 停止
- 設定を再読み込み
- 設定フォルダを開く
- 終了

## 注意点

- 音声ファイル自体は GitHub に同梱せず、利用者のローカルファイルを参照する設計です
- セキュリティ上の理由で、UNC パス (`//server/share/...`) とネットワーク共有を指すマップドドライブは読み込み対象にしません
- グローバル入力監視とグローバルホットキーは Windows の権限やセキュリティソフトの影響を受ける場合があります
- mp3 の再生可否は実行環境の SDL / pygame 構成に依存します
