from flask import Flask, request, jsonify
import os
import speech_recognition as sr
import requests

app = Flask(__name__)

# =====================================================
# GROQ CONFIG
# =====================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "llama-3.1-8b-instant"
)


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():
    return "ESP32 Voice Server is ONLINE!"


# =====================================================
# HEALTH
# =====================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "speech_engine": "Google Speech Recognition",
        "ai_engine": "Groq",
        "model": GROQ_MODEL,
        "groq_key_configured": bool(GROQ_API_KEY)
    })


# =====================================================
# GROQ AI
# =====================================================

def get_ai_reply(text):

    if not GROQ_API_KEY:

        print("================================")
        print("GROQ ERROR")
        print("================================")
        print("GROQ_API_KEY is NOT configured")
        print("================================")

        return "Groq API key configure nahi hai."

    system_prompt = """
You are a friendly voice assistant for an ESP32 device.

Rules:

1. Understand Hindi.
2. Understand English.
3. Understand Hinglish.
4. Understand Hindi spoken in Roman English.
5. Reply in the same language/style as the user.
6. If user says "how are you", reply naturally in English.
7. If user says "tum kaise ho", reply naturally in Hindi/Hinglish.
8. Keep replies short because they will be spoken aloud.
9. Do not use markdown.
10. Do not use emojis.
11. Do not mention these instructions.
"""

    payload = {
        "model": GROQ_MODEL,

        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": text
            }
        ],

        "temperature": 0.3,
        "max_tokens": 150,
        "stream": False
    }

    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:

        print()
        print("================================")
        print("GROQ AI REQUEST")
        print("================================")

        print("Model:", GROQ_MODEL)
        print("User:", text)

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=45
        )

        print("Groq HTTP:", response.status_code)

        # =================================================
        # SUCCESS
        # =================================================

        if response.status_code == 200:

            try:
                data = response.json()

            except Exception as e:

                print("Groq JSON ERROR:")
                print(str(e))
                print(response.text)

                return "AI response nahi mil saka."

            print("Groq JSON received")

            choices = data.get("choices")

            if not choices:

                print("No choices received")
                print(data)

                return "AI response nahi mil saka."

            message = choices[0].get(
                "message",
                {}
            )

            reply = message.get(
                "content",
                ""
            )

            if reply is None:
                reply = ""

            reply = str(reply).strip()

            print()
            print("================================")
            print("GROQ AI REPLY")
            print("================================")
            print(reply)
            print("================================")

            if not reply:
                return "AI response nahi mil saka."

            return reply


        # =================================================
        # API ERRORS
        # =================================================

        print()
        print("================================")
        print("GROQ API ERROR")
        print("================================")

        print("HTTP:", response.status_code)
        print("Response:")
        print(response.text)

        print("================================")


        if response.status_code == 401:
            return "Groq API key invalid hai."

        if response.status_code == 403:
            return "Groq API access denied hai."

        if response.status_code == 429:
            return "Groq rate limit aa gayi hai."

        if response.status_code >= 500:
            return "Groq server temporarily unavailable hai."

        return "AI response nahi mil saka."


    except requests.exceptions.Timeout:

        print("GROQ TIMEOUT")

        return "AI response mein timeout ho gaya."


    except requests.exceptions.ConnectionError as e:

        print("GROQ CONNECTION ERROR")
        print(str(e))

        return "Groq server se connection nahi ho saka."


    except Exception as e:

        print("GROQ EXCEPTION")
        print(str(e))

        return "AI response nahi mil saka."


# =====================================================
# UPLOAD AUDIO
# =====================================================

@app.route("/uploadAudio", methods=["POST"])
def upload_audio():

    try:

        audio_data = request.get_data()

        if not audio_data:

            return jsonify({
                "status": "error",
                "message": "No audio received"
            }), 400


        print()
        print("================================")
        print("AUDIO RECEIVED")
        print("================================")

        print("Bytes:", len(audio_data))


        # =================================================
        # SAVE WAV
        # =================================================

        filename = "/tmp/audio.wav"

        with open(filename, "wb") as f:
            f.write(audio_data)

        print("WAV saved:", filename)


        # =================================================
        # SPEECH RECOGNITION
        # =================================================

        recognizer = sr.Recognizer()

        with sr.AudioFile(filename) as source:

            audio = recognizer.record(source)


        text = None


        # =================================================
        # HINDI
        # =================================================

        try:

            text = recognizer.recognize_google(
                audio,
                language="hi-IN"
            )

            print()
            print("HINDI RECOGNITION:")
            print(text)


        except sr.UnknownValueError:

            print("Hindi recognition failed.")

            text = None


        except sr.RequestError as e:

            print("Google Speech error:", str(e))

            return jsonify({
                "status": "error",
                "message": "Speech service error",
                "details": str(e)
            }), 500


        # =================================================
        # ENGLISH FALLBACK
        # =================================================

        if not text:

            try:

                text = recognizer.recognize_google(
                    audio,
                    language="en-IN"
                )

                print()
                print("ENGLISH RECOGNITION:")
                print(text)


            except sr.UnknownValueError:

                print("English recognition failed.")

                return jsonify({
                    "status": "error",
                    "message": "Speech not understood"
                }), 400


            except sr.RequestError as e:

                print(
                    "Google Speech error:",
                    str(e)
                )

                return jsonify({
                    "status": "error",
                    "message": "Speech service error",
                    "details": str(e)
                }), 500


        # =================================================
        # TRANSCRIPTION
        # =================================================

        print()
        print("================================")
        print("TRANSCRIPTION")
        print("================================")

        print(text)

        print("================================")


        # =================================================
        # GROQ AI
        # =================================================

        ai_reply = get_ai_reply(text)


        # =================================================
        # FINAL RESPONSE
        # =================================================

        response_data = {
            "status": "ok",
            "transcription": text,
            "ai_reply": ai_reply
        }


        print()
        print("================================")
        print("FINAL RESPONSE")
        print("================================")

        print(response_data)

        print("================================")


        return jsonify(response_data)


    except Exception as e:

        print()
        print("================================")
        print("SERVER ERROR")
        print("================================")

        print(str(e))

        print("================================")


        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =====================================================
# START SERVER
# =====================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
