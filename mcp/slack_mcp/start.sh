#!/bin/bash

# Slack MCPサーバー起動スクリプト

# Slack APIトークンが環境変数にセットされているか確認
if [ -z "$SLACK_API_TOKEN" ]; then
    echo "エラー: SLACK_API_TOKEN環境変数が設定されていません"
    echo "以下のコマンドでトークンを設定してください:"
    echo "export SLACK_API_TOKEN=xoxb-your-token-here"
    exit 1
fi

# ログファイルの設定
LOG_FILE="slack-mcp.log"

echo "Slack MCPサーバーを起動しています..."
echo "ログは $LOG_FILE に記録されます"

# サーバーをバックグラウンドで実行し、ログを記録
./slack-mcp > "$LOG_FILE" 2>&1 &

# プロセスIDを表示
PID=$!
echo "サーバーが起動しました (PID: $PID)"
echo "サーバーを停止するには: kill $PID"