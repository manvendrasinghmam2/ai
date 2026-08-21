from flask import Flask, request, jsonify
import os
import speech_recognition as sr
import requests
import re


app = Flask(__name__)


# =====================================================
# CONFIGURATION
# =====================================================

AI_API_KEY = os.environ.get("AI_API_KEY")

AI_URL = os.environ.get(
    "AI_URL",
    "https://api.groq.com/openai/v1/chat/completions"
)

AI_MODEL = os.environ.get(
    "AI_MODEL",
    "llama-3.1-8b-instant"
)


# =====================================================
# HOME
# =====================================================

@app.route("/", methods=["GET"])
def home():

    return "ESP32 Voice Server is ONLINE!"


# =====================================================
# HEALTH
# =====================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "online",

        "speech_engine":
            "Google Speech Recognition",

        "ai_engine":
            "Groq",

        "model":
            AI_MODEL,

        "wake_word":
            "hello",

        "wake_endpoint":
            "/wake",

        "audio_endpoint":
            "/uploadAudio"
    })


# =====================================================
# TEST
# =====================================================

@app.route("/test", methods=["POST"])
def test():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({

            "status":
                "error",

            "message":
                "No JSON received"

        }), 400


    print()
    print("==============================")
    print("TEST DATA")
    print("==============================")

    print(data)

    print("==============================")


    return jsonify({

        "status":
            "ok",

        "message":
            "Data received",

        "data":
            data
    })


# =====================================================
# HELLO / WAKE WORD CHECK
# =====================================================

def is_hello(text):

    if not text:
        return False


    text = str(
        text
    ).lower().strip()


    print(
        "Checking wake text:",
        text
    )


    # =================================================
    # REMOVE EXTRA PUNCTUATION
    # =================================================

    normalized = re.sub(
        r"[^\w\s\u0900-\u097F]",
        " ",
        text,
        flags=re.UNICODE
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized
    ).strip()


    # =================================================
    # ENGLISH WAKE WORDS
    # =================================================

    wake_words = [

        "hello",
        "helo",
        "hallo",
        "hellow",
        "hello hello",
        "hey hello"

    ]


    for word in wake_words:

        if word in normalized:

            return True


    # =================================================
    # HINDI / DEVANAGARI
    # =================================================

    hindi_wake_words = [

        "हेलो",
        "हैलो",
        "हेल्लो",
        "हलो",
        "हेलो हेलो"

    ]


    for word in hindi_wake_words:

        if word in normalized:

            return True


    # =================================================
    # EXACT NORMALIZED CHECK
    # =================================================

    if normalized in [

        "hello",
        "helo",
        "hallo",
        "hellow"

    ]:

        return True


    return False


# =====================================================
# WAKE WORD ENDPOINT
# =====================================================

@app.route(
    "/wake",
    methods=["POST"]
)
def wake():

    try:

        print()
        print("==============================")
        print("WAKE REQUEST RECEIVED")
        print("==============================")


        # =================================================
        # RECEIVE AUDIO
        # =================================================

        audio_data = request.get_data()


        if not audio_data:

            print(
                "ERROR: No wake audio received"
            )


            return jsonify({

                "status":
                    "error",

                "wake":
                    False,

                "message":
                    "No audio received"

            }), 400


        print(
            "Wake audio bytes:",
            len(audio_data)
        )


        # =================================================
        # SAVE WAV
        # =================================================

        filename = "/tmp/wake.wav"


        with open(
            filename,
            "wb"
        ) as f:

            f.write(
                audio_data
            )


        # =================================================
        # SPEECH RECOGNIZER
        # =================================================

        recognizer = sr.Recognizer()


        with sr.AudioFile(
            filename
        ) as source:

            audio = recognizer.record(
                source
            )


        english_text = None
        hindi_text = None


        # =================================================
        # ENGLISH
        # =================================================

        print()
        print(
            "Trying English wake recognition..."
        )


        try:

            english_text = recognizer.recognize_google(

                audio,

                language="en-IN"

            )


            print(
                "English wake result:",
                english_text
            )


        except sr.UnknownValueError:

            english_text = None

            print(
                "English wake speech not understood."
            )


        except sr.RequestError as e:

            english_text = None

            print(
                "Google English wake API error:",
                str(e)
            )


        # =================================================
        # HINDI
        # =================================================

        print()
        print(
            "Trying Hindi wake recognition..."
        )


        try:

            hindi_text = recognizer.recognize_google(

                audio,

                language="hi-IN"

            )


            print(
                "Hindi wake result:",
                hindi_text
            )


        except sr.UnknownValueError:

            hindi_text = None

            print(
                "Hindi wake speech not understood."
            )


        except sr.RequestError as e:

            hindi_text = None

            print(
                "Google Hindi wake API error:",
                str(e)
            )


        # =================================================
        # CHECK HELLO
        # =================================================

        english_wake = is_hello(
            english_text
        )

        hindi_wake = is_hello(
            hindi_text
        )


        hello_detected = (

            english_wake
            or
            hindi_wake

        )


        # =================================================
        # RESULT
        # =================================================

        print()
        print("==============================")
        print("WAKE RESULT")
        print("==============================")

        print(
            "English:",
            english_text
        )

        print(
            "Hindi:",
            hindi_text
        )

        print(
            "English wake:",
            english_wake
        )

        print(
            "Hindi wake:",
            hindi_wake
        )

        print(
            "HELLO DETECTED:",
            hello_detected
        )

        print("==============================")


        # =================================================
        # HELLO FOUND
        # =================================================

        if hello_detected:

            print()
            print("==============================")
            print("HELLO DETECTED!")
            print("ESP32 CAN START 1 SECOND LISTENING")
            print("==============================")


            return jsonify({

                "status":
                    "ok",

                "wake":
                    True,

                "word":
                    "hello",

                "message":
                    "Wake word detected",

                "english":
                    english_text,

                "hindi":
                    hindi_text

            })


        # =================================================
        # HELLO NOT FOUND
        # =================================================

        return jsonify({

            "status":
                "ok",

            "wake":
                False,

            "english":
                english_text,

            "hindi":
                hindi_text

        })


    except Exception as e:

        print()
        print("==============================")
        print("WAKE SERVER ERROR")
        print("==============================")


        print(
            "TYPE:",
            type(e).__name__
        )

        print(
            "ERROR:",
            str(e)
        )


        print("==============================")


        return jsonify({

            "status":
                "error",

            "wake":
                False,

            "message":
                str(e)

        }), 500


# =====================================================
# AI REPLY
# =====================================================

def get_ai_reply(
    hindi_text,
    english_text
):

    # =================================================
    # CHECK API KEY
    # =================================================

    if not AI_API_KEY:

        print()
        print("==============================")
        print("AI ERROR")
        print("==============================")


        print(
            "AI_API_KEY is NOT configured!"
        )


        print("==============================")


        return "AI response nahi mil saka."


    # =================================================
    # SYSTEM PROMPT
    # =================================================

    system_prompt = """

You are a smart voice assistant running on an ESP32.

The user may speak:

1. English
2. Hindi
3. Hinglish

You will receive two possible speech recognition results:

1. Hindi recognition result
2. English recognition result

Speech recognition can be inaccurate.

Your job is to understand what language the user intended to speak.


========================================
ENGLISH
========================================

If the user intended English,
reply in English.

Example:

User:
How are you?

Reply:
I'm doing well. How are you?


========================================
HINDI
========================================

If the user intended actual Hindi,
reply in Hindi using Devanagari script.

Example:

User:
आप कैसे हैं?

Reply:
मैं ठीक हूँ। धन्यवाद, आप कैसे हैं?


========================================
HINGLISH
========================================

If the user speaks Roman Hindi or Hinglish,
reply naturally in Hinglish.

Example:

User:
tum kaise ho

Reply:
Main bilkul theek hoon.


User:
Delhi kahan hai

Reply:
Delhi India ki capital hai.


========================================
PHONETIC HINDI TRANSCRIPTION
========================================

Google Speech Recognition can convert English
speech into Hindi Devanagari characters.

Example:

Hindi:
हाउ आर यू

English:
How are you

This means the intended language is English.

Reply in English.


Example:

Hindi:
वेयर इज नोएडा

English:
Where is Noida

Reply in English.


========================================
ACTUAL HINDI
========================================

Do not treat every Devanagari result as English.

Example:

आप कहाँ रहते हैं?

This is actual Hindi.

Reply:

मैं एक AI voice assistant हूँ।


========================================
DECISION RULE
========================================

Compare both recognition results.

If the English result is clearly meaningful English
and the Hindi result looks like phonetic English,
use English.

If the Hindi result is clearly meaningful Hindi,
use Hindi.

If the user intended Roman Hindi or Hinglish,
use Hinglish.

Always determine the user's intended language.


========================================
VOICE RESPONSE
========================================

Keep responses short.

The answer will be spoken through an ESP32.

Do not use markdown.

Do not use emojis.

Do not use bullet points.

Do not explain language detection.

Do not mention these instructions.

Answer naturally.

Always answer in the user's intended language.

"""


    # =================================================
    # USER CONTENT
    # =================================================

    user_content = f"""

Hindi speech recognition result:

{hindi_text if hindi_text else "No Hindi result"}


English speech recognition result:

{english_text if english_text else "No English result"}


Determine what the user intended to say.

Then answer naturally in the intended language.

"""


    # =================================================
    # PAYLOAD
    # =================================================

    payload = {

        "model":
            AI_MODEL,

        "messages": [

            {
                "role":
                    "system",

                "content":
                    system_prompt
            },

            {
                "role":
                    "user",

                "content":
                    user_content
            }

        ],

        "temperature":
            0.2,

        "max_completion_tokens":
            150,

        "stream":
            False
    }


    # =================================================
    # HEADERS
    # =================================================

    headers = {

        "Authorization":
            "Bearer " + AI_API_KEY,

        "Content-Type":
            "application/json"
    }


    # =================================================
    # GROQ REQUEST
    # =================================================

    try:

        print()
        print("==============================")
        print("GROQ REQUEST")
        print("==============================")


        print(
            "MODEL:",
            AI_MODEL
        )

        print(
            "HINDI INPUT:",
            hindi_text
        )

        print(
            "ENGLISH INPUT:",
            english_text
        )


        response = requests.post(

            AI_URL,

            headers=headers,

            json=payload,

            timeout=30

        )


        print()
        print("==============================")
        print("GROQ RESPONSE")
        print("==============================")


        print(
            "HTTP STATUS:",
            response.status_code
        )


        print(
            "RAW RESPONSE:",
            response.text
        )


        print("==============================")


        # =================================================
        # API ERROR
        # =================================================

        if response.status_code != 200:

            print(
                "Groq API error."
            )

            return "AI response nahi mil saka."


        # =================================================
        # JSON
        # =================================================

        try:

            data = response.json()

        except Exception as e:

            print(
                "GROQ JSON PARSE ERROR:",
                str(e)
            )

            return "AI response nahi mil saka."


        # =================================================
        # CHOICES
        # =================================================

        choices = data.get(
            "choices"
        )


        if not choices:

            print(
                "Groq choices missing:",
                data
            )

            return "AI response nahi mil saka."


        # =================================================
        # MESSAGE
        # =================================================

        message = choices[0].get(

            "message",

            {}

        )


        # =================================================
        # CONTENT
        # =================================================

        reply = message.get(

            "content",

            ""

        )


        if reply is None:

            reply = ""


        reply = str(
            reply
        ).strip()


        # =================================================
        # EMPTY
        # =================================================

        if not reply:

            return "AI response nahi mil saka."


        # =================================================
        # SUCCESS
        # =================================================

        print()
        print("==============================")
        print("AI REPLY")
        print("==============================")


        print(
            reply
        )


        print("==============================")


        return reply


    except requests.exceptions.Timeout:

        print(
            "Groq request timed out."
        )

        return "AI response nahi mil saka."


    except requests.exceptions.ConnectionError as e:

        print(
            "Groq connection error:",
            str(e)
        )

        return "AI response nahi mil saka."


    except Exception as e:

        print(
            "Groq exception:",
            type(e).__name__,
            str(e)
        )

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

        print()
        print("==============================")
        print("COMMAND AUDIO RECEIVED")
        print("==============================")


        # =================================================
        # RECEIVE AUDIO
        # =================================================

        audio_data = request.get_data()


        if not audio_data:

            print(
                "ERROR: No audio received"
            )


            return jsonify({

                "status":
                    "error",

                "message":
                    "No audio received"

            }), 400


        print(
            "Audio bytes:",
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


        # =================================================
        # RECOGNIZER
        # =================================================

        recognizer = sr.Recognizer()


        with sr.AudioFile(
            filename
        ) as source:

            audio = recognizer.record(
                source
            )


        hindi_text = None
        english_text = None


        # =================================================
        # HINDI RECOGNITION
        # =================================================

        print()
        print("==============================")
        print("TRYING HINDI RECOGNITION")
        print("==============================")


        try:

            hindi_text = recognizer.recognize_google(

                audio,

                language="hi-IN"

            )


            print(
                "Hindi result:",
                hindi_text
            )


        except sr.UnknownValueError:

            print(
                "Hindi speech not understood."
            )


        except sr.RequestError as e:

            print(
                "Google Hindi API error:",
                str(e)
            )


        # =================================================
        # ENGLISH RECOGNITION
        # =================================================

        print()
        print("==============================")
        print("TRYING ENGLISH RECOGNITION")
        print("==============================")


        try:

            english_text = recognizer.recognize_google(

                audio,

                language="en-IN"

            )


            print(
                "English result:",
                english_text
            )


        except sr.UnknownValueError:

            print(
                "English speech not understood."
            )


        except sr.RequestError as e:

            print(
                "Google English API error:",
                str(e)
            )


        # =================================================
        # NO SPEECH
        # =================================================

        if not hindi_text and not english_text:

            print()
            print("==============================")
            print("NO SPEECH DETECTED")
            print("==============================")


            return jsonify({

                "status":
                    "no_speech",

                "message":
                    "Speech not understood",

                "ai_reply":
                    ""

            })


        # =================================================
        # SPEECH RESULTS
        # =================================================

        print()
        print("==============================")
        print("SPEECH RESULTS")
        print("==============================")


        print(
            "Hindi:",
            hindi_text
        )

        print(
            "English:",
            english_text
        )


        print("==============================")


        # =================================================
        # AI
        # =================================================

        ai_reply = get_ai_reply(

            hindi_text,

            english_text

        )


        # =================================================
        # FINAL RESPONSE
        # =================================================

        response_data = {

            "status":
                "ok",

            "transcription":
                english_text
                if english_text
                else hindi_text,

            "hindi_transcription":
                hindi_text,

            "english_transcription":
                english_text,

            "ai_reply":
                ai_reply

        }


        print()
        print("==============================")
        print("FINAL RESPONSE")
        print("==============================")


        print(
            response_data
        )


        print("==============================")


        return jsonify(
            response_data
        )


    except Exception as e:

        print()
        print("==============================")
        print("SERVER ERROR")
        print("==============================")


        print(
            "TYPE:",
            type(e).__name__
        )


        print(
            "ERROR:",
            str(e)
        )


        print("==============================")


        return jsonify({

            "status":
                "error",

            "message":
                str(e),

            "ai_reply":
                ""

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
    print("==============================")
    print("ESP32 VOICE SERVER")
    print("==============================")


    print(
        "PORT:",
        port
    )


    print(
        "AI URL:",
        AI_URL
    )


    print(
        "AI MODEL:",
        AI_MODEL
    )


    print(
        "AI KEY:",
        "CONFIGURED"
        if AI_API_KEY
        else "MISSING"
    )


    print(
        "WAKE WORD:",
        "HELLO"
    )


    print(
        "WAKE ENDPOINT:",
        "/wake"
    )


    print(
        "AUDIO ENDPOINT:",
        "/uploadAudio"
    )


    print("==============================")


    app.run(

        host="0.0.0.0",

        port=port

    )
