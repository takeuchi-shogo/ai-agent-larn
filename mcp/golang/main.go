package main

import (
	"context"
	"fmt"
	"log"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

func main() {
	log.Println("MCPサーバーを起動します...")
	// MCPサーバーインスタンスの作成
	s := server.NewMCPServer(
		"calculator",
		"1.0.0",
		server.WithResourceCapabilities(true, true), // リソース機能のオプション（ツールの公開のみの場合は不要）
		server.WithLogging(),
	)
	log.Println("MCPサーバーが作成されました")

	// 四則演算ツールのインターフェース定義
	calculatorTool := mcp.NewTool("calculate",
		mcp.WithDescription("基本的な四則演算を実行します"),
		mcp.WithString("operation",
			mcp.Required(),
			mcp.Description("実行する演算（add:加算, subtract:減算, multiply:乗算, divide:除算）"),
			mcp.Enum("add", "subtract", "multiply", "divide"),
		),
		mcp.WithNumber("x",
			mcp.Required(),
			mcp.Description("1番目の数値"),
		),
		mcp.WithNumber("y",
			mcp.Required(),
			mcp.Description("2番目の数値"),
		),
	)

	// 四則演算ツールの実装
	s.AddTool(calculatorTool, func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		// パラメータの取得
		op := request.Params.Arguments["operation"].(string)
		x := request.Params.Arguments["x"].(float64)
		y := request.Params.Arguments["y"].(float64)

		var result float64
		switch op {
		case "add": // 加算
			result = x + y
		case "subtract": // 減算
			result = x - y
		case "multiply": // 乗算
			result = x * y
		case "divide": // 除算
			if y == 0 {
				return mcp.NewToolResultError("0による除算はできません"), nil
			}
			result = x / y
		}

		// 結果を小数点以下2桁まで表示
		return mcp.NewToolResultText(fmt.Sprintf("%.2f", result)), nil
	})
	log.Println("四則演算ツールが追加されました")

	log.Println("標準入出力でサーバーを起動します...")
	// サーバーの起動
	if err := server.ServeStdio(s); err != nil {
		log.Printf("サーバーエラー: %v\n", err)
		fmt.Printf("サーバーエラー: %v\n", err)
	}
	log.Println("サーバーが起動しました")
}
