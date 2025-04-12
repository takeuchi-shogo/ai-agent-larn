# Slack MCP Server

MCPプロトコルを使用してSlackにメッセージを送信するためのサーバーです。

## システムアーキテクチャ

```mermaid
graph TD
    AI[AIアシスタント] -->|MCP呼び出し| Server[Slack MCPサーバー]
    Server -->|標準入出力| Interface[MCP通信インターフェース]
    Interface -->|ツール登録/呼び出し| Handler[メッセージ送信ハンドラ]
    Handler -->|API呼び出し| Slack[Slack API]
    Slack -->|メッセージ送信| Channel[Slackチャンネル/ユーザー]
    
    classDef component fill:#f9f,stroke:#333,stroke-width:2px;
    classDef external fill:#bbf,stroke:#333,stroke-width:2px;
    
    class Server,Interface,Handler component;
    class AI,Slack,Channel external;
```

## デプロイメント図

```mermaid
graph TD
    subgraph "ユーザー環境"
        AI[AIアシスタント]
    end
    
    subgraph "ローカル/サーバー環境"
        MCP[Slack MCPサーバー]
        ENV[環境変数: SLACK_API_TOKEN]
    end
    
    subgraph "Slack インフラ"
        API[Slack API]
        WS[Slackワークスペース]
    end
    
    AI -->|標準入出力| MCP
    MCP -->|API呼び出し| API
    ENV -->|認証情報提供| MCP
    API -->|メッセージ配信| WS
    
    classDef user fill:#d0f0c0,stroke:#333,stroke-width:1px;
    classDef server fill:#f5deb3,stroke:#333,stroke-width:1px;
    classDef external fill:#add8e6,stroke:#333,stroke-width:1px;
    
    class AI user;
    class MCP,ENV server;
    class API,WS external;
```

## シーケンス図

```mermaid
sequenceDiagram
    participant AI as AIアシスタント
    participant MCP as Slack MCPサーバー
    participant Slack as Slack API
    
    AI->>MCP: ツール呼び出し (send_message)
    Note over AI,MCP: channel, message パラメータを含む
    
    MCP->>MCP: パラメータ検証
    
    alt パラメータ不正
        MCP-->>AI: エラーレスポンス
    else パラメータ正常
        MCP->>Slack: メッセージ送信 (PostMessage)
        Note over MCP,Slack: SLACK_API_TOKEN で認証
        
        alt 送信失敗
            Slack-->>MCP: エラーレスポンス
            MCP-->>AI: エラーレスポンス
        else 送信成功
            Slack-->>MCP: 成功レスポンス (channelID, timestamp)
            MCP-->>AI: 成功レスポンス
        end
    end
```

## 必要条件

- Go 1.20以上
- Slack APIトークン

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/slack-mcp.git
cd slack-mcp

# ビルド
go build -o slack-mcp
```

## 設定

サーバーを実行する前に、Slack APIトークンを環境変数として設定する必要があります：

```bash
export SLACK_API_TOKEN=xoxb-your-token-here
```

Slack APIトークンを取得するには：
1. [Slack API Apps](https://api.slack.com/apps)にアクセス
2. 新しいアプリを作成するか、既存のアプリを選択
3. "OAuth & Permissions"に移動
4. 以下のスコープを追加：
   - `chat:write`
   - `chat:write.public` （ボットが参加していないチャンネルにメッセージを送信する場合）
5. アプリをワークスペースにインストール
6. `xoxb-`で始まる"Bot User OAuth Token"をコピー

## 使用方法

サーバーの実行：

```bash
./slack-mcp
```

MCPサーバーは標準入出力（stdin/stdout）を介して通信するため、MCPプロトコルをサポートするAIアシスタントから呼び出されることを前提としています。

### ツール: send_message

このツールはSlackチャンネルまたはユーザーにメッセージを送信します。

パラメータ：
- `channel` (必須): Slackチャンネル（例：#general）またはユーザーID
- `message` (必須): 送信するメッセージテキスト

リクエスト例：
```json
{
  "id": "123",
  "method": "mcp.call_tool",
  "params": {
    "name": "send_message",
    "arguments": {
      "channel": "#general",
      "message": "MCPサーバーからこんにちは！"
    }
  }
}
```

レスポンス例：
```json
{
  "id": "123",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "メッセージが正常に送信されました。チャンネル: C12345678, タイムスタンプ: 1647123456.123456"
      }
    ]
  }
}
```

## トラブルシューティング

- **エラー: SLACK_API_TOKEN環境変数が設定されていません** - 環境変数が正しく設定されているか確認してください
- **エラー: channel_not_found** - チャンネル名が正しいこと、およびボットがチャンネルに追加されていることを確認してください
- **エラー: not_in_channel** - ボットをチャンネルに追加するか、`chat:write.public`スコープを使用してください