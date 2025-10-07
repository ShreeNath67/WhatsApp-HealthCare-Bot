# 🩺 WhatsApp HealthCare Bot

A conversational AI bot for **rural healthcare triage** using **WhatsApp**, **Gemini AI**, and **Google Maps**.

---

## ✅ Features

- 🤒 Symptom-based triage (fever, malaria, dengue, etc.)
- 🩹 WHO-style first aid and preventive advice
- 🧠 Gemini fallback for open-ended queries
- 🗣 Language selection + auto-detection (English/Hindi)
- 🏥 Doctor referral via Google Maps

---

## 🛠 Tools Used
| Tool              | Purpose                                      |
|-------------------|----------------------------------------------|
| Flask             | Web server for Twilio webhook                |
| Twilio            | WhatsApp messaging API (Twilio Sandbox)      |
| Ngrok             | Exposes local Flask server to the web        |
| Gemini API        | Handles fallback queries using Google AI     |
| Langdetect        | Detects and switches between English/Hindi   |
| Google Maps API   | Finds nearby hospitals or clinics            |

---

## ⚙️ Setup Guide (Step-by-Step)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/ShreeNath67/WhatsApp-HealthCare-Bot.git
cd whatsapp-healthcare-bot
pip install -r requirements.txt
```

### 2️⃣ Create `.env` File

⚠️ These Twilio credentials are for **testing only** (hackathon use). Replace with your own later.
Copy paste in '.env' file

```env
TWILIO_ACCOUNT_SID=AC32221d007c565448f669a5e880323083
TWILIO_AUTH_TOKEN=8953bd25c3aa7e7f6c9a0e1ffc9f0d4c
TWILIO_PHONE_NUMBER=whatsapp:+14155238886
FLASK_ENV=development
FLASK_DEBUG=1
GEMINI_API_KEY=your_gemini_key
GOOGLE_API_KEY=your_maps_key
```

### 3️⃣ Run Flask App

```bash
python app.py
```
### 4️⃣ Setup Ngrok

- Create an account at [Ngrok Dashboard](https://dashboard.ngrok.com)
- Add your auth token (for demo use only):

```bash
ngrok config add-authtoken 33eOuODzwGUSyDi2bEgjVorSSAF_4vsMmGbsggGSMz4XAbLQv
```

- Start Ngrok:

```bash
ngrok http 5000
```

- Use this live webhook URL for Twilio:
  ```
  https://unimperious-occultly-leopoldo.ngrok-free.dev/whatsapp
  ```

### 5️⃣ Setup Twilio (WhatsApp Sandbox)

- Create account at [Twilio](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn)
- Verify email and phone
- Go to Messaging → Try WhatsApp
- Scan QR code or send join code to sandbox number: `+1 415 523 8886`
- Copy your SID and Auth Token → paste into `.env`
- In Sandbox settings, paste your Ngrok URL under “When a message comes in”

---

## 📱 How to Use

Send “Hello” to: `+1 415 523 8886`

Then type symptoms like:

- `fever`
- `cold`
- `chills`
- `headache`

---
## 🧩 Test Symptoms

| Symptom      | Mapped Disease | Notes                                 |
|--------------|----------------|----------------------------------------|
| fever        | Fever          | Core symptom, triggers fever flow      |
| temperature  | Fever          | Alternate phrasing                     |
| chills       | Fever          | Often co-occurs with fever             |
| headache     | Fever          | Shared across multiple conditions      |
| cold         | Cold           | Primary trigger for cold flow          |
| runny nose   | Cold           | Common cold symptom                    |
| sneezing     | Cold           | May overlap with allergies             |
| blocked nose | Cold           | Useful for nasal congestion detection  |

---

## 🎥 Demo Video
Watch setup video here:                                                                                                                                         
🔗 [Click to view](https://drive.google.com/file/d/1vAAllk2w4cUid7SxVx_0TnMJRyPKvXRQ/view?usp=drive_link)

Watch the working demo here:  
🔗 [Click to view](https://drive.google.com/file/d/1XUYwrJtPmhQDhbMkIyiAbYQXdQev-lXk/view?usp=drive_link)

---

## 📎 Notes

- These credentials are for **temporary testing** only.
- Replace with your own Twilio and Ngrok accounts for production.
- Keep `.env` private — add it to `.gitignore`.

---

## 💡 Future Enhancements

- Multilingual support (Marathi, Tamil, etc.)
- Hospital booking API integration
- Voice-based interaction system
- Streamlit or Flutter-based frontend

---

## 👨‍💻 Author

**Shree Nath**
AI & Healthcare Innovator  
📧 Contact: shreenath064@gmail.com

##Team Members
**Arjun Chaudhary**
**Aditya Singh Baghel**
**Suraj Kumar**




