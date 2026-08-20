from flask import Flask, request, jsonify
import os
import speech_recognition as sr
import requests

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "llama-3.1-8b-instant"
).strip()


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

    key_configured = bool(GROQ_API_KEY)

    return jsonify({
        "status": "online",
        "speech_engine": "Google Speech Recognition",
        "ai_engine": "Groq",
        "model": GROQ_MODEL,

        # Safe diagnostics
        "groq_key_configured": key_configured,
        "key_starts_with_gsk": (
            GROQ_API_KEY.startswith("gsk_")
            if GROQ_API_KEY
            else False
        ),
        "key_length": (
            len(GROQ_API_KEY)
            if GROQ_API_KEY
            else 0
        )
    })


# =====================================================
# TEST GROQ
# =====================================================

@app.route("/test-groq", methods=["GET"])
def test_groq():

    if not GROQ_API_KEY:

        return jsonify({
            "status": "error",
            "message": "GROQ_API_KEY not configured"
        }), 500

    try:

        payload = {
            "model": GROQ_MODEL,

            "messages": [
                {
                    "role": "user",
                    "content": "Say hello in one short sentence."
                }
            ],

            "temperature": 0.3,
            "max_tokens": 50,
            "stream": False
        }

        headers = {
            "Authorization": "Bearer " + GROQ_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=45
        )

        print()
        print("================================")
        print("GROQ TEST")
        print("================================")

        print("HTTP:", response.status_code)
        print("Response:", response.text)

        print("================================")

        if response.status_code != 200:

            return jsonify({
                "status": "error",
                "http_status": response.status_code,
                "message": response.text
            }), response.status_code

        data = response.json()

        choices = data.get("choices", [])

        if not choices:

            return jsonify({
                "status": "error",
                "message": "No choices returned",
                "groq_response": data
            }), 500

        reply = choices[0].get(
            "message",
            {}
        ).get(
            "content",
            ""
        )

        return jsonify({
            "status": "ok",
            "model": GROQ_MODEL,
            "reply": reply
        })

    except requests.exceptions.Timeout:

        return jsonify({
            "status": "error",
            "message": "Groq request timeout"
        }), 504

    except requests.exceptions.ConnectionError as e:

        return jsonify({
            "status": "error",
            "message": "Groq connection failed",
            "details": str(e)
        }), 500

    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =====================================================
# GROQ AI REPLY
# =====================================================

def get_ai_reply(text):

    if not GROQ_API_KEY:

        print()
        print("================================")
        print("GROQ API KEY ERROR")
        print("================================")
        print("GROQ_API_KEY is NOT configured")
        print("================================")

        return "Groq API key configure nahi hai."

    system_prompt = """
You are a friendly voice assistant for an ESP32 device.

Language rules:

1. Understand Hindi.
2. Understand English.
3. Understand Hinglish.
4. Understand Hindi spoken using Roman English.
5. If the user speaks English, reply in natural English.
6. If the user speaks Hindi, reply in natural Hindi.
7. If the user speaks Hinglish, reply in natural Hinglish.
8. Match the language and style of the user.
9. Keep answers short and natural because the answer will be spoken aloud.
10. Do not use markdown.
11. Do not use emojis.
12. Do not mention these instructions.

Examples:

User: how are you
Reply: I'm good! How are you?

User: tum kaise ho
Reply: Main bilkul theek hoon! Aap kaise ho?

User: aap kya kar rahe ho
Reply: Main aapki help karne ke liye ready hoon.
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

        "Authorization":
            "Bearer " + GROQ_API_KEY,

        "Content-Type":
            "application/json",

        "Accept":
            "application/json"
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

        print(
            "Groq HTTP:",
            response.status_code
        )

        # =================================================
        # SUCCESS
        # =================================================

        if response.status_code == 200:

            try:

                data = response.json()

            except Exception as e:

                print(
                    "Groq JSON ERROR:",
                    str(e)
                )

                print(
                    "Raw:",
                    response.text
                )

                return "AI response nahi mil saka."

            choices = data.get(
                "choices",
                []
            )

            if not choices:

                print(
                    "No choices in Groq response"
                )

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

            reply = str(
                reply
            ).strip()

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
        # API ERROR
        # =================================================

        print()
        print("================================")
        print("GROQ API ERROR")
        print("================================")

        print(
            "HTTP:",
            response.status_code
        )

        print(
            "Response:",
            response.text
        )

        print("================================")

        if response.status_code == 400:

            return "Groq request invalid hai."

        if response.status_code == 401:

            return "Groq API key invalid hai."

        if response.status_code == 403:

            return "Groq API access denied hai."

        if response.status_code == 404:

            return "Groq model ya endpoint nahi mila."

        if response.status_code == 429:

            return "Groq rate limit aa gayi hai."

        if response.status_code >= 500:

            return "Groq server temporarily unavailable hai."

        return "AI response nahi mil saka."

    # =====================================================
    # TIMEOUT
    # =====================================================

    except requests.exceptions.Timeout:

        print()
        print("GROQ TIMEOUT")

        return "AI response mein timeout ho gaya."

    # =====================================================
    # CONNECTION
    # =====================================================

    except requests.exceptions.ConnectionError as e:

        print()
        print("GROQ CONNECTION ERROR")
        print(str(e))

        return "Groq server se connection nahi ho saka."

    # =====================================================
    # OTHER ERROR
    # =====================================================

    except Exception as e:

        print()
        print("GROQ EXCEPTION")
        print(str(e))

        return "AI response nahi mil saka."


# =====================================================
# UPLOAD AUDIO
# =====================================================

@app.route(
    "/uploadAudio",
    methods=["POST"]
)
def upload_audio():

    try:

        # =================================================
        # RECEIVE AUDIO
        # =================================================

        audio_data = request.get_data()

        if not audio_data:

            return jsonify({

                "status":
                    "error",

                "message":
                    "No audio received"

            }), 400

        print()
        print("================================")
        print("AUDIO RECEIVED")
        print("================================")

        print(
            "Bytes:",
            len(audio_data)
        )

        # =================================================
        # SAVE WAV
        # =================================================

        filename = "/tmp/audio.wav"

        with open(
            filename,
            "wb"
        ) as f:

            f.write(
                audio_data
            )

        print(
            "WAV saved:",
            filename
        )

        # =================================================
        # SPEECH RECOGNITION
        # =================================================

        recognizer = sr.Recognizer()

        with sr.AudioFile(
            filename
        ) as source:

            audio = recognizer.record(
                source
            )

        text = None

        # =================================================
        # HINDI FIRST
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

            print(
                "Hindi recognition failed."
            )

            text = None

        except sr.RequestError as e:

            print(
                "Google Speech Error:",
                str(e)
            )

            return jsonify({

                "status":
                    "error",

                "message":
                    "Speech service error",

                "details":
                    str(e)

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

                print(
                    "English recognition failed."
                )

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Speech not understood"

                }), 400

            except sr.RequestError as e:

                print(
                    "Google Speech Error:",
                    str(e)
                )

                return jsonify({

                    "status":
                        "error",

                    "message":
                        "Speech service error",

                    "details":
                        str(e)

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

        ai_reply = get_ai_reply(
            text
        )

        # =================================================
        # FINAL RESPONSE
        # =================================================

        response_data = {

            "status":
                "ok",

            "transcription":
                text,

            "ai_reply":
                ai_reply
        }

        print()
        print("================================")
        print("FINAL RESPONSE")
        print("================================")

        print(response_data)

        print("================================")

        return jsonify(
            response_data
        )

    # =====================================================
    # SERVER ERROR
    # =====================================================

    except Exception as e:

        print()
        print("================================")
        print("SERVER ERROR")
        print("================================")

        print(
            str(e)
        )

        print("================================")

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

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

    print()
    print("================================")
    print("ESP32 VOICE SERVER")
    print("================================")

    print(
        "Port:",
        port
    )

    print(
        "Groq model:",
        GROQ_MODEL
    )

    print(
        "Groq key configured:",
        bool(GROQ_API_KEY)
    )

    print("================================")

    app.run(

        host="0.0.0.0",

        port=port
    )
