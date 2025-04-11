import os
import json
import o3mini
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def dashboard_control(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST requests are allowed.")
    try:
        data = json.loads(request.body)
        instruction = data.get("instruction", "")
        if not instruction:
            return HttpResponseBadRequest("Missing 'instruction' in request payload.")
        # Set the OpenAI API key from environment variables (.env should have OPENAI_API_KEY)
        o3mini.api_key = os.getenv("O3_MINI_API_KEY")
        if not o3mini.api_key:
            return JsonResponse({"error": "O3_MINI_API_KEY not set in environment."}, status=500)
        # Create a ChatCompletion request using OpenAI API
        response = o3mini.ChatCompletion.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "Dashboard control instructions received."},
                {"role": "user", "content": instruction}
            ]
        )
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
