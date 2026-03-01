import asyncio
import random
import json
from telethon import TelegramClient, events
from collections import defaultdict

# BOT AYARLARI - SENİN BİLGİLERİN
BOT_TOKEN = "8667363324:AAFGuNiGCx40dWV159iDChvdn-4ixdKf7uE"
API_ID = 30424455
API_HASH = "af3a166038b2ba69e99aca86e614abe6"

# Bot istemcisi
client = TelegramClient("DirokzanBot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Aktif gruplar
aktif_gruplar = []

# Son sorulan soruları takip et (her grup için)
son_sorular = {}

# Kullanıcı puanları (grup bazında)
kullanici_puanlari = defaultdict(lambda: defaultdict(int))

def load_questions():
    """3.json dosyasından soruları yükle"""
    try:
        with open('3.json', 'r', encoding='utf-8') as file:
            sorular = json.load(file)
            
        # Her soruya bir ID ve doğru cevap indeksi ekle
        for i, soru in enumerate(sorular):
            soru['id'] = i
            harf_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
            soru['correct_index'] = harf_to_index.get(soru.get('correct', 'A'), 0)
        
        return sorular
    except Exception as e:
        print(f"❌ Sorular yüklenemedi: {e}")
        return []

# Soruları yükle
TUM_SORULAR = load_questions()
print(f"✅ Toplam {len(TUM_SORULAR)} tarih sorusu yüklendi")

async def send_quiz_question(chat_id):
    """Belirtilen gruba rastgele bir soru gönder"""
    
    if not TUM_SORULAR:
        return
    
    soru = random.choice(TUM_SORULAR)
    
    # Bu gruba son sorulan soruyu kaydet
    son_sorular[chat_id] = {
        'soru_id': soru['id'],
        'correct_index': soru['correct_index'],
        'cevaplayanlar': [],
        'dogru_sayan': 0
    }
    
    question = soru.get("question")
    answers = soru.get("answers", [])
    
    if not question or len(answers) < 2:
        return
    
    try:
        # Soru metnini oluştur
        message = f"📜 **TARİH SORUSU** 📜\n\n"
        message += f"❓ {question}\n\n"
        
        # Şıkları harflendir
        harfler = ['A', 'B', 'C', 'D']
        for i, answer in enumerate(answers):
            if i < len(harfler):
                message += f"{harfler[i]}) {answer}\n"
        
        message += "\n⏳ Cevabınızı **A, B, C veya D** yazın! (30 saniye)"
        
        await client.send_message(chat_id, message)
        print(f"✅ Soru gönderildi: {chat_id}")
        
        # 30 saniye sonra cevap süresini bitir
        async def cevap_suresi_bitir():
            await asyncio.sleep(30)
            if chat_id in son_sorular:
                dogru_cevap = answers[soru['correct_index']]
                dogru_harf = harfler[soru['correct_index']]
                dogru_sayan = son_sorular[chat_id].get('dogru_sayan', 0)
                
                mesaj = f"⏰ **Süre bitti!**\n\n✅ Doğru cevap: **{dogru_harf}) {dogru_cevap}**\n📊 {dogru_sayan} kişi doğru bildi."
                await client.send_message(chat_id, mesaj)
                
                # Puan durumunu göster
                await show_scores(chat_id)
                
                # Son soruyu temizle
                del son_sorular[chat_id]
        
        asyncio.create_task(cevap_suresi_bitir())
        
    except Exception as e:
        print(f"❌ Soru gönderilemedi: {e}")

async def show_scores(chat_id):
    """Gruptaki puan durumunu göster"""
    if chat_id not in kullanici_puanlari or not kullanici_puanlari[chat_id]:
        await client.send_message(chat_id, "📊 Henüz puan kazanan yok!")
        return
    
    puanlar = kullanici_puanlari[chat_id]
    sirali = sorted(puanlar.items(), key=lambda x: x[1], reverse=True)[:10]
    
    mesaj = "🏆 **PUAN DURUMU** 🏆\n\n"
    
    for i, (kullanici_id, puan) in enumerate(sirali, 1):
        try:
            kullanici = await client.get_entity(kullanici_id)
            isim = kullanici.first_name or "İsimsiz"
            if kullanici.last_name:
                isim += " " + kullanici.last_name
            if kullanici.username:
                isim += f" (@{kullanici.username})"
            mesaj += f"{i}. {isim}: **{puan}** puan\n"
        except:
            mesaj += f"{i}. Kullanıcı: **{puan}** puan\n"
    
    await client.send_message(chat_id, mesaj)

async def quiz_dongusu():
    """Sürekli çalışan döngü - Aktif gruplara soru gönder"""
    print("🔄 Quiz döngüsü başladı...")
    
    while True:
        if aktif_gruplar:
            print(f"📊 Aktif grup sayısı: {len(aktif_gruplar)}")
            
            for grup_id in aktif_gruplar:
                await send_quiz_question(grup_id)
                await asyncio.sleep(10)  # Gruplar arası 10 saniye
            
            print("⏱️ 5 dakika bekleniyor...")
        else:
            print("😴 Aktif grup yok, bekleniyor...")
        
        await asyncio.sleep(300)  # 5 dakika

@client.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    chat_id = event.chat_id
    
    if event.is_private:
        await event.reply(
            "📜 **Dîrokzan Bot'a Hoş Geldiniz!** 📜\n\n"
            "Ben bir tarih quiz botuyum. Gruplarınıza ekleyip tarih soruları sorabilirsiniz.\n\n"
            "**📌 Kullanım:**\n"
            "1. Beni grubunuza ekleyin: @DirokzanBot\n"
            "2. Grupta /start yazın\n"
            "3. 5 dakikada bir otomatik soru gelsin!\n\n"
            "**📋 Komutlar:**\n"
            "/start - Botu başlat\n"
            "/stop - Botu durdur\n"
            "/puan - Puan durumunu göster\n"
            "/sorular - Kaç soru olduğunu göster\n"
            "/yardim - Yardım menüsü"
        )
    else:
        if chat_id not in aktif_gruplar:
            aktif_gruplar.append(chat_id)
            await event.reply(
                f"✅ **Bot aktif edildi!**\n\n"
                f"⏱️ **Sıklık:** 5 dakikada bir\n"
                f"📚 **Soru sayısı:** {len(TUM_SORULAR)}\n\n"
                "**Nasıl oynanır?**\n"
                "• Soru geldiğinde **A, B, C veya D** yazın\n"
                "• Doğru cevap için **30 saniyeniz** var\n"
                "• Her doğru cevap **+10 puan**\n\n"
                "İlk soru hemen geliyor! 🎯"
            )
            await send_quiz_question(chat_id)
        else:
            await event.reply("ℹ️ Bot zaten aktif.")

@client.on(events.NewMessage(pattern='/stop'))
async def stop_command(event):
    chat_id = event.chat_id
    if chat_id in aktif_gruplar:
        aktif_gruplar.remove(chat_id)
        await event.reply("⏸️ **Bot durduruldu.**\nTekrar başlatmak için /start yazın.")
    else:
        await event.reply("ℹ️ Bot zaten aktif değil.")

@client.on(events.NewMessage(pattern='/puan'))
async def puan_command(event):
    await show_scores(event.chat_id)

@client.on(events.NewMessage(pattern='/yardim'))
async def yardim_command(event):
    await event.reply(
        "📚 **Yardım Menüsü**\n\n"
        "**Komutlar:**\n"
        "/start - Botu başlat\n"
        "/stop - Botu durdur\n"
        "/puan - Puan durumunu göster\n"
        "/sorular - Kaç soru olduğunu göster\n\n"
        "**Nasıl Oynanır?**\n"
        "• Soru geldiğinde **A, B, C veya D** yazın\n"
        "• Doğru cevap için **30 saniyeniz** var\n"
        "• Her doğru cevap **+10 puan**\n\n"
        "📊 Puanlar her grupta ayrı tutulur."
    )

@client.on(events.NewMessage(pattern='/sorular'))
async def sorular_command(event):
    await event.reply(f"📚 Toplam **{len(TUM_SORULAR)}** tarih sorusu var.")

@client.on(events.NewMessage)
async def cevap_kontrol(event):
    if not event.is_group:
        return
    
    chat_id = event.chat_id
    
    if chat_id not in aktif_gruplar or chat_id not in son_sorular:
        return
    
    if not event.message.text or event.message.text.startswith('/'):
        return
    
    cevap = event.message.text.strip().upper()
    
    if cevap not in ['A', 'B', 'C', 'D']:
        return
    
    kullanici_id = event.sender_id
    
    if kullanici_id in son_sorular[chat_id].get('cevaplayanlar', []):
        await event.reply("⚠️ Zaten cevap verdiniz!")
        return
    
    harf_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    kullanici_index = harf_to_index.get(cevap, -1)
    dogru_index = son_sorular[chat_id]['correct_index']
    
    son_sorular[chat_id]['cevaplayanlar'].append(kullanici_id)
    
    if kullanici_index == dogru_index:
        kullanici_puanlari[chat_id][kullanici_id] += 10
        son_sorular[chat_id]['dogru_sayan'] += 1
        await event.reply(f"✅ **DOĞRU!** +10 puan! 🎉")
    else:
        await event.reply(f"❌ **YANLIŞ!**")

async def main():
    print("🚀 Dîrokzan Bot başlatılıyor...")
    print(f"📚 {len(TUM_SORULAR)} tarih sorusu yüklendi")
    print(f"🤖 Bot: @DirokzanBot")
    print("-" * 30)
    
    await client.start()
    print("✅ Bot başarıyla başlatıldı!")
    
    asyncio.create_task(quiz_dongusu())
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
