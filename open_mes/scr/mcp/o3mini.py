class O3MiniMock:
    """
    MCP統合用モッククラス
    実際のO3 Miniデバイスとの通信をエミュレート
    """
    @staticmethod
    def get_data():
        return {
            'temperature': 25.4,
            'humidity': 55.2,
            'co2': 412,
            'timestamp': '2025-04-12 01:45:00'
        }

    @staticmethod
    def send_command(command):
        print(f"Mock command sent: {command}")
        return True

from openai import OpenAI

class O3MiniAPI:
    """
    o3-mini API連携クラス
    """
    def __init__(self, api_key=None):
        # 環境変数などでAPIキーを設定する場合は下記を調整してください
        self.client = OpenAI(api_key=api_key or "YOUR_API_KEY")

    def generate_code(self, content, reasoning_effort="medium"):
        """
        o3-miniモデルを使ったテキスト生成・コード生成用関数
        """
        response = self.client.chat.completions.create(
            model="o3-mini",
            messages=[{"role": "developer", "content": content}],
            reasoning_effort=reasoning_effort
        )
        return response.choices[0].message.content
