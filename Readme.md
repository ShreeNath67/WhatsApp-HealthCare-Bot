🩺 WhatsApp Healthcare Bot
A conversational AI bot for rural healthcare triage using WhatsApp, Gemini, and Google Maps.

✅ Features
- Symptom-based triage (fever, malaria, dengue, etc.)
- WHO-style first aid and preventive advice
- Gemini fallback for open-ended queries
- Language selection + auto-detection (English/Hindi)
- Doctor referral via Google Maps

Sure, Shree — here’s a clean, concise README.md with all essentials:

🩺 WhatsApp Healthcare Bot
A conversational AI bot for rural healthcare triage using WhatsApp, Gemini, and Google Maps.

✅ Features
- Symptom-based triage (fever, malaria, dengue, etc.)
- WHO-style first aid and preventive advice
- Gemini fallback for open-ended queries
- Language selection + auto-detection (English/Hindi)
- Doctor referral via Google Maps

🛠 Tools Used
- Flask – Web server for Twilio webhook
- Twilio – WhatsApp messaging API (Twilio Sandbox)
- Ngrok – Exposes local server (Ngrok Dashboard)
- Gemini API – Handles fallback queries (Google AI Studio)
- Langdetect – Detects user language
- Google Maps API – Provides nearby health center links

📦 Setup
1. Clone repo and install dependencies:
-
pip install -r requirements.txt
-

2. Create .env file:
-
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=whatsapp:+14155238886
FLASK_ENV=development
FLASK_DEBUG=1
GEMINI_API_KEY=your_gemini_key
GOOGLE_API_KEY=your_maps_key
-

3. Run bot:
-
python app.py
-

4. Setup ngrok:
-
Go to ngrok and create an account and then you will find access tokken there.
Copy that tokken and paste on next cmd.
-

5. Start ngrok:
-
ngrok http 5000
-

6. Setup Twilio:
-
Create an account on Twilio and choose whatsapp.
Connect your whatsapp with Twilio by scanning QR code and Code will be given for initilization. Send that and It will be connected.
You will find SID and Auth_Tokken at right side. Copy and paste to your .env file.
-

6. Paste ngrok URL into Twilio Sandbox:
-
https://your-ngrok-url.ngrok-free.dev/whatsapp
-

📱 How to Use
Send “Hello” to:
-
+1 415 523 8886
-

Test Symptoms:
| Symptom         | Mapped Disease | Notes                                 |
|-----------------|----------------|----------------------------------------|
| fever           | Fever          | Core symptom, triggers fever flow      |
| temperature     | Fever          | Alternate phrasing for fever           |
| chills          | Fever          | Often co-occurs with fever             |
| headache        | Fever          | Shared across multiple conditions      |
| cold            | Cold           | Primary trigger for cold flow          |
| runny nose      | Cold           | Common cold symptom                    |
| sneezing        | Cold           | May overlap with allergies             |
| blocked nose    | Cold           | Useful for nasal congestion detection  |

---


For further assistance watch demo video.
