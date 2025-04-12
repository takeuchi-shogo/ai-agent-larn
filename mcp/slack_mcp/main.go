package main

import (
	"context"
	"log"
	"os"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"github.com/slack-go/slack"
)

func main() {
	log.Println("Slack MCPサーバーを起動します...")

	// MCPサーバーインスタンスの作成
	s := server.NewMCPServer(
		"slack-messenger",
		"1.0.0",
		server.WithLogging(),
	)
	log.Println("Slack MCPサーバーが作成されました")

	// Slackメッセージ送信ツールの定義
	sendMessageTool := mcp.NewTool("send_message",
		mcp.WithDescription("Slackチャンネルまたはユーザーにメッセージを送信する"),
		mcp.WithString("channel",
			mcp.Required(),
			mcp.Description("メッセージを送信するSlackチャンネル（例：#general）またはユーザーID"),
		),
		mcp.WithString("message",
			mcp.Required(),
			mcp.Description("送信するメッセージテキスト"),
		),
	)

	// Slackメッセージ送信ツールの実装
	s.AddTool(sendMessageTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// Slack APIトークンの取得
		token := os.Getenv("SLACK_API_TOKEN")
		if token == "" {
			return mcp.NewToolResultError("SLACK_API_TOKEN環境変数が設定されていません"), nil
		}

		// パラメータの取得
		channel := request.Params.Arguments["channel"].(string)
		message := request.Params.Arguments["message"].(string)

		// パラメータの検証
		if channel == "" {
			return mcp.NewToolResultError("チャンネルを指定してください"), nil
		}
		if message == "" {
			return mcp.NewToolResultError("メッセージを指定してください"), nil
		}

		// Slackクライアントの作成
		api := slack.New(token)

		// メッセージ送信
		channelID, timestamp, err := api.PostMessage(
			channel,
			slack.MsgOptionText(message, false),
		)
		if err != nil {
			return mcp.NewToolResultError("メッセージ送信に失敗しました: " + err.Error()), nil
		}

		// 成功レスポンスの返却
		return mcp.NewToolResultText("メッセージが正常に送信されました。チャンネル: " + channelID + ", タイムスタンプ: " + timestamp), nil
	})
	log.Println("Slackメッセージ送信ツールが追加されました")

	log.Println("標準入出力でサーバーを起動します...")
	// サーバーの起動
	if err := server.ServeStdio(s); err != nil {
		log.Fatalf("サーバーエラー: %v", err)
	}
	log.Println("サーバーが終了しました")
}
