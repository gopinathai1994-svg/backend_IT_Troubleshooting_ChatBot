from flask import Flask, request, jsonify
from services.gemini_service import gemini_service
import json

app = Flask(__name__)


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():

    try:

        prompt = request.form.get("prompt")
        file = request.files.get("file")

        if not prompt:
            return jsonify({
                "status": "error",
                "message": "Prompt is required.",
                "solution": []
            }), 400

        if file:

            image_bytes = file.read()

            raw_response = gemini_service.generate_multimodal_response(
                prompt,
                image_bytes
            )

        else:

            raw_response = gemini_service.generate_text_response(
                prompt
            )

        # Remove markdown code blocks
        cleaned_response = raw_response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]

        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        cleaned_response = cleaned_response.strip()

        # Convert Gemini JSON string to Python dictionary
        parsed_json = json.loads(cleaned_response)

        return jsonify(parsed_json)

    except json.JSONDecodeError as e:

        return jsonify({
            "status": "error",
            "message": f"Gemini returned invalid JSON: {str(e)}",
            "solution": [
                "Try submitting the question again."
            ]
        }), 500

    except Exception as e:

        error_msg = str(e)

        print("ERROR:", error_msg)

        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:

            return jsonify({
                "status": "error",
                "message": "Gemini API rate limit exceeded.",
                "solution": [
                    "Check your Gemini API quota.",
                    "Wait and try again."
                ]
            }), 429

        elif "503" in error_msg or "UNAVAILABLE" in error_msg:

            return jsonify({
                "status": "error",
                "message": "Gemini service is temporarily unavailable.",
                "solution": [
                    "Wait a few seconds.",
                    "Try again."
                ]
            }), 503

        else:

            return jsonify({
                "status": "error",
                "message": "An unexpected error occurred.",
                "solution": [
                    error_msg
                ]
            }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )