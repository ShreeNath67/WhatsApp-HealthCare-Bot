import os
import time
import logging
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from langdetect import detect
import google.generativeai as genai
import backoff

# -------------------------
# Config & Logging
# -------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEN_MODEL = os.getenv("GEN_MODEL", "gemini-1.5-flash")  # safer default for free keys

# Configure Gemini client (will be a no-op if key is missing)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healthbot")

app = Flask(__name__)
user_sessions = {}

# ---------------------------
# Constants (kept from original)
# ---------------------------
GREETING_WORDS = ["hello", "hi", "hey", "namaste", "नमस्ते"]
EXIT_WORDS = ["bye", "no", "thanks", "thank you", "नहीं", "धन्यवाद", "stop", "exit"]
SUPPORTED_LANGS = ["en", "hi", "mr", "bn"]
SESSION_TIMEOUT = 300  # 5 minutes


LANG_PROMPT = (
    "👋 Welcome! कृपया भाषा निवडा | ভাষা নির্বাচন করুন | Please choose your language:\n"
    "[हिंदी | English | मराठी | বাংলা]"
)

LANG_RESPONSES = {
    "hi": "कैसे मदद कर सकता हूँ?",
    "en": "How can I help you today?",
    "mr": "मी तुम्हाला कशी मदत करू शकतो?",
    "bn": "আমি কীভাবে সাহায্য করতে পারি?"
}

# Keep your DISEASE_GUIDE unchanged (copy from original)
DISEASE_GUIDE = {
    "fever": {
        "symptoms": ["fever", "temperature", "chills", "headache"],
        "first_aid": {
            "en": "Rest, drink fluids, take paracetamol.",
            "hi": "आराम करें, पानी पिएं, पैरासिटामोल लें।",
            "mr": "आराम करा, पाणी प्या, पॅरासिटामोल घ्या.",
            "bn": "বিশ্রাম নিন, পানি পান করুন, প্যারাসিটামল নিন।"
        },
        "preventive": {
            "en": "Avoid crowded places, monitor temperature.",
            "hi": "भीड़ से बचें, तापमान जांचें।",
            "mr": "गर्दी टाळा, तापमान तपासा.",
            "bn": "ভিড় এড়িয়ে চলুন, তাপমাত্রা পরীক্ষা করুন।"
        },
        "consult": {
            "en": "Consult doctor if fever lasts >3 days.",
            "hi": "अगर बुखार 3 दिन से ज़्यादा हो तो डॉक्टर से मिलें।",
            "mr": "ताप तीन दिवसांपेक्षा जास्त टिकल्यास डॉक्टरांचा सल्ला घ्या.",
            "bn": "জ্বর ৩ দিনের বেশি হলে ডাক্তার দেখান।"
        }
    },
    "cold": {
        "symptoms": ["cold", "runny nose", "sneezing", "blocked nose"],
        "first_aid": {
            "en": "Rest, steam inhalation, drink warm fluids.",
            "hi": "आराम करें, भाप लें, गर्म तरल पदार्थ पिएं।",
            "mr": "आराम करा, वाफ घ्या, गरम पेये प्या.",
            "bn": "বিশ্রাম নিন, ভাপ নিন, গরম তরল পান করুন।"
        },
        "preventive": {
            "en": "Avoid cold exposure, wash hands regularly.",
            "hi": "ठंड से बचें, हाथ धोते रहें।",
            "mr": "थंडीपासून बचाव करा, हात स्वच्छ ठेवा.",
            "bn": "ঠান্ডা থেকে দূরে থাকুন, নিয়মিত হাত ধুয়ে ফেলুন।"
        },
        "consult": {
            "en": "Consult doctor if symptoms persist >5 days.",
            "hi": "अगर लक्षण 5 दिन से ज़्यादा रहें तो डॉक्टर से मिलें।",
            "mr": "लक्षण ५ दिवसांपेक्षा जास्त टिकल्यास डॉक्टरांचा सल्ला घ्या.",
            "bn": "উপসর্গ ৫ দিনের বেশি থাকলে ডাক্তার দেখান।"
        }
    }
}

# ---------------------------
# Utilities
# ---------------------------
def detect_language(text):
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGS else "en"
    except Exception as e:
        logger.debug("langdetect failed: %s", e)
        return "en"

def generate_maps_link(query="health center near me"):
    return f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

def fallback_message(lang):
    return {
        "hi": "माफ़ कीजिए, अभी जवाब नहीं दे पा रहे हैं। कृपया बाद में प्रयास करें।",
        "mr": "माफ करा, सध्या उत्तर देऊ शकत नाही. कृपया नंतर प्रयत्न करा.",
        "bn": "দুঃখিত, এখন উত্তর দিতে পারছি না। পরে আবার চেষ্টা করুন।",
        "en": "Sorry, I couldn't process that right now. Please try again later."
    }.get(lang, "Sorry, please try again later.")

def match_disease(text):
    normalized = text.lower()
    for disease, info in DISEASE_GUIDE.items():
        for symptom in info["symptoms"]:
            if symptom.lower() in normalized:
                return disease
    return None

def get_user_state(user_id):
    state = user_sessions.get(user_id)
    if state:
        # expire after SESSION_TIMEOUT seconds of inactivity
        if time.time() - state.get("last_seen", 0) <= SESSION_TIMEOUT:
            state["last_seen"] = time.time()
            return state
        else:
            # expired session -> remove and return fresh state
            user_sessions.pop(user_id, None)
            logger.info("Session expired for %s - resetting", user_id)
    # default fresh state
    return {
        "lang": None,
        "step": "greet",
        "mode": "rule_based",
        "msg_count": 0,
        "last_seen": time.time(),
        "disease": None,
        "gemini_since": None
    }

# ---------------------------
# Gemini helper (robust)
# ---------------------------
def build_gemini_prompt(user_text: str, lang: str = "en", health_only: bool = False) -> str:
    """
    Build a controlled prompt for Gemini.
    - health_only: instruct model to refuse non-health questions.
    """
    base = (
        f"You are a helpful rural healthcare assistant. Answer concisely in the user's language ({lang.upper()}).\n"
        "- Provide symptom analysis, first aid, preventive measures, and clear guidance on when to see a doctor.\n"
        "- Use WHO-aligned, conservative health advice.\n"
        "- Keep suggestions safe and encourage seeking medical attention for red flags.\n\n"
        f"User: {user_text}\n"
    )
    if health_only:
        base = (
            "Important: Only reply to health-related queries. If the user asks non-health questions, politely refuse and "
            "ask them to ask a health-related question. Keep the response brief and in the requested language.\n\n"
        ) + base
    return base

# Add simple retry/backoff for transient errors
@backoff.on_exception(backoff.expo, Exception, max_tries=3, factor=1)
def ask_gemini(question: str, lang="en", health_only=False) -> str:
    if not GEMINI_API_KEY:
        logger.error("No GEMINI_API_KEY configured.")
        return fallback_message(lang)

    try:
        prompt = build_gemini_prompt(question, lang=lang, health_only=health_only)
        logger.info("Gemini prompt: %s", prompt[:100] + ("..." if len(prompt) > 100 else ""))
        model = genai.GenerativeModel(GEN_MODEL)
        response = model.generate_content(prompt)
        # Response handling - depending on SDK response shape; try multiple options
        reply = None
        if hasattr(response, "text"):
            reply = response.text
        elif isinstance(response, dict) and "candidates" in response:
            # older/newer SDK shapes
            cands = response.get("candidates")
            if cands and isinstance(cands, list):
                reply = cands[0].get("content", {}).get("text", "")
        else:
            # attempt attribute access for different SDKs
            try:
                reply = getattr(response, "output", None) or getattr(response, "candidates", None)
            except Exception:
                reply = None

        if not reply:
            logger.warning("Gemini returned empty. Falling back.")
            return fallback_message(lang)

        reply_text = (reply.strip() if isinstance(reply, str) else str(reply)).strip()
        logger.info("Gemini response length: %d", len(reply_text))
        return reply_text if reply_text else fallback_message(lang)

    except Exception as e:
        logger.exception("Gemini error: %s", e)
        # re-raise for backoff to catch transient issues, otherwise final fallback
        raise

# ---------------------------
# Conversation logic (refined)
# ---------------------------
def build_conversation_response(user_id, incoming_msg):
    incoming_msg_raw = incoming_msg
    incoming_msg = incoming_msg.strip().lower()
    logger.info("Processing message from %s: %s", user_id, incoming_msg_raw)

    # Load or init session state
    state = get_user_state(user_id)
    # increment message count (user sent a new message)
    state["msg_count"] = state.get("msg_count", 0) + 1
    state["last_seen"] = time.time()
    # write back
    user_sessions[user_id] = state

    # Normalize quick exit
    if any(incoming_msg == w or incoming_msg.startswith(w + " ") for w in EXIT_WORDS):
        user_sessions.pop(user_id, None)
        logger.info("User %s requested exit.", user_id)
        return "Conversation ended. You can say 'Hello' to start again."

    # If session is in gemini mode, route directly to Gemini until user exits or timeout
    if state.get("mode") == "gemini":
        # Use health_only flag depending on requirement; for scenario 3, we set gemini_since flag optionally
        health_only = True  # enforce health-only while in gemini mode
        try:
            gemini_reply = ask_gemini(incoming_msg_raw, lang=state.get("lang", "en"), health_only=health_only)
            # update gemini_since if not set
            if not state.get("gemini_since"):
                state["gemini_since"] = time.time()
            user_sessions[user_id] = state
            return gemini_reply + f"\n\n🗺️ Nearby health centers: {generate_maps_link()}"
        except Exception:
            # final fallback
            return fallback_message(state.get("lang", "en"))

    # Non-gemini (rule-based) flow
    # Greeting handling
    if incoming_msg in GREETING_WORDS or state["step"] == "greet":
        state.update({"lang": None, "step": "choose_lang", "mode": "rule_based", "msg_count": state.get("msg_count", 0)})
        user_sessions[user_id] = state
        return LANG_PROMPT

    # Language selection step
    if state["step"] == "choose_lang":
        # try picking language from the user message explicitly
        chosen = None
        for key in ["हिंदी", "english", "मराठी", "বাংলা", "bengali"]:
            if key in incoming_msg_raw.lower():
                chosen = {"हिंदी": "hi", "english": "en", "मराठी": "mr", "বাংলা": "bn", "bengali": "bn"}[key]
                break
        if not chosen:
            # fallback to detection
            chosen = detect_language(incoming_msg_raw)
        state["lang"] = chosen
        state["step"] = "ask_symptom"
        user_sessions[user_id] = state
        return LANG_RESPONSES.get(chosen, LANG_RESPONSES["en"])

    # Ask symptoms step
    if state["step"] == "ask_symptom":
        state["step"] = "clarify"
        user_sessions[user_id] = state
        return {
            "hi": "कृपया लक्षण स्पष्ट करें।",
            "en": "Could you please specify your symptoms?",
            "mr": "कृपया लक्षण स्पष्ट करा.",
            "bn": "আপনার উপসর্গগুলি নির্দিষ্ট করুন।"
        }.get(state.get("lang", "en"), "Please specify your symptoms.")

    # Clarify step: user provides symptoms or disease
    if state["step"] == "clarify":
        disease = match_disease(incoming_msg_raw)
        state["disease"] = disease
        # If disease matched -> give rule-based answer then hand off to Gemini (per Scenario 2)
        if disease:
            info = DISEASE_GUIDE[disease]
            advice = (
                f"🩺 Based on your symptoms, it may be {disease}.\n\n"
                f"First Aid: {info['first_aid'][state['lang']]}\n"
                f"Preventive Measures: {info['preventive'][state['lang']]}\n"
                f"When to Consult a Doctor: {info['consult'][state['lang']]}"
            )
            # Per your Scenario 2 request: give a little rule-based output then switch to Gemini for deeper follow-ups
            state["mode"] = "gemini"
            state["gemini_since"] = time.time()
            state["step"] = "gemini_active"
            user_sessions[user_id] = state
            follow = {
                "hi": "\n\nक्या आप डॉक्टर से मिलना चाहेंगे?",
                "en": "\n\nWould you like to consult a doctor?",
                "mr": "\n\nतुम्हाला डॉक्टरांचा सल्ला हवा आहे का?",
                "bn": "\n\nআপনি কি একজন ডাক্তারের সাথে পরামর্শ করতে চান?"
            }.get(state["lang"], "\n\nWould you like to consult a doctor?")
            # immediately also include nearby link
            return advice + follow + f"\n\n🗺️ Nearby health centers: {generate_maps_link()}"

        # If disease not matched -> call Gemini and set mode to gemini (Scenario 1)
        try:
            # ask gemini once, then remain in gemini mode
            gemini_reply = ask_gemini(incoming_msg_raw, lang=state.get("lang", "en"), health_only=False)
            state["mode"] = "gemini"
            state["gemini_since"] = time.time()
            state["step"] = "gemini_active"
            user_sessions[user_id] = state
            return gemini_reply + f"\n\n🗺️ {generate_maps_link()}"
        except Exception:
            return fallback_message(state.get("lang", "en"))

    # Default path for any other rule-based steps
    # If message count crosses 10 during the conversation -> switch to Gemini
    if state.get("msg_count", 0) >= 10:
        logger.info("Switching user %s to gemini mode after %d messages", user_id, state["msg_count"])
        state["mode"] = "gemini"
        state["gemini_since"] = time.time()
        user_sessions[user_id] = state
        try:
            gemini_reply = ask_gemini(incoming_msg_raw, lang=state.get("lang", "en"), health_only=True)
            return gemini_reply + f"\n\n🗺️ {generate_maps_link()}"
        except Exception:
            return fallback_message(state.get("lang", "en"))

    # Otherwise fallback to asking Gemini once (but keep rule_based unless explicit handoff)
    try:
        gemini_reply = ask_gemini(incoming_msg_raw, lang=state.get("lang", "en"), health_only=False)
        # don't automatically switch mode here unless reply suggests deeper engagement - we'll prefer explicit transitions
        return gemini_reply + f"\n\n🗺️ {generate_maps_link()}"
    except Exception:
        return fallback_message(state.get("lang", "en"))

# ---------------------------
# Flask routes
# ---------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.form.get("Body", "")
    from_number = request.form.get("From", "")
    logger.info("Incoming WhatsApp message from %s: %s", from_number, incoming_msg)

    reply_text = build_conversation_response(from_number, incoming_msg)

    resp = MessagingResponse()
    msg = resp.message()
    msg.body(reply_text)
    return Response(str(resp), mimetype="application/xml")

@app.route("/", methods=["GET"])
def index():
    return "✅ WhatsApp Healthcare Bot is running."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
