import discord
from discord.ext import commands

import asyncio
import requests
import os
import tempfile
import json

try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    Model = None
    KaldiRecognizer = None


from config import DISCORD_TOKEN
from config import PREFIX

from database import veritabani_olustur
from database import soru_kaydet
from database import soru_sayisi
from database import kullanici_gecmisi




TEKNIK_SERVIS_SITESI = "https://www.trendyol.com/"
TEKNIK_SERVIS_NUMARASI = "0850 540 600 025"




YEREL_AI_MODEL = "gemma3:1b"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"




VOSK_MODEL_PATH = "vosk-model-small-tr-0.3"

_vosk_model = None


def vosk_model_yukle():

    global _vosk_model

    if _vosk_model is not None:
        return _vosk_model

    if Model is None:

        print(
            "❌ Vosk kurulu değil. `pip install vosk` çalıştırın."
        )

        return None

    if not os.path.isdir(VOSK_MODEL_PATH):

        print(
            "❌ Vosk Türkçe model klasörü bulunamadı:",
            VOSK_MODEL_PATH
        )

        return None

    try:

        _vosk_model = Model(
            VOSK_MODEL_PATH
        )

        print(
            "🎤 Vosk Türkçe STT modeli hazır."
        )

        return _vosk_model

    except Exception as hata:

        print(
            "❌ Vosk model yükleme hatası:",
            hata
        )

        return None


def sesi_yaziya_cevir_sync(dosya_yolu):

    model = vosk_model_yukle()

    if model is None:
        return ""

    wav_yolu = dosya_yolu + ".wav"

    try:

        import subprocess

        sonuc = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                dosya_yolu,
                "-ar",
                "16000",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                wav_yolu
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if (
            sonuc.returncode != 0
            or not os.path.exists(wav_yolu)
        ):

            print(
                "❌ FFmpeg ses dönüştürme hatası:",
                sonuc.stderr[-1000:]
            )

            return ""

        import wave

        with wave.open(
            wav_yolu,
            "rb"
        ) as ses:

            if (
                ses.getnchannels() != 1
                or ses.getsampwidth() != 2
            ):

                print(
                    "❌ Ses formatı uygun değil."
                )

                return ""

            recognizer = KaldiRecognizer(
                model,
                ses.getframerate()
            )

            recognizer.SetWords(False)

            while True:

                veri = ses.readframes(4000)

                if not veri:
                    break

                recognizer.AcceptWaveform(
                    veri
                )

            sonuc_verisi = json.loads(
                recognizer.FinalResult()
            )

            return str(
                sonuc_verisi.get(
                    "text",
                    ""
                )
            ).strip()

    except FileNotFoundError:

        print(
            "❌ FFmpeg bulunamadı. "
            "FFmpeg'in PATH'e ekli olduğundan emin olun."
        )

        return ""

    except Exception as hata:

        print(
            "❌ STT HATASI:",
            hata
        )

        return ""

    finally:

        if os.path.exists(wav_yolu):

            try:
                os.remove(wav_yolu)

            except Exception:
                pass


async def sesi_yaziya_cevir(dosya_yolu):

    return await asyncio.to_thread(
        sesi_yaziya_cevir_sync,
        dosya_yolu
    )


# ==================================================
# DISCORD AYARLARI
# ==================================================

intents = discord.Intents.default()

intents.message_content = True


bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)




yazili_soru_sayisi = 0
sesli_soru_sayisi = 0
ai_soru_sayisi = 0




sesli_mesaj_bekleyenler = set()




BOT_ACIKLAMASI = (
    "🛠️ **TEKNİK SERVİS ASİSTANI**\n\n"

    "👋 **Merhaba!**\n"
    "Ben teknik servis destek botuyum. "
    "Alışveriş, sipariş, teknik sorunlar ve "
    "yapay zekâ desteği gibi konularda size yardımcı olabilirim.\n\n"

    "📌 **BOT NASIL ÇALIŞIR?**\n\n"

    "💬 **Mesaj Gönderme:**\n"
    "Sorununuzu doğrudan bu kanala yazabilirsiniz. "
    "Bot önce hazır cevaplar arasında sorunuza uygun bir cevap arar. "
    "Hazır cevap bulunamazsa yerel yapay zekâdan yardım alır.\n\n"

    "🛒 **Alışveriş:**\n"
    "Web sitesinden nasıl alışveriş yapılabileceği ve "
    "ürünlerin nasıl aranabileceği hakkında bilgi verir.\n\n"

    "📦 **Sipariş Durumu:**\n"
    "Verdiğiniz siparişin durumunu ve sipariş bilgilerinin "
    "nereden kontrol edilebileceğini açıklar.\n\n"

    "❌ **Sipariş İptali:**\n"
    "Sipariş gönderilmeden önce iptal işleminin nasıl "
    "yapılabileceği hakkında bilgi verir.\n\n"

    "⚠️ **Hasarlı / Bozuk Ürün:**\n"
    "Ürün hasarlı, kırık veya bozuk geldiyse "
    "hangi adımların izlenebileceğini açıklar.\n\n"

    "🔧 **Teknik Destek:**\n"
    "Bilgisayar, telefon, tablet, internet ve diğer "
    "teknik sorunlarınız için temel çözüm önerileri sunar.\n\n"

    "🚚 **Teslimat:**\n"
    "Kargo ve teslimat süreci hakkında genel bilgi verir "
    "ve sipariş bilgilerinizden teslimat durumunu "
    "nasıl kontrol edebileceğinizi açıklar.\n\n"

    "↩️ **İade:**\n"
    "Satın aldığınız bir ürünü iade etmek istediğinizde "
    "hangi bölümden iade seçeneklerini kontrol "
    "edebileceğinizi gösterir.\n\n"

    "🛡️ **Garanti:**\n"
    "Ürünlerin garanti bilgilerini nereden "
    "kontrol edebileceğinizi açıklar.\n\n"

    "💳 **Ödeme:**\n"
    "Ödeme yöntemleri ve ödeme sırasında "
    "yaşanabilecek sorunlar hakkında yardımcı olur.\n\n"

    "🧾 **Fatura:**\n"
    "Satın aldığınız ürünün faturasına "
    "nereden ulaşabileceğinizi açıklar.\n\n"

    "👤 **Hesap:**\n"
    "Yeni hesap oluşturma ve hesapla ilgili "
    "temel işlemler hakkında bilgi verir.\n\n"

    "🔑 **Şifre:**\n"
    "Şifrenizi unuttuğunuzda nasıl yenileyebileceğinizi "
    "açıklar.\n\n"

    "💻 **Bilgisayar:**\n"
    "Bilgisayar açılmıyor, yavaş çalışıyor veya "
    "başka bir teknik sorun yaşıyorsanız temel "
    "kontroller konusunda yardımcı olur.\n\n"

    "📱 **Telefon / Tablet:**\n"
    "Telefon veya tablet açılmıyor, şarj olmuyor "
    "ya da düzgün çalışmıyorsa temel çözüm önerileri sunar.\n\n"

    "🌐 **İnternet / Wi-Fi:**\n"
    "İnternet veya Wi-Fi bağlantısı çalışmıyorsa "
    "yapabileceğiniz temel kontrolleri açıklar.\n\n"

    "🖨️ **Yazıcı:**\n"
    "Yazıcının çalışmaması, bağlantı problemi veya "
    "kağıt sorunları gibi durumlarda temel öneriler verir.\n\n"

    "🔋 **Batarya:**\n"
    "Cihazınızın şarjının hızlı bitmesi gibi "
    "batarya sorunlarında temel öneriler sunar.\n\n"

    "💾 **Depolama:**\n"
    "Cihazınızda depolama alanı dolduğunda "
    "yer açmak için neler yapabileceğinizi açıklar.\n\n"

    "🖥️ **Ekran:**\n"
    "Ekranla ilgili temel sorunlarda "
    "kontrol edilebilecek noktaları açıklar.\n\n"

    "⌨️ **Klavye:**\n"
    "Klavye çalışmıyorsa bağlantı ve USB gibi "
    "temel kontrolleri yapmanıza yardımcı olur.\n\n"

    "🖱️ **Mouse:**\n"
    "Mouse çalışmadığında bağlantı, USB ve "
    "pil gibi temel kontrolleri açıklar.\n\n"

    "🔊 **Ses:**\n"
    "Cihazdan ses gelmiyorsa ses seviyesi, "
    "sessiz mod ve ses çıkışını kontrol etmenize yardımcı olur.\n\n"

    "📷 **Kamera:**\n"
    "Kamera çalışmıyorsa uygulama izinleri ve "
    "kamera ayarlarını kontrol etmenizi önerir.\n\n"

    "📶 **Bluetooth:**\n"
    "Bluetooth bağlantısı kurulamadığında "
    "bağlantıyı yeniden kurmak için temel adımları açıklar.\n\n"

    "🔄 **Güncelleme:**\n"
    "Cihaz veya uygulama güncellenmiyorsa "
    "internet ve depolama gibi temel kontrolleri açıklar.\n\n"

    "🛡️ **Güvenlik:**\n"
    "Hesap ve cihaz güvenliği için güçlü parola kullanımı, "
    "şüpheli bağlantılardan kaçınma gibi temel güvenlik "
    "önerileri verir.\n\n"

    "🔐 **Hesap Güvenliği:**\n"
    "Hesabınızı daha güvenli kullanmanız için "
    "güçlü parola ve iki aşamalı doğrulama gibi "
    "güvenlik yöntemlerini açıklar.\n\n"

    "🤖 **Yerel Yapay Zekâ:**\n"
    "Hazır cevaplarda bulunmayan sorularınızı "
    "bilgisayarınızda çalışan Ollama ve "
    "Gemma modeli ile cevaplamaya çalışır.\n\n"

    "🎤 **Sesli Mesaj:**\n"
    "Sesli Mesaj butonuna bastıktan sonra "
    "sesli sorunuzu Discord üzerinden gönderebilirsiniz. "
    "Sesiniz yerel Vosk sistemi ile yazıya çevrilir "
    "ve ortaya çıkan soru Ollama'ya gönderilir.\n\n"

    "📚 **Soru Geçmişi:**\n"
    "Daha önce sorduğunuz soruların son 5 tanesini "
    "görüntülemenizi sağlar.\n\n"

    "📊 **İstatistik:**\n"
    "Botun kaç yazılı soru, kaç sesli soru ve "
    "kaç yapay zekâ sorusu cevapladığını gösterir.\n\n"

    "⭐ **Geri Bildirim:**\n"
    "Botu 1 ile 5 arasında puanlayabilir ve "
    "bot hakkındaki düşüncelerinizi yazabilirsiniz.\n\n"

    "🔐 **Yönetici:**\n"
    "Yalnızca sunucu yöneticilerinin kullanabildiği "
    "bölümdür. Botun soru istatistiklerini gösterir.\n\n"

    "📞 **Teknik Servis:**\n"
    "Teknik servis telefon numarası ve web sitesi "
    "gibi iletişim bilgilerini görüntüleyebilirsiniz.\n\n"

    "💡 **Kullanım:**\n"
    "Aşağıdaki butonlardan istediğiniz özelliği seçin "
    "veya sorununuzu doğrudan mesaj olarak yazın."
)




ANA_MENU_MESAJI = (
    "🛠️ **TEKNİK SERVİS ASİSTANI**\n\n"
    "Merhaba! 👋\n"
    "Aşağıdaki butonlardan yapmak istediğiniz işlemi seçebilirsiniz.\n\n"
    "📖 **Bot Açıklaması** butonuna basarak botun tüm "
    "özelliklerinin ne işe yaradığını görebilirsiniz."
)




sorular = {

    "nasıl alışveriş yapabilirim":
        "🛒 İstediğiniz ürünü seçip sepete ekleyebilirsiniz. "
        "Daha sonra sepet bölümünden satın alma işlemini "
        "tamamlayabilirsiniz.",

    "siparişimin durumunu nasıl öğrenebilirim":
        "📦 Sipariş durumunuzu hesabınızdaki "
        "\"Siparişlerim\" bölümünden kontrol edebilirsiniz.",

    "bir siparişi nasıl iptal edebilirim":
        "❌ Siparişiniz gönderilmeden önce iptal işlemi "
        "yapılabilir. İptal için sipariş bölümünü kontrol "
        "edebilir veya müşteri hizmetleriyle iletişime "
        "geçebilirsiniz.",

    "siparişim hasarlı gelirse ne yapmalıyım":
        "⚠️ Hasarlı ürün teslim aldıysanız ürünü kullanmadan "
        "müşteri hizmetleriyle iletişime geçmeniz ve mümkünse "
        "ürünün fotoğraflarını saklamanız önerilir.",

    "teknik destekle nasıl iletişime geçebilirim":
        "🔧 Teknik destek için:\n\n"
        "📞 Telefon: " + TEKNIK_SERVIS_NUMARASI + "\n"
        "🌐 Web sitesi: " + TEKNIK_SERVIS_SITESI,

    "teslimat ne kadar sürer":
        "🚚 Teslimat süresi ürüne, satıcıya ve kargo şirketine "
        "göre değişebilir. Siparişinizin tahmini teslimat "
        "tarihini sipariş bilgilerinden kontrol edebilirsiniz.",

    "iade nasıl yapılır":
        "↩️ İade işlemi için siparişleriniz bölümünden ilgili "
        "siparişi seçebilir ve mevcut iade seçeneklerini "
        "kontrol edebilirsiniz.",

    "garanti süresi ne kadar":
        "🛡️ Garanti süresi ürüne göre değişebilir. "
        "Ürün sayfasındaki veya satın alma belgesindeki "
        "garanti bilgilerini kontrol edebilirsiniz.",

    "ödeme başarısız oldu":
        "💳 Kart bilgilerinizi kontrol edip tekrar deneyin. "
        "Sorun devam ederse farklı bir ödeme yöntemi "
        "deneyebilir veya müşteri hizmetleriyle iletişime "
        "geçebilirsiniz.",

    "fatura nasıl alınır":
        "🧾 Faturanıza hesabınızdaki siparişler bölümünden "
        "ulaşabilirsiniz.",

    "hesabımı nasıl açabilirim":
        "👤 Web sitesindeki hesap bölümünden kayıt olarak "
        "yeni bir hesap oluşturabilirsiniz.",

    "şifremi unuttum":
        "🔑 Giriş ekranındaki \"Şifremi Unuttum\" seçeneğini "
        "kullanarak şifrenizi yenileyebilirsiniz.",

    "ürün nasıl aranır":
        "🔎 Web sitesindeki arama bölümüne ürünün adını "
        "yazarak arama yapabilirsiniz.",

    "ürün stokta yok":
        "📦 Ürün stokta yoksa daha sonra tekrar kontrol "
        "edebilirsiniz. Stok durumu zaman içinde değişebilir.",

    "sipariş numaramı nereden bulabilirim":
        "🔢 Sipariş numaranızı siparişlerim bölümündeki "
        "ilgili siparişin ayrıntılarında bulabilirsiniz.",

    "kargo takip numarası nerede":
        "🚚 Kargo takip numarası, siparişiniz kargoya "
        "verildikten sonra sipariş bilgilerinde görünebilir.",

    "kargom nerede":
        "📦 Kargonuzu takip etmek için siparişinizdeki "
        "kargo takip bilgilerini kontrol edebilirsiniz.",

    "ürün bozuk geldi":
        "⚠️ Ürün bozuk geldiyse ürünü kullanmayı bırakın ve "
        "müşteri hizmetleriyle iletişime geçin.",

    "ürün kırık geldi":
        "⚠️ Ürün kırık geldiyse durumu müşteri hizmetlerine "
        "bildirin ve ürünün fotoğraflarını saklayın.",

    "bilgisayarım açılmıyor":
        "💻 Bilgisayar açılmıyorsa güç bağlantısını, şarj "
        "adaptörünü ve güç düğmesini kontrol edin. Sorun "
        "devam ederse teknik destek alın.",

    "bilgisayarım yavaş":
        "🐌 Bilgisayar yavaşsa gereksiz programları kapatmayı, "
        "bilgisayarı yeniden başlatmayı ve depolama alanını "
        "kontrol etmeyi deneyebilirsiniz.",

    "telefonum açılmıyor":
        "📱 Telefon açılmıyorsa şarj durumunu kontrol edin "
        "ve cihazı yeniden başlatmayı deneyin. Sorun devam "
        "ederse teknik destek alın.",

    "tablet açılmıyor":
        "📱 Tablet açılmıyorsa şarj bağlantısını kontrol edin "
        "ve cihazı yeniden başlatmayı deneyin.",

    "telefon şarj olmuyor":
        "🔌 Şarj kablosunu ve adaptörü kontrol edin. Farklı "
        "bir uyumlu şarj kablosu veya adaptör ile deneme "
        "yapabilirsiniz.",

    "batarya çabuk bitiyor":
        "🔋 Pilin hızlı tükenmesinin birçok nedeni olabilir. "
        "Arka plandaki gereksiz uygulamaları kapatmayı ve "
        "pil kullanım bölümünü kontrol etmeyi deneyin.",

    "ekran çalışmıyor":
        "🖥️ Ekran çalışmıyorsa cihazın güç durumunu ve "
        "bağlantılarını kontrol edin. Sorun devam ederse "
        "teknik destek alın.",

    "internet çalışmıyor":
        "🌐 Modemi ve cihazınızı yeniden başlatmayı deneyin. "
        "Sorun devam ederse internet servis sağlayıcınızla "
        "iletişime geçebilirsiniz.",

    "wifi bağlanmıyor":
        "📡 Wi-Fi bağlantısını kapatıp tekrar açmayı ve "
        "ağı yeniden seçmeyi deneyin.",

    "yazıcı çalışmıyor":
        "🖨️ Yazıcının güç bağlantısını, kablosunu ve kağıt "
        "durumunu kontrol edin.",

    "klavye çalışmıyor":
        "⌨️ Klavye bağlantısını kontrol edin. USB bağlantısı "
        "kullanıyorsanız farklı bir USB bağlantısı deneyebilirsiniz.",

    "mouse çalışmıyor":
        "🖱️ Mouse bağlantısını ve pil durumunu kontrol edin. "
        "Kabloluysa bağlantıyı tekrar takmayı deneyebilirsiniz.",

    "depolama alanım dolu":
        "💾 Gereksiz dosyaları ve kullanmadığınız programları "
        "silerek depolama alanı açabilirsiniz.",

    "uygulama çalışmıyor":
        "📱 Uygulamayı kapatıp tekrar açmayı ve cihazı "
        "yeniden başlatmayı deneyin.",

    "ürün hakkında bilgi":
        "🛒 Ürünün teknik özelliklerini ürün sayfasından "
        "kontrol edebilirsiniz.",

    "müşteri hizmetleri":
        "☎️ Müşteri hizmetleri için:\n\n"
        "📞 " + TEKNIK_SERVIS_NUMARASI + "\n"
        "🌐 " + TEKNIK_SERVIS_SITESI,

    "teknik servis nerede":
        "🔧 Teknik servis bilgileri için:\n\n"
        "📞 " + TEKNIK_SERVIS_NUMARASI + "\n"
        "🌐 " + TEKNIK_SERVIS_SITESI,

    "ödeme yöntemleri":
        "💳 Kullanılabilir ödeme yöntemlerini ödeme "
        "sayfasında görebilirsiniz.",

    "sipariş verdim":
        "📦 Siparişinizin durumunu hesabınızdaki "
        "\"Siparişlerim\" bölümünden kontrol edebilirsiniz.",

    "ürün değiştirmek istiyorum":
        "🔄 Ürün değişimi için ilgili siparişin seçeneklerini "
        "kontrol edin veya müşteri hizmetleriyle iletişime geçin.",

    "adresimi değiştirmek istiyorum":
        "🏠 Sipariş gönderilmeden önce adres değişikliği "
        "mümkün olabilir. Sipariş bilgilerinizi kontrol edin.",

    "hesabımı kapatmak istiyorum":
        "👤 Hesap kapatma işlemleri için hesap ayarlarınızı "
        "kontrol edebilir veya müşteri hizmetleriyle "
        "iletişime geçebilirsiniz."
}




yeni_cevaplar = {

    "telefon sorunları":
        "📱 Telefonunuzda sorun varsa öncelikle cihazı yeniden "
        "başlatmayı ve şarj durumunu kontrol etmeyi deneyin. "
        "Sorun devam ederse teknik destek alın.",

    "bilgisayar sorunları":
        "💻 Bilgisayar sorunlarında cihazı yeniden başlatmayı, "
        "kabloları kontrol etmeyi ve depolama alanını incelemeyi "
        "deneyebilirsiniz.",

    "wifi sorunları":
        "📡 Wi-Fi sorunu yaşıyorsanız modemi ve cihazı yeniden "
        "başlatmayı deneyin. Wi-Fi bağlantısını kapatıp tekrar "
        "açabilirsiniz.",

    "şarj sorunları":
        "🔌 Şarj sorunu için kabloyu ve adaptörü kontrol edin. "
        "Mümkünse uyumlu başka bir kablo veya adaptör deneyin.",

    "pil batarya":
        "🔋 Pil hızlı bitiyorsa arka plandaki gereksiz uygulamaları "
        "kapatın ve pil kullanım bölümünü kontrol edin.",

    "ekran sorunları":
        "🖥️ Ekran sorunu varsa cihazın açık olduğundan ve güç "
        "bağlantısının bulunduğundan emin olun. Sorun devam ederse "
        "teknik destek alın.",

    "klavye sorunları":
        "⌨️ Klavye çalışmıyorsa bağlantıyı kontrol edin. USB "
        "klavyelerde farklı bir USB bağlantısı deneyebilirsiniz.",

    "mouse sorunları":
        "🖱️ Mouse çalışmıyorsa kablo veya USB bağlantısını kontrol "
        "edin. Kablosuz mouse kullanıyorsanız pil durumunu kontrol edin.",

    "yazıcı sorunları":
        "🖨️ Yazıcı çalışmıyorsa güç bağlantısını, USB/Wi-Fi "
        "bağlantısını ve kağıt durumunu kontrol edin.",

    "depolama sorunları":
        "💾 Depolama alanı doluysa kullanmadığınız uygulamaları "
        "ve gereksiz dosyaları kaldırarak yer açabilirsiniz.",

    "ses sorunları":
        "🔊 Ses gelmiyorsa ses seviyesini, sessiz modu ve seçili "
        "ses çıkış cihazını kontrol edin.",

    "kamera sorunları":
        "📷 Kamera çalışmıyorsa uygulamanın kamera iznini ve "
        "cihazın kamera ayarlarını kontrol edin.",

    "bluetooth sorunları":
        "📶 Bluetooth bağlanmıyorsa Bluetooth'u kapatıp açın ve "
        "bağlanmak istediğiniz cihazı yeniden eşleştirmeyi deneyin.",

    "güncelleme sorunları":
        "🔄 Güncelleme yapılmıyorsa cihazın internete bağlı "
        "olduğundan ve yeterli depolama alanı bulunduğundan emin olun.",

    "güvenlik sorunları":
        "🛡️ Güvenlik için güçlü ve benzersiz parolalar kullanın, "
        "şüpheli bağlantılara tıklamayın ve cihazınızı güncel tutun.",

    "hesap güvenliği":
        "🔐 Hesabınızı korumak için güçlü bir parola kullanın ve "
        "mümkünse iki aşamalı doğrulamayı etkinleştirin.",

    "teslim alma":
        "📦 Teslim alırken mümkünse paketin dış durumunu kontrol "
        "edin. Hasar fark ederseniz durumu kargo ve müşteri hizmetlerine "
        "bildirin.",

    "fatura sorunları":
        "🧾 Faturanıza ulaşamıyorsanız hesabınızdaki siparişler "
        "bölümünü kontrol edin. Sorun devam ederse müşteri hizmetlerine "
        "başvurabilirsiniz.",

    "ödeme sorunları":
        "💳 Ödeme sorunu yaşıyorsanız kart bilgilerini ve kullanılabilir "
        "ödeme yöntemlerini kontrol edin. Sorun devam ederse farklı "
        "bir ödeme yöntemi deneyebilirsiniz.",

    "müşteri hizmetleri":
        "📞 Müşteri hizmetleri için:\n\n"
        "Telefon: " + TEKNIK_SERVIS_NUMARASI + "\n"
        "Web sitesi: " + TEKNIK_SERVIS_SITESI
}


# ==================================================
# SORUYU TEMİZLE
# ==================================================

def soruyu_temizle(soru):

    if not isinstance(soru, str):
        return ""

    soru = soru.lower().strip()

    noktalama = "?!.,;:()[]{}\"'`"

    for karakter in noktalama:
        soru = soru.replace(
            karakter,
            ""
        )

    soru = " ".join(
        soru.split()
    )

    return soru



def hazir_cevap_bul(soru):

    soru = soruyu_temizle(
        soru
    )

    if not soru:
        return None

    for anahtar, cevap in sorular.items():

        temiz_anahtar = soruyu_temizle(
            anahtar
        )

        if temiz_anahtar in soru:
            return cevap

    return None


# ==================================================
# OLLAMA KONTROL
# ==================================================

def ollama_kontrol_sync():

    try:

        cevap = requests.get(
            OLLAMA_TAGS_URL,
            timeout=5
        )

        if cevap.status_code != 200:

            print(
                "⚠️ Ollama HTTP durumu:",
                cevap.status_code
            )

            return False

        veri = cevap.json()

        modeller = veri.get(
            "models",
            []
        )

        bulunan_modeller = []

        for model in modeller:

            isim = str(
                model.get(
                    "name",
                    ""
                )
            )

            bulunan_modeller.append(
                isim
            )

            if (
                isim == YEREL_AI_MODEL
                or isim.startswith(
                    YEREL_AI_MODEL + ":"
                )
            ):

                return True

        print(
            "⚠️ Ollama çalışıyor fakat model bulunamadı:",
            YEREL_AI_MODEL
        )

        if bulunan_modeller:

            print(
                "📦 Yüklü modeller:",
                ", ".join(
                    bulunan_modeller
                )
            )

        return False

    except requests.exceptions.ConnectionError:

        print(
            "❌ Ollama çalışmıyor."
        )

        return False

    except requests.exceptions.Timeout:

        print(
            "⏳ Ollama kontrolü zaman aşımına uğradı."
        )

        return False

    except Exception as hata:

        print(
            "⚠️ Ollama kontrol hatası:",
            hata
        )

        return False


async def ollama_kontrol():

    return await asyncio.to_thread(
        ollama_kontrol_sync
    )




def yerel_ai_cevabi_sync(soru):

    sistem_mesaji = (
        "Sen Türkçe konuşan bir teknik servis destek botusun.\n\n"
        "Kısa, anlaşılır ve yardımcı cevaplar ver.\n"
        "Teknik servis, bilgisayar, telefon, tablet, internet, "
        "sipariş, alışveriş, kargo, iade, garanti, ödeme ve fatura "
        "konularında yardımcı ol.\n"
        "Bilmediğin şirket bilgilerini uydurma.\n"
        "Bilmediğin sipariş bilgilerini uydurma.\n"
        "Tehlikeli işlemler için güvenli ve genel öneriler ver.\n"
        "Kullanıcıya Türkçe cevap ver."
    )

    prompt = (
        sistem_mesaji
        + "\n\nKullanıcının sorusu:\n"
        + soru
        + "\n\nCevap:"
    )

    try:

        sonuc = requests.post(

            OLLAMA_URL,

            json={
                "model": YEREL_AI_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            },

            timeout=120
        )

        if sonuc.status_code != 200:

            print(
                "❌ OLLAMA HTTP HATASI:",
                sonuc.status_code
            )

            print(
                sonuc.text[:1000]
            )

            return (
                "❌ Yerel yapay zekâ şu anda cevap veremiyor.\n\n"
                "Ollama'nın çalıştığını ve "
                f"`{YEREL_AI_MODEL}` modelinin yüklü olduğunu "
                "kontrol edin."
            )

        try:

            veri = sonuc.json()

        except ValueError:

            return (
                "❌ Ollama'dan geçerli bir cevap alınamadı."
            )

        cevap = str(
            veri.get(
                "response",
                ""
            )
        ).strip()

        if cevap == "":

            return (
                "❌ Yapay zekâ boş bir cevap verdi."
            )

        return cevap

    except requests.exceptions.ConnectionError:

        print(
            "❌ Ollama çalışmıyor."
        )

        return (
            "❌ Yerel yapay zekâya bağlanılamadı.\n\n"
            "Ollama'nın çalıştığından emin olun."
        )

    except requests.exceptions.Timeout:

        return (
            "⏳ Yapay zekâ çok uzun sürede cevap verdi."
        )

    except Exception as hata:

        print(
            "❌ YEREL AI HATASI:",
            hata
        )

        return (
            "❌ Yerel yapay zekâya ulaşılamadı."
        )


async def yerel_ai_cevabi(soru):

    global ai_soru_sayisi

    ai_soru_sayisi += 1

    return await asyncio.to_thread(
        yerel_ai_cevabi_sync,
        soru
    )


async def yapay_zeka_cevabi(soru):

    return await yerel_ai_cevabi(
        soru
    )




def mesaj_parcalari(
    mesaj,
    maksimum=1800
):

    if not mesaj:
        return [""]

    parcalar = []

    while len(mesaj) > maksimum:

        bolum = mesaj[:maksimum]

        son_bosluk = bolum.rfind(" ")

        if son_bosluk > 500:
            bolum = bolum[:son_bosluk]

        parcalar.append(
            bolum
        )

        mesaj = mesaj[
            len(bolum):
        ].lstrip()

    if mesaj:
        parcalar.append(
            mesaj
        )

    return parcalar


async def mesaj_gonder(
    channel,
    mesaj,
    **kwargs
):

    parcalar = mesaj_parcalari(
        mesaj
    )

    for parca in parcalar:

        await channel.send(
            parca,
            **kwargs
        )




async def aciklamayi_goster(
    interaction
):

    parcalar = mesaj_parcalari(
        BOT_ACIKLAMASI,
        1800
    )

    toplam = len(parcalar)

    ilk_mesaj = (
        "📖 **Bot Açıklaması "
        + str(1)
        + "/"
        + str(toplam)
        + "**\n\n"
        + parcalar[0]
    )

    await interaction.response.send_message(
        ilk_mesaj,
        ephemeral=True
    )

    for sayac, parca in enumerate(
        parcalar[1:],
        start=2
    ):

        await interaction.followup.send(
            "📖 **Bot Açıklaması "
            + str(sayac)
            + "/"
            + str(toplam)
            + "**\n\n"
            + parca,
            ephemeral=True
        )




class GeriBildirimModal(
    discord.ui.Modal
):

    def __init__(self):

        super().__init__(
            title="Teknik Servis Geri Bildirimi"
        )

        self.puan = discord.ui.TextInput(
            label="Hizmetimizi 1-5 arasında puanlayın",
            placeholder="Örneğin: 5",
            required=True,
            max_length=1
        )

        self.yorum = discord.ui.TextInput(
            label="Yorumunuz",
            placeholder="Bot hakkında düşüncenizi yazın...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500
        )

        self.add_item(
            self.puan
        )

        self.add_item(
            self.yorum
        )

    async def on_submit(
        self,
        interaction
    ):

        puan = str(
            self.puan.value
        ).strip()

        yorum = str(
            self.yorum.value
        ).strip()

        if puan not in [
            "1",
            "2",
            "3",
            "4",
            "5"
        ]:

            await interaction.response.send_message(
                "❌ Lütfen 1 ile 5 arasında bir puan girin.",
                ephemeral=True
            )

            return

        if yorum == "":
            yorum = "Yorum bırakılmadı."

        print(
            "⭐ GERİ BİLDİRİM:",
            str(interaction.user),
            "| Puan:",
            puan,
            "| Yorum:",
            yorum
        )

        await interaction.response.send_message(
            "⭐ **Geri bildirimin için teşekkürler!**\n\n"
            "Puanın: " + puan + "/5\n\n"
            "Görüşün bizim için çok değerli.",
            ephemeral=True
        )




class AIsoruModal(
    discord.ui.Modal
):

    def __init__(self):

        super().__init__(
            title="Yapay Zekâya Soru Sor"
        )

        self.soru = discord.ui.TextInput(
            label="Sorunuz",
            placeholder="Örneğin: Bilgisayarım neden açılmıyor?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(
            self.soru
        )

    async def on_submit(
        self,
        interaction
    ):

        soru = str(
            self.soru.value
        ).strip()

        if not soru:

            await interaction.response.send_message(
                "❌ Soru boş olamaz.",
                ephemeral=True
            )

            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            cevap = await yapay_zeka_cevabi(
                soru
            )

            try:

                soru_kaydet(
                    interaction.user.id,
                    str(interaction.user),
                    soru,
                    cevap
                )

            except Exception as hata:

                print(
                    "⚠️ VERİTABANI HATASI:",
                    hata
                )

            await interaction.followup.send(
                "🤖 **Yerel Yapay Zekâ Cevabı:**\n\n"
                + cevap,
                ephemeral=True
            )

        except Exception as hata:

            print(
                "❌ AI HATASI:",
                hata
            )

            await interaction.followup.send(
                "❌ Yerel yapay zekâya ulaşılamadı.",
                ephemeral=True
            )




class AnaMenu(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    async def cevap_ver(
        self,
        interaction,
        cevap
    ):

        try:

            await interaction.response.send_message(
                cevap,
                ephemeral=True
            )

        except discord.InteractionResponded:

            await interaction.followup.send(
                cevap,
                ephemeral=True
            )




    @discord.ui.button(
        label="Alışveriş",
        style=discord.ButtonStyle.primary,
        emoji="🛒",
        row=0
    )
    async def alisveris(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "nasıl alışveriş yapabilirim"
            ]
        )




    @discord.ui.button(
        label="Sipariş Durumu",
        style=discord.ButtonStyle.primary,
        emoji="📦",
        row=0
    )
    async def siparis_durumu(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "siparişimin durumunu nasıl öğrenebilirim"
            ]
        )



    @discord.ui.button(
        label="Sipariş İptali",
        style=discord.ButtonStyle.danger,
        emoji="❌",
        row=0
    )
    async def siparis_iptal(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "bir siparişi nasıl iptal edebilirim"
            ]
        )




    @discord.ui.button(
        label="Hasarlı Ürün",
        style=discord.ButtonStyle.danger,
        emoji="⚠️",
        row=0
    )
    async def hasarli(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "siparişim hasarlı gelirse ne yapmalıyım"
            ]
        )




    @discord.ui.button(
        label="Teknik Destek",
        style=discord.ButtonStyle.success,
        emoji="🔧",
        row=1
    )
    async def teknik_destek(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "teknik destekle nasıl iletişime geçebilirim"
            ]
        )




    @discord.ui.button(
        label="Teslimat",
        style=discord.ButtonStyle.secondary,
        emoji="🚚",
        row=1
    )
    async def teslimat(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "teslimat ne kadar sürer"
            ]
        )




    @discord.ui.button(
        label="İade",
        style=discord.ButtonStyle.secondary,
        emoji="↩️",
        row=1
    )
    async def iade(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "iade nasıl yapılır"
            ]
        )




    @discord.ui.button(
        label="Garanti",
        style=discord.ButtonStyle.secondary,
        emoji="🛡️",
        row=1
    )
    async def garanti(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "garanti süresi ne kadar"
            ]
        )




    @discord.ui.button(
        label="Ödeme",
        style=discord.ButtonStyle.secondary,
        emoji="💳",
        row=2
    )
    async def odeme(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "ödeme yöntemleri"
            ]
        )




    @discord.ui.button(
        label="Fatura",
        style=discord.ButtonStyle.secondary,
        emoji="🧾",
        row=2
    )
    async def fatura(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            sorular[
                "fatura nasıl alınır"
            ]
        )




    @discord.ui.button(
        label="Soru Geçmişim",
        style=discord.ButtonStyle.primary,
        emoji="📚",
        row=2
    )
    async def gecmis(
        self,
        interaction,
        button
    ):

        try:

            gecmis = kullanici_gecmisi(
                interaction.user.id
            )

        except Exception as hata:

            print(
                "GEÇMİŞ HATASI:",
                hata
            )

            await interaction.response.send_message(
                "❌ Soru geçmişi alınamadı.",
                ephemeral=True
            )

            return

        if not gecmis:

            await interaction.response.send_message(
                "📭 Henüz kayıtlı bir soru geçmişin yok.",
                ephemeral=True
            )

            return

        mesaj = "📚 **Son 5 Sorun**\n\n"

        for sayac, soru in enumerate(
            gecmis[:5],
            start=1
        ):

            if isinstance(
                soru,
                (tuple, list)
            ):

                metin = str(
                    soru[0]
                )

            else:

                metin = str(
                    soru
                )

            mesaj += (
                str(sayac)
                + ". "
                + metin
                + "\n"
            )

        await interaction.response.send_message(
            mesaj,
            ephemeral=True
        )




    @discord.ui.button(
        label="İstatistik",
        style=discord.ButtonStyle.primary,
        emoji="📊",
        row=3
    )
    async def istatistik(
        self,
        interaction,
        button
    ):

        try:

            toplam = soru_sayisi()

        except Exception:

            toplam = 0

        await interaction.response.send_message(

            "📊 **TEKNİK SERVİS İSTATİSTİKLERİ**\n\n"
            "💬 Yazılı sorular: "
            + str(
                yazili_soru_sayisi
            )
            + "\n"
            "🎤 Sesli sorular: "
            + str(
                sesli_soru_sayisi
            )
            + "\n"
            "🤖 AI soruları: "
            + str(
                ai_soru_sayisi
            )
            + "\n"
            "🗄️ Toplam kayıt: "
            + str(
                toplam
            ),

            ephemeral=True
        )




    @discord.ui.button(
        label="Yapay Zekâ",
        style=discord.ButtonStyle.success,
        emoji="🤖",
        row=3
    )
    async def ai(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            AIsoruModal()
        )




    @discord.ui.button(
        label="Geri Bildirim",
        style=discord.ButtonStyle.secondary,
        emoji="⭐",
        row=4
    )
    async def geri_bildirim(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            GeriBildirimModal()
        )




    @discord.ui.button(
        label="Yönetici",
        style=discord.ButtonStyle.danger,
        emoji="🔐",
        row=4
    )
    async def yonetici_buton(
        self,
        interaction,
        button
    ):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Bu bölümü yalnızca sunucu yöneticileri "
                "kullanabilir.",
                ephemeral=True
            )

            return

        try:

            toplam = soru_sayisi()

        except Exception:

            toplam = 0

        await interaction.response.send_message(

            "🔐 **YÖNETİCİ PANELİ**\n\n"
            "📊 Toplam soru: "
            + str(
                toplam
            )
            + "\n"
            "💬 Yazılı soru: "
            + str(
                yazili_soru_sayisi
            )
            + "\n"
            "🎤 Sesli soru: "
            + str(
                sesli_soru_sayisi
            )
            + "\n"
            "🤖 AI sorusu: "
            + str(
                ai_soru_sayisi
            ),

            ephemeral=True
        )




    @discord.ui.button(
        label="Bot Açıklaması",
        style=discord.ButtonStyle.primary,
        emoji="📖",
        row=4
    )
    async def bot_aciklamasi(
        self,
        interaction,
        button
    ):

        await aciklamayi_goster(
            interaction
        )




    @discord.ui.button(
        label="Ana Menü",
        style=discord.ButtonStyle.primary,
        emoji="🏠",
        row=4
    )
    async def ana_menu(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            content=ANA_MENU_MESAJI,
            view=AnaMenu()
        )




    @discord.ui.button(
        label="Diğer Destekler",
        style=discord.ButtonStyle.success,
        emoji="🛠️",
        row=4
    )
    async def diger_destekler(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            content=(
                "🛠️ **DİĞER TEKNİK DESTEKLER - SAYFA 2**\n\n"
                "İhtiyacınız olan teknik destek seçeneğini seçin."
            ),
            view=TeknikMenu2()
        )




class TeknikMenu2(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    async def cevap_ver(
        self,
        interaction,
        cevap
    ):

        try:

            await interaction.response.send_message(
                cevap,
                ephemeral=True
            )

        except discord.InteractionResponded:

            await interaction.followup.send(
                cevap,
                ephemeral=True
            )


    @discord.ui.button(
        label="Telefon",
        style=discord.ButtonStyle.primary,
        emoji="📱",
        row=0
    )
    async def telefon_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "telefon sorunları"
            ]
        )


    @discord.ui.button(
        label="Bilgisayar",
        style=discord.ButtonStyle.primary,
        emoji="💻",
        row=0
    )
    async def bilgisayar_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "bilgisayar sorunları"
            ]
        )


    @discord.ui.button(
        label="Wi-Fi",
        style=discord.ButtonStyle.primary,
        emoji="📡",
        row=1
    )
    async def wifi_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "wifi sorunları"
            ]
        )


    @discord.ui.button(
        label="Şarj",
        style=discord.ButtonStyle.primary,
        emoji="🔌",
        row=1
    )
    async def sarj_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "şarj sorunları"
            ]
        )


    @discord.ui.button(
        label="Pil",
        style=discord.ButtonStyle.primary,
        emoji="🔋",
        row=2
    )
    async def pil_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "pil batarya"
            ]
        )


    @discord.ui.button(
        label="Ekran",
        style=discord.ButtonStyle.secondary,
        emoji="🖥️",
        row=2
    )
    async def ekran_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "ekran sorunları"
            ]
        )


    @discord.ui.button(
        label="Klavye",
        style=discord.ButtonStyle.secondary,
        emoji="⌨️",
        row=3
    )
    async def klavye_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "klavye sorunları"
            ]
        )


    @discord.ui.button(
        label="Mouse",
        style=discord.ButtonStyle.secondary,
        emoji="🖱️",
        row=3
    )
    async def mouse_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "mouse sorunları"
            ]
        )


    @discord.ui.button(
        label="Yazıcı",
        style=discord.ButtonStyle.secondary,
        emoji="🖨️",
        row=4
    )
    async def yazici_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "yazıcı sorunları"
            ]
        )


    @discord.ui.button(
        label="Depolama",
        style=discord.ButtonStyle.secondary,
        emoji="💾",
        row=4
    )
    async def depolama_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "depolama sorunları"
            ]
        )


    @discord.ui.button(
        label="Sonraki Sayfa",
        style=discord.ButtonStyle.success,
        emoji="➡️",
        row=4
    )
    async def sonraki_sayfa(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            content=(
                "🛠️ **DİĞER TEKNİK DESTEKLER - SAYFA 3**\n\n"
                "Daha fazla teknik destek seçeneği."
            ),
            view=TeknikMenu3()
        )


    @discord.ui.button(
        label="Ana Menü",
        style=discord.ButtonStyle.primary,
        emoji="🏠",
        row=4
    )
    async def ana_menu(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            content=ANA_MENU_MESAJI,
            view=AnaMenu()
        )



class TeknikMenu3(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    async def cevap_ver(
        self,
        interaction,
        cevap
    ):

        try:

            await interaction.response.send_message(
                cevap,
                ephemeral=True
            )

        except discord.InteractionResponded:

            await interaction.followup.send(
                cevap,
                ephemeral=True
            )


    @discord.ui.button(
        label="Ses",
        style=discord.ButtonStyle.secondary,
        emoji="🔊",
        row=0
    )
    async def ses_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "ses sorunları"
            ]
        )


    @discord.ui.button(
        label="Kamera",
        style=discord.ButtonStyle.secondary,
        emoji="📷",
        row=0
    )
    async def kamera_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "kamera sorunları"
            ]
        )


    @discord.ui.button(
        label="Bluetooth",
        style=discord.ButtonStyle.secondary,
        emoji="📶",
        row=1
    )
    async def bluetooth_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "bluetooth sorunları"
            ]
        )


    @discord.ui.button(
        label="Güncelleme",
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        row=1
    )
    async def guncelleme_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "güncelleme sorunları"
            ]
        )


    @discord.ui.button(
        label="Güvenlik",
        style=discord.ButtonStyle.danger,
        emoji="🛡️",
        row=2
    )
    async def guvenlik_sorunlari(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "güvenlik sorunları"
            ]
        )


    @discord.ui.button(
        label="Hesap Güvenliği",
        style=discord.ButtonStyle.danger,
        emoji="🔐",
        row=2
    )
    async def hesap_guvenligi(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "hesap güvenliği"
            ]
        )


    @discord.ui.button(
        label="Teslim Alma",
        style=discord.ButtonStyle.primary,
        emoji="📦",
        row=3
    )
    async def teslim_alma(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "teslim alma"
            ]
        )


    @discord.ui.button(
        label="Fatura Sorunu",
        style=discord.ButtonStyle.primary,
        emoji="🧾",
        row=3
    )
    async def fatura_sorunu(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "fatura sorunları"
            ]
        )


    @discord.ui.button(
        label="Sesli Mesaj",
        style=discord.ButtonStyle.success,
        emoji="🎤",
        row=3
    )
    async def sesli_mesaj(
        self,
        interaction,
        button
    ):

        sesli_mesaj_bekleyenler.add(
            interaction.user.id
        )

        await interaction.response.send_message(
            "🎤 **Sesli soru modu açıldı!**\n\n"
            "Şimdi buraya bir Discord sesli mesajı gönder.\n\n"
            "🧠 Ses, internet API'si kullanılmadan yerel Vosk "
            "ile yazıya çevrilecek.\n"
            "🤖 Ortaya çıkan metin Ollama'ya gönderilecek.\n\n"
            "⏳ Hazır olduğunda sesli mesajını gönder!",
            ephemeral=True
        )


    @discord.ui.button(
        label="Ödeme Sorunu",
        style=discord.ButtonStyle.danger,
        emoji="💳",
        row=4
    )
    async def odeme_sorunu(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "ödeme sorunları"
            ]
        )


    @discord.ui.button(
        label="Müşteri Hiz.",
        style=discord.ButtonStyle.success,
        emoji="📞",
        row=4
    )
    async def musteri_hizmetleri(
        self,
        interaction,
        button
    ):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar[
                "müşteri hizmetleri"
            ]
        )


    @discord.ui.button(
        label="Önceki Sayfa",
        style=discord.ButtonStyle.primary,
        emoji="⬅️",
        row=4
    )
    async def onceki_sayfa(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            content=(
                "🛠️ **DİĞER TEKNİK DESTEKLER - SAYFA 2**\n\n"
                "İhtiyacınız olan teknik destek seçeneğini seçin."
            ),
            view=TeknikMenu2()
        )


    @discord.ui.button(
        label="Ana Menü",
        style=discord.ButtonStyle.primary,
        emoji="🏠",
        row=4
    )
    async def ana_menu(
        self,
        interaction,
        button
    ):

        await interaction.response.edit_message(
            content=ANA_MENU_MESAJI,
            view=AnaMenu()
        )




async def sesli_soruyu_isle(
    message,
    attachment
):

    global sesli_soru_sayisi

    sesli_soru_sayisi += 1

    await message.channel.send(
        "🎤 **Sesli mesaj alındı!**\n\n"
        "⏳ Ses yazıya çevriliyor..."
    )

    dosya_yolu = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".ogg"
        ) as gecici_dosya:

            dosya_yolu = gecici_dosya.name

        await attachment.save(
            dosya_yolu
        )

        soru = await sesi_yaziya_cevir(
            dosya_yolu
        )

        if not soru:

            await message.channel.send(
                "❌ Sesli mesajdan konuşma algılanamadı.\n\n"
                "Lütfen daha net bir sesli mesaj gönder."
            )

            return

        await mesaj_gonder(
            message.channel,
            "🗣️ **Algılanan soru:**\n"
            + soru
        )

        cevap = hazir_cevap_bul(
            soru
        )

        if cevap is None:

            await message.channel.send(
                "🤖 **Ollama düşünüyor...**"
            )

            cevap = await yapay_zeka_cevabi(
                soru
            )

        try:

            soru_kaydet(
                message.author.id,
                str(message.author),
                soru,
                cevap
            )

        except Exception as hata:

            print(
                "⚠️ SESLİ SORU VERİTABANI HATASI:",
                hata
            )

        await mesaj_gonder(
            message.channel,
            "🤖 **Cevap:**\n\n"
            + cevap
        )

    except discord.NotFound:

        await message.channel.send(
            "❌ Ses dosyası artık bulunamıyor."
        )

    except discord.Forbidden:

        await message.channel.send(
            "❌ Ses dosyasını indirmek için gerekli Discord izni yok."
        )

    except Exception as hata:

        print(
            "❌ SESLİ SORU HATASI:",
            hata
        )

        await message.channel.send(
            "❌ Sesli mesaj işlenirken bir hata oluştu."
        )

    finally:

        if (
            dosya_yolu
            and os.path.exists(dosya_yolu)
        ):

            try:

                os.remove(
                    dosya_yolu
                )

            except Exception as hata:

                print(
                    "⚠️ Geçici ses dosyası silinemedi:",
                    hata
                )




@bot.event
async def on_ready():

    print(
        "--------------------------------"
    )

    print(
        "TEKNİK SERVİS BOTU ÇALIŞIYOR!"
    )

    print(
        "Bot:",
        bot.user
    )

    print(
        "Yerel AI:",
        YEREL_AI_MODEL
    )

    try:

        ai_durumu = await ollama_kontrol()

        if ai_durumu:

            print(
                "Ollama: BAĞLI"
            )

            print(
                "Model: HAZIR"
            )

        else:

            print(
                "Ollama: BAĞLANAMADI / MODEL YOK"
            )

    except Exception as hata:

        print(
            "Ollama kontrolünde hata:",
            hata
        )

    try:

        print(
            "Toplam soru:",
            soru_sayisi()
        )

    except Exception as hata:

        print(
            "Veritabanı okunamadı:",
            hata
        )

    print(
        "--------------------------------"
    )




@bot.event
async def on_message(message):

    global yazili_soru_sayisi
    global sesli_soru_sayisi

    if message.author.bot:
        return

    if message.content.startswith(PREFIX):

        await bot.process_commands(
            message
        )

        return

    if message.attachments:

        ses_eki = None

        for ek in message.attachments:

            try:

                if ek.is_voice_message():

                    ses_eki = ek
                    break

            except AttributeError:

                dosya_adi = ek.filename.lower()

                content_type = str(
                    ek.content_type or ""
                ).lower()

                if (
                    content_type.startswith(
                        "audio/"
                    )
                    or dosya_adi.endswith(".mp3")
                    or dosya_adi.endswith(".wav")
                    or dosya_adi.endswith(".ogg")
                    or dosya_adi.endswith(".m4a")
                    or dosya_adi.endswith(".webm")
                    or dosya_adi.endswith(".aac")
                    or dosya_adi.endswith(".flac")
                ):

                    ses_eki = ek
                    break

        if ses_eki is not None:

            if (
                message.author.id
                not in sesli_mesaj_bekleyenler
            ):

                await message.channel.send(
                    "🎤 Sesli mesaj algılandı.\n\n"
                    "Sesli soru kullanmak için önce teknik destek "
                    "menüsündeki **🎤 Sesli Mesaj** butonuna bas."
                )

                return

            sesli_mesaj_bekleyenler.discard(
                message.author.id
            )

            await sesli_soruyu_isle(
                message,
                ses_eki
            )

            return

    soru = message.content.strip()

    if not soru:
        return

    yazili_soru_sayisi += 1

    cevap = hazir_cevap_bul(
        soru
    )

    if cevap is None:

        cevap = await yapay_zeka_cevabi(
            soru
        )

    try:

        soru_kaydet(
            message.author.id,
            str(message.author),
            soru,
            cevap
        )

    except Exception as hata:

        print(
            "⚠️ VERİTABANI HATASI:",
            hata
        )

    try:

        await mesaj_gonder(
            message.channel,
            cevap
        )

    except discord.Forbidden:

        print(
            "❌ Mesaj gönderme izni yok:",
            message.channel
        )

    except Exception as hata:

        print(
            "❌ MESAJ GÖNDERME HATASI:",
            hata
        )




@bot.command()
async def hello(ctx):

    await ctx.send(
        ANA_MENU_MESAJI,
        view=AnaMenu()
    )




@bot.command()
async def yardim(ctx):

    await ctx.send(

        "🛠️ **YARDIM MERKEZİ**\n\n"
        "💬 Sorunu doğrudan yazabilirsin.\n"
        "🤖 Yerel AI'ya soru sorabilirsin.\n"
        "📚 Son sorularını görebilirsin.\n"
        "⭐ Geri bildirim bırakabilirsin.\n"
        "📖 Botun özelliklerini görmek için "
        "**Bot Açıklaması** butonunu kullanabilirsin.\n\n"
        "Menüyü açmak için aşağıdaki butonları "
        "kullanabilirsin.",

        view=AnaMenu()
    )




@bot.command()
async def siparis(ctx):

    await ctx.send(
        sorular[
            "siparişimin durumunu nasıl öğrenebilirim"
        ]
    )


@bot.command()
async def iptal(ctx):

    await ctx.send(
        sorular[
            "bir siparişi nasıl iptal edebilirim"
        ]
    )


@bot.command()
async def hasar(ctx):

    await ctx.send(
        sorular[
            "siparişim hasarlı gelirse ne yapmalıyım"
        ]
    )


@bot.command()
async def teknikdestek(ctx):

    await ctx.send(
        "🔧 **TEKNİK DESTEK**\n\n"
        "📞 Telefon: "
        + TEKNIK_SERVIS_NUMARASI
        + "\n\n"
        "🌐 Web sitesi:\n"
        + TEKNIK_SERVIS_SITESI
    )


@bot.command()
async def teslimat(ctx):

    await ctx.send(
        sorular[
            "teslimat ne kadar sürer"
        ]
    )


@bot.command()
async def istatistik(ctx):

    try:

        toplam = soru_sayisi()

    except Exception:

        toplam = 0

    await ctx.send(

        "📊 **TEKNİK SERVİS İSTATİSTİKLERİ**\n\n"
        "💬 Yazılı sorular: "
        + str(
            yazili_soru_sayisi
        )
        + "\n"
        "🎤 Sesli sorular: "
        + str(
            sesli_soru_sayisi
        )
        + "\n"
        "🤖 AI soruları: "
        + str(
            ai_soru_sayisi
        )
        + "\n"
        "🗄️ Toplam kayıt: "
        + str(
            toplam
        )
    )


@bot.command()
async def gecmis(ctx):

    try:

        gecmis = kullanici_gecmisi(
            ctx.author.id
        )

    except Exception as hata:

        print(
            "GEÇMİŞ HATASI:",
            hata
        )

        await ctx.send(
            "❌ Soru geçmişi alınamadı."
        )

        return

    if not gecmis:

        await ctx.send(
            "📭 Henüz kayıtlı bir soru geçmişin yok."
        )

        return

    mesaj = "📚 **SON 5 SORUN**\n\n"

    for sayac, soru in enumerate(
        gecmis[:5],
        start=1
    ):

        if isinstance(
            soru,
            (tuple, list)
        ):

            metin = str(
                soru[0]
            )

        else:

            metin = str(
                soru
            )

        mesaj += (
            str(sayac)
            + ". "
            + metin
            + "\n"
        )

    await mesaj_gonder(
        ctx.channel,
        mesaj
    )


@bot.command()
async def ai(
    ctx,
    *,
    soru=None
):

    if soru is None or not soru.strip():

        await ctx.send(

            "🤖 Bir soru yazmalısın.\n\n"
            "Örnek:\n"
            f"`{PREFIX}ai Bilgisayarım neden açılmıyor?`"
        )

        return

    try:

        async with ctx.typing():

            cevap = await yapay_zeka_cevabi(
                soru
            )

        try:

            soru_kaydet(
                ctx.author.id,
                str(ctx.author),
                soru,
                cevap
            )

        except Exception as hata:

            print(
                "VERİTABANI HATASI:",
                hata
            )

        await mesaj_gonder(
            ctx.channel,
            cevap
        )

    except Exception as hata:

        print(
            "❌ YEREL AI HATASI:",
            hata
        )

        await ctx.send(
            "❌ Yerel AI çalıştırılamadı."
        )


@bot.command()
async def destek(ctx):

    await ctx.send(

        "🎫 **TEKNİK SERVİS DESTEK MERKEZİ**\n\n"
        "Sorunuzu buraya yazabilirsiniz.\n\n"
        "🤖 Hazır cevap bulunamazsa yerel AI yardımcı olur.\n"
        "📞 Teknik destek: "
        + TEKNIK_SERVIS_NUMARASI
        + "\n\n"
        "Aşağıdaki menüyü kullanabilirsiniz.",

        view=AnaMenu()
    )


@bot.command()
async def telefon(ctx):

    await ctx.send(

        "📞 **TEKNİK SERVİS TELEFON NUMARASI**\n\n"
        + TEKNIK_SERVIS_NUMARASI
        + "\n\n"
        "⚠️ Bu kodda kullanılan numara örnektir."
    )


@bot.command()
async def site(ctx):

    await ctx.send(

        "🌐 **TEKNİK SERVİS WEB SİTESİ**\n\n"
        + TEKNIK_SERVIS_SITESI
    )


@bot.command()
async def hakkinda(ctx):

    await ctx.send(
        ANA_MENU_MESAJI,
        view=AnaMenu()
    )


@bot.command()
async def ping(ctx):

    gecikme = round(
        bot.latency * 1000
    )

    await ctx.send(

        "🏓 **Pong!**\n\n"
        "📡 Bot gecikmesi: "
        + str(
            gecikme
        )
        + " ms"
    )


@bot.command()
@commands.has_permissions(
    administrator=True
)
async def yonetici(ctx):

    try:

        toplam = soru_sayisi()

    except Exception:

        toplam = 0

    await ctx.send(

        "🔐 **YÖNETİCİ PANELİ**\n\n"
        "📊 Toplam soru: "
        + str(
            toplam
        )
        + "\n"
        "💬 Yazılı soru: "
        + str(
            yazili_soru_sayisi
        )
        + "\n"
        "🎤 Sesli soru: "
        + str(
            sesli_soru_sayisi
        )
        + "\n"
        "🤖 AI sorusu: "
        + str(
            ai_soru_sayisi
        )
    )




@bot.command()
async def telefonsorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "telefon sorunları"
        ]
    )


@bot.command()
async def bilgisayarsorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "bilgisayar sorunları"
        ]
    )


@bot.command()
async def wifisorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "wifi sorunları"
        ]
    )


@bot.command()
async def sarj(ctx):

    await ctx.send(
        yeni_cevaplar[
            "şarj sorunları"
        ]
    )


@bot.command()
async def pil(ctx):

    await ctx.send(
        yeni_cevaplar[
            "pil batarya"
        ]
    )


@bot.command()
async def ekransorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "ekran sorunları"
        ]
    )


@bot.command()
async def klavyesorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "klavye sorunları"
        ]
    )


@bot.command()
async def mousesorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "mouse sorunları"
        ]
    )


@bot.command()
async def yazicisorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "yazıcı sorunları"
        ]
    )


@bot.command()
async def depolamasorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "depolama sorunları"
        ]
    )


@bot.command()
async def ses(ctx):

    await ctx.send(
        yeni_cevaplar[
            "ses sorunları"
        ]
    )


@bot.command()
async def kamera(ctx):

    await ctx.send(
        yeni_cevaplar[
            "kamera sorunları"
        ]
    )


@bot.command()
async def bluetooth(ctx):

    await ctx.send(
        yeni_cevaplar[
            "bluetooth sorunları"
        ]
    )


@bot.command()
async def guncelleme(ctx):

    await ctx.send(
        yeni_cevaplar[
            "güncelleme sorunları"
        ]
    )


@bot.command()
async def guvenlik(ctx):

    await ctx.send(
        yeni_cevaplar[
            "güvenlik sorunları"
        ]
    )


@bot.command()
async def hesapguvenligi(ctx):

    await ctx.send(
        yeni_cevaplar[
            "hesap güvenliği"
        ]
    )


@bot.command()
async def teslimalma(ctx):

    await ctx.send(
        yeni_cevaplar[
            "teslim alma"
        ]
    )


@bot.command()
async def faturasorun(ctx):

    await ctx.send(
        yeni_cevaplar[
            "fatura sorunları"
        ]
    )


@bot.command()
async def odemes(ctx):

    await ctx.send(
        yeni_cevaplar[
            "ödeme sorunları"
        ]
    )


@bot.command()
async def musterihizmetleri(ctx):

    await ctx.send(
        yeni_cevaplar[
            "müşteri hizmetleri"
        ]
    )




@yonetici.error
async def yonetici_hata(
    ctx,
    hata
):

    if isinstance(
        hata,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Bu komutu kullanmak için "
            "sunucu yöneticisi olmalısın."
        )

        return

    print(
        "YÖNETİCİ KOMUT HATASI:",
        hata
    )




@bot.event
async def on_command_error(
    ctx,
    hata
):

    if hasattr(
        ctx.command,
        "on_error"
    ):

        return

    if isinstance(
        hata,
        commands.CommandNotFound
    ):

        await ctx.send(
            "❓ Böyle bir komut bulunamadı.\n"
            f"`{PREFIX}hello` yazarak menüyü açabilirsin."
        )

        return

    if isinstance(
        hata,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Komutu eksik kullandın."
        )

        return

    if isinstance(
        hata,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ Bu komutu kullanmak için "
            "gerekli yetkiye sahip değilsin."
        )

        return

    if isinstance(
        hata,
        commands.BotMissingPermissions
    ):

        await ctx.send(
            "❌ Botun bu işlem için gerekli Discord "
            "yetkileri yok."
        )

        return

    if isinstance(
        hata,
        commands.CommandOnCooldown
    ):

        await ctx.send(
            "⏳ Bu komutu tekrar kullanmadan önce "
            f"{hata.retry_after:.1f} saniye beklemelisin."
        )

        return

    print(
        "❌ KOMUT HATASI:",
        hata
    )

try:

    veritabani_olustur()

    print(
        "🗄️ Veritabanı hazır."
    )

except Exception as hata:

    print(
        "❌ VERİTABANI BAŞLATMA HATASI:",
        hata
    )




if not DISCORD_TOKEN:

    print(
        "❌ HATA: config.py dosyasına Discord tokeni "
        "eklenmemiş."
    )

else:

    print(
        "Discord botuna bağlanılıyor..."
    )

    try:

        bot.run(
            "TOKEN"
        )

    except discord.LoginFailure:

        print(
            "❌ Discord token geçersiz."
        )

        print(
            "Discord Developer Portal'dan bot tokenini "
            "yenileyip config.py içine doğru şekilde ekleyin."
        )

    except discord.PrivilegedIntentsRequired:

        print(
            "❌ Gerekli Privileged Intent izinleri açık değil."
        )

        print(
            "Discord Developer Portal > Bot > "
            "Privileged Gateway Intents bölümünü kontrol edin."
        )

    except Exception as hata:

        print(
            "❌ BOT BAŞLATMA HATASI:",
            hata
        )





        
    



   
        







