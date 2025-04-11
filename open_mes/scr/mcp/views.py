from datetime import datetime
import os
import json
from django.http import JsonResponse, HttpResponseBadRequest, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from .o3mini import O3MiniAPI

@csrf_exempt
def dashboard_control(request):
    # POST 以外はエラー
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST requests are allowed.')

    try:
        # JSON 解析
        data = json.loads(request.body)
        instruction = data.get('instruction', '')
        if not instruction:
            return HttpResponseBadRequest("Missing 'instruction' in request payload.")

        # 環境変数から API キーを取得
        api_key = os.getenv('O3_MINI_API_KEY')
        if not api_key:
            return JsonResponse({'error': 'O3_MINI_API_KEY not set in environment.'}, status=500)

        # O3MiniAPI クライアントを初期化
        api_client = O3MiniAPI(api_key=api_key)

        # o3-mini 用のプロンプトを生成
        prompt = f"生産数値と指令ステータスをJSONで返却してください。ユーザー入力: {instruction}"

        # コード生成関数を呼び出して応答を取得
        result_text = api_client.generate_code(content=prompt, reasoning_effort='medium')

        # 生成結果は通常文字列なので JSON としてパースを試みる
        try:
            parsed_json = json.loads(result_text)
            production_value = parsed_json.get('production_value', 0)
            status = parsed_json.get('status', '処理中')
        except (ValueError, TypeError):
            production_value = 0
            status = 'エラー'

        # 結果を返却
        response_data = {
            'value': production_value,
            'instruction': instruction,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        return JsonResponse(response_data, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
