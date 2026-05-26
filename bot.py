import requests

# ====================== AYARLAR ======================
BOT_TOKEN = "7869982853:AAGkI5v1o028LUaI4q-KCcqcotoH9nFsDyA"      # BotFather'dan aldığın token
CHAT_ID = "8216576697"          # Kendi chat id'n

MESSAGE = "✅ Bot Active - Working Normally"

# ====================== MESAJ GÖNDERME ======================

def send_active_message():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": MESSAGE,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Bot Active mesajı başarıyla gönderildi.")
        else:
            print(f"❌ Mesaj gönderilemedi. Hata kodu: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")


# ====================== ANA KISIM ======================

if __name__ == "__main__":
    print("Bot başlatılıyor...")
    send_active_message()
    print("Mesaj gönderildi. Program kapatılıyor...")
    
    # Program burada doğal olarak durur
