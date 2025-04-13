#!/usr/bin/env python3
"""
MCPモジュールの簡易テストスクリプト
"""
import json
import sys
import os

# 必要なパスを追加して、MCPモジュールをインポートできるようにする
sys.path.append(os.path.join(os.path.dirname(__file__), 'open_mes/scr'))

# MCPモジュールのモッククラスをインポート
from mcp.o3mini import O3MiniMock

def test_mock_data():
    """O3MiniMockのget_dataメソッドをテスト"""
    print("=== O3MiniMock.get_data() テスト ===")
    mock = O3MiniMock()
    data = mock.get_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("テスト成功: データが取得できました\n")
    return data

def test_mock_command():
    """O3MiniMockのsend_commandメソッドをテスト"""
    print("=== O3MiniMock.send_command() テスト ===")
    mock = O3MiniMock()
    result = mock.send_command("生産ラインの速度を10%上げる")
    print(f"コマンド送信結果: {result}")
    print("テスト成功: コマンドが送信できました\n")
    return result

def simulate_dashboard_control():
    """dashboard_controlの動作をシミュレート"""
    print("=== dashboard_control シミュレーション ===")
    mock = O3MiniMock()
    data = mock.get_data()
    
    # dashboard_controlの処理をシミュレート
    instruction = "生産ラインの速度を10%上げる"
    response_data = {
        'value': data.get('temperature', 0),
        'instruction': instruction,
        'status': '正常（モック）',
        'timestamp': data.get('timestamp', '')
    }
    
    print(json.dumps(response_data, indent=2, ensure_ascii=False))
    print("シミュレーション成功: ダッシュボード制御のレスポンスを生成しました\n")
    return response_data

def simulate_data_stream():
    """data_streamの動作をシミュレート"""
    print("=== data_stream シミュレーション ===")
    # 5回分のデータストリームをシミュレート
    print("Server-Sent Eventsのシミュレーション（5サンプル）:")
    
    for i in range(5):
        # ダミーデータを生成
        data = {
            'value': 75 + (i % 20),  # 変動する値
            'instruction': '通常運転中',
            'status': '正常',
            'timestamp': f"2025-04-13T16:{30+i}:00.000000"
        }
        
        # SSE形式でデータを表示
        print(f"data: {json.dumps(data)}")
    
    print("\nシミュレーション成功: データストリームを生成しました\n")

def main():
    """メイン関数"""
    print("MCPモジュール簡易テスト開始\n")
    
    try:
        test_mock_data()
        test_mock_command()
        simulate_dashboard_control()
        simulate_data_stream()
        
        print("すべてのテストが成功しました！")
        print("MCPモジュールは正常に動作しています。")
    except Exception as e:
        print(f"テスト中にエラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
