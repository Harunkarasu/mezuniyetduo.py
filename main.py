import discord
from discord.ext import commands

import asyncio
import requests


# ==================================================
# AYARLAR VE VERİTABANI
# ==================================================

from config import DISCORD_TOKEN
from config import PREFIX

from database import veritabani_olustur
from database import soru_kaydet
from database import soru_sayisi
from database import kullanici_gecmisi


# ==================================================
# TEKNİK SERVİS BİLGİLERİ
# ==================================================

TEKNIK_SERVIS_SITESI = "https://www.trendyol.com/"
TEKNIK_SERVIS_NUMARASI = "0850 540 600 025"


# ==================================================
# YEREL AI AYARLARI
# ==================================================

YEREL_AI_MODEL = "gemma3:1b"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"


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


# ==================================================
# İSTATİSTİKLER
# ==================================================

yazili_soru_sayisi = 0
sesli_soru_sayisi = 0
ai_soru_sayisi = 0


# ==================================================
# BOT TANITIMI
# ==================================================

BOT_ACIKLAMASI = (
    "🛠️ **TEKNİK SERVİS ASİSTANI**\n\n"

    "Merhaba! Ben teknik servis destek botuyum. 🤖\n\n"

    "Size şu konularda yardımcı olabilirim:\n\n"

    "🛒 Alışveriş\n"
    "📦 Sipariş durumu\n"
    "❌ Sipariş iptali\n"
    "⚠️ Hasarlı ürün\n"
    "🔧 Teknik destek\n"
    "🚚 Teslimat\n"
    "↩️ İade\n"
    "🛡️ Garanti\n"
    "💳 Ödeme\n"
    "🧾 Fatura\n"
    "👤 Hesap\n"
    "🔑 Şifre\n"
    "💻 Bilgisayar\n"
    "📱 Telefon ve tablet\n"
    "🌐 İnternet\n"
    "🖨️ Yazıcı\n"
    "🔋 Batarya\n"
    "💾 Depolama\n"
    "🖥️ Ekran\n"
    "⌨️ Klavye\n"
    "🖱️ Mouse\n"
    "🔌 Şarj\n"
    "🔊 Ses\n"
    "📷 Kamera\n"
    "📶 Bluetooth\n"
    "🔄 Güncelleme\n"
    "🛡️ Güvenlik\n"
    "🔐 Hesap güvenliği\n"
    "📦 Teslim alma\n"
    "🤖 Yerel yapay zekâ\n"
    "📚 Soru geçmişi\n"
    "📊 İstatistikler\n"
    "⭐ Geri bildirim\n\n"

    "Bir konu seçmek için aşağıdaki butonları kullanabilirsin."
)


# ==================================================
# SIKÇA SORULAN SORULAR
# ==================================================

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


# ==================================================
# YENİ 20 TEKNİK DESTEK CEVABI
# ==================================================

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
        soru = soru.replace(karakter, "")

    soru = " ".join(soru.split())

    return soru


# ==================================================
# HAZIR CEVAP BUL
# ==================================================

def hazir_cevap_bul(soru):

    soru = soruyu_temizle(soru)

    if not soru:
        return None

    for anahtar, cevap in sorular.items():

        temiz_anahtar = soruyu_temizle(anahtar)

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
                model.get("name", "")
            )

            bulunan_modeller.append(
                isim
            )

            if (
                isim == YEREL_AI_MODEL
                or isim.startswith(YEREL_AI_MODEL + ":")
            ):
                return True

        print(
            "⚠️ Ollama çalışıyor fakat model bulunamadı:",
            YEREL_AI_MODEL
        )

        if bulunan_modeller:

            print(
                "📦 Yüklü modeller:",
                ", ".join(bulunan_modeller)
            )

        return False

    except requests.exceptions.ConnectionError:

        print("❌ Ollama çalışmıyor.")

        return False

    except requests.exceptions.Timeout:

        print("⏳ Ollama kontrolü zaman aşımına uğradı.")

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


# ==================================================
# YEREL AI
# ==================================================

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
            veri.get("response", "")
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


# ==================================================
# MESAJI PARÇALA
# ==================================================

def mesaj_parcalari(mesaj, maksimum=1900):

    if not mesaj:
        return [""]

    parcalar = []

    while len(mesaj) > maksimum:

        bolum = mesaj[:maksimum]

        son_bosluk = bolum.rfind(" ")

        if son_bosluk > 500:
            bolum = bolum[:son_bosluk]

        parcalar.append(bolum)

        mesaj = mesaj[len(bolum):].lstrip()

    if mesaj:
        parcalar.append(mesaj)

    return parcalar


async def mesaj_gonder(channel, mesaj, **kwargs):

    for parca in mesaj_parcalari(mesaj):

        await channel.send(
            parca,
            **kwargs
        )


# ==================================================
# GERİ BİLDİRİM
# ==================================================

class GeriBildirimModal(discord.ui.Modal):

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

        self.add_item(self.puan)
        self.add_item(self.yorum)

    async def on_submit(self, interaction):

        puan = str(self.puan.value).strip()
        yorum = str(self.yorum.value).strip()

        if puan not in ["1", "2", "3", "4", "5"]:

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


# ==================================================
# AI SORU MODALI
# ==================================================

class AIsoruModal(discord.ui.Modal):

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

        self.add_item(self.soru)

    async def on_submit(self, interaction):

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


# ==================================================
# ANA MENÜ
# ==================================================

class AnaMenu(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    async def cevap_ver(self, interaction, cevap):

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


    # ==================================================
    # MEVCUT BUTONLAR
    # ==================================================

    @discord.ui.button(
        label="Alışveriş",
        style=discord.ButtonStyle.primary,
        emoji="🛒",
        row=0
    )
    async def alisveris(self, interaction, button):

        await self.cevap_ver(
            interaction,
            sorular["nasıl alışveriş yapabilirim"]
        )


    @discord.ui.button(
        label="Sipariş Durumu",
        style=discord.ButtonStyle.primary,
        emoji="📦",
        row=0
    )
    async def siparis_durumu(self, interaction, button):

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
    async def siparis_iptal(self, interaction, button):

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
    async def hasarli(self, interaction, button):

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
    async def teknik_destek(self, interaction, button):

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
    async def teslimat(self, interaction, button):

        await self.cevap_ver(
            interaction,
            sorular["teslimat ne kadar sürer"]
        )


    @discord.ui.button(
        label="İade",
        style=discord.ButtonStyle.secondary,
        emoji="↩️",
        row=1
    )
    async def iade(self, interaction, button):

        await self.cevap_ver(
            interaction,
            sorular["iade nasıl yapılır"]
        )


    @discord.ui.button(
        label="Garanti",
        style=discord.ButtonStyle.secondary,
        emoji="🛡️",
        row=1
    )
    async def garanti(self, interaction, button):

        await self.cevap_ver(
            interaction,
            sorular["garanti süresi ne kadar"]
        )


    @discord.ui.button(
        label="Ödeme",
        style=discord.ButtonStyle.secondary,
        emoji="💳",
        row=2
    )
    async def odeme(self, interaction, button):

        await self.cevap_ver(
            interaction,
            sorular["ödeme yöntemleri"]
        )


    @discord.ui.button(
        label="Fatura",
        style=discord.ButtonStyle.secondary,
        emoji="🧾",
        row=2
    )
    async def fatura(self, interaction, button):

        await self.cevap_ver(
            interaction,
            sorular["fatura nasıl alınır"]
        )


    @discord.ui.button(
        label="Soru Geçmişim",
        style=discord.ButtonStyle.primary,
        emoji="📚",
        row=2
    )
    async def gecmis(self, interaction, button):

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

            if isinstance(soru, (tuple, list)):
                metin = str(soru[0])
            else:
                metin = str(soru)

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
    async def istatistik(self, interaction, button):

        try:
            toplam = soru_sayisi()
        except Exception:
            toplam = 0

        await interaction.response.send_message(

            "📊 **TEKNİK SERVİS İSTATİSTİKLERİ**\n\n"
            "💬 Yazılı sorular: "
            + str(yazili_soru_sayisi)
            + "\n"
            "🎤 Sesli sorular: "
            + str(sesli_soru_sayisi)
            + "\n"
            "🤖 AI soruları: "
            + str(ai_soru_sayisi)
            + "\n"
            "🗄️ Toplam kayıt: "
            + str(toplam),

            ephemeral=True
        )


    @discord.ui.button(
        label="Yapay Zekâ",
        style=discord.ButtonStyle.success,
        emoji="🤖",
        row=3
    )
    async def ai(self, interaction, button):

        await interaction.response.send_modal(
            AIsoruModal()
        )


    @discord.ui.button(
        label="Geri Bildirim",
        style=discord.ButtonStyle.secondary,
        emoji="⭐",
        row=4
    )
    async def geri_bildirim(self, interaction, button):

        await interaction.response.send_modal(
            GeriBildirimModal()
        )


    @discord.ui.button(
        label="Yönetici",
        style=discord.ButtonStyle.danger,
        emoji="🔐",
        row=4
    )
    async def yonetici_buton(self, interaction, button):

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
            + str(toplam)
            + "\n"
            "💬 Yazılı soru: "
            + str(yazili_soru_sayisi)
            + "\n"
            "🎤 Sesli soru: "
            + str(sesli_soru_sayisi)
            + "\n"
            "🤖 AI sorusu: "
            + str(ai_soru_sayisi),

            ephemeral=True
        )


    @discord.ui.button(
        label="Ana Menü",
        style=discord.ButtonStyle.primary,
        emoji="🏠",
        row=4
    )
    async def ana_menu(self, interaction, button):

        await interaction.response.edit_message(
            content=BOT_ACIKLAMASI,
            view=AnaMenu()
        )


    # ==================================================
    # YENİ DESTEKLER MENÜSÜ
    # ==================================================

    @discord.ui.button(
        label="Diğer Destekler",
        style=discord.ButtonStyle.success,
        emoji="🛠️",
        row=4
    )
    async def diger_destekler(self, interaction, button):

        await interaction.response.edit_message(
            content=(
                "🛠️ **DİĞER TEKNİK DESTEKLER - SAYFA 2**\n\n"
                "İhtiyacınız olan teknik destek seçeneğini seçin."
            ),
            view=TeknikMenu2()
        )


# ==================================================
# TEKNİK DESTEK SAYFA 2
# ==================================================

class TeknikMenu2(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    async def cevap_ver(self, interaction, cevap):

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
    async def telefon_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["telefon sorunları"]
        )


    @discord.ui.button(
        label="Bilgisayar",
        style=discord.ButtonStyle.primary,
        emoji="💻",
        row=0
    )
    async def bilgisayar_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["bilgisayar sorunları"]
        )


    @discord.ui.button(
        label="Wi-Fi",
        style=discord.ButtonStyle.primary,
        emoji="📡",
        row=1
    )
    async def wifi_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["wifi sorunları"]
        )


    @discord.ui.button(
        label="Şarj",
        style=discord.ButtonStyle.primary,
        emoji="🔌",
        row=1
    )
    async def sarj_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["şarj sorunları"]
        )


    @discord.ui.button(
        label="Pil",
        style=discord.ButtonStyle.primary,
        emoji="🔋",
        row=2
    )
    async def pil_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["pil batarya"]
        )


    @discord.ui.button(
        label="Ekran",
        style=discord.ButtonStyle.secondary,
        emoji="🖥️",
        row=2
    )
    async def ekran_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["ekran sorunları"]
        )


    @discord.ui.button(
        label="Klavye",
        style=discord.ButtonStyle.secondary,
        emoji="⌨️",
        row=3
    )
    async def klavye_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["klavye sorunları"]
        )


    @discord.ui.button(
        label="Mouse",
        style=discord.ButtonStyle.secondary,
        emoji="🖱️",
        row=3
    )
    async def mouse_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["mouse sorunları"]
        )


    @discord.ui.button(
        label="Yazıcı",
        style=discord.ButtonStyle.secondary,
        emoji="🖨️",
        row=4
    )
    async def yazici_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["yazıcı sorunları"]
        )


    @discord.ui.button(
        label="Depolama",
        style=discord.ButtonStyle.secondary,
        emoji="💾",
        row=4
    )
    async def depolama_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["depolama sorunları"]
        )


    @discord.ui.button(
        label="Sonraki Sayfa",
        style=discord.ButtonStyle.success,
        emoji="➡️",
        row=4
    )
    async def sonraki_sayfa(self, interaction, button):

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
    async def ana_menu(self, interaction, button):

        await interaction.response.edit_message(
            content=BOT_ACIKLAMASI,
            view=AnaMenu()
        )


# ==================================================
# TEKNİK DESTEK SAYFA 3
# ==================================================

class TeknikMenu3(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=600
        )

    async def cevap_ver(self, interaction, cevap):

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
    async def ses_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["ses sorunları"]
        )


    @discord.ui.button(
        label="Kamera",
        style=discord.ButtonStyle.secondary,
        emoji="📷",
        row=0
    )
    async def kamera_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["kamera sorunları"]
        )


    @discord.ui.button(
        label="Bluetooth",
        style=discord.ButtonStyle.secondary,
        emoji="📶",
        row=1
    )
    async def bluetooth_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["bluetooth sorunları"]
        )


    @discord.ui.button(
        label="Güncelleme",
        style=discord.ButtonStyle.secondary,
        emoji="🔄",
        row=1
    )
    async def guncelleme_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["güncelleme sorunları"]
        )


    @discord.ui.button(
        label="Güvenlik",
        style=discord.ButtonStyle.danger,
        emoji="🛡️",
        row=2
    )
    async def guvenlik_sorunlari(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["güvenlik sorunları"]
        )


    @discord.ui.button(
        label="Hesap Güvenliği",
        style=discord.ButtonStyle.danger,
        emoji="🔐",
        row=2
    )
    async def hesap_guvenligi(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["hesap güvenliği"]
        )


    @discord.ui.button(
        label="Teslim Alma",
        style=discord.ButtonStyle.primary,
        emoji="📦",
        row=3
    )
    async def teslim_alma(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["teslim alma"]
        )


    @discord.ui.button(
        label="Fatura Sorunu",
        style=discord.ButtonStyle.primary,
        emoji="🧾",
        row=3
    )
    async def fatura_sorunu(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["fatura sorunları"]
        )


    @discord.ui.button(
        label="Ödeme Sorunu",
        style=discord.ButtonStyle.danger,
        emoji="💳",
        row=4
    )
    async def odeme_sorunu(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["ödeme sorunları"]
        )


    @discord.ui.button(
        label="Müşteri Hiz.",
        style=discord.ButtonStyle.success,
        emoji="📞",
        row=4
    )
    async def musteri_hizmetleri(self, interaction, button):

        await self.cevap_ver(
            interaction,
            yeni_cevaplar["müşteri hizmetleri"]
        )


    @discord.ui.button(
        label="Önceki Sayfa",
        style=discord.ButtonStyle.primary,
        emoji="⬅️",
        row=4
    )
    async def onceki_sayfa(self, interaction, button):

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
    async def ana_menu(self, interaction, button):

        await interaction.response.edit_message(
            content=BOT_ACIKLAMASI,
            view=AnaMenu()
        )


# ==================================================
# BOT HAZIR
# ==================================================

@bot.event
async def on_ready():

    print("--------------------------------")
    print("TEKNİK SERVİS BOTU ÇALIŞIYOR!")
    print("Bot:", bot.user)
    print("Yerel AI:", YEREL_AI_MODEL)

    try:

        ai_durumu = await ollama_kontrol()

        if ai_durumu:

            print("Ollama: BAĞLI")
            print("Model: HAZIR")

        else:

            print("Ollama: BAĞLANAMADI / MODEL YOK")

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

    print("--------------------------------")


# ==================================================
# MESAJ SİSTEMİ
# ==================================================

@bot.event
async def on_message(message):

    global yazili_soru_sayisi

    if message.author.bot:
        return

    if message.content.startswith(PREFIX):

        await bot.process_commands(
            message
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


# ==================================================
# !HELLO
# ==================================================

@bot.command()
async def hello(ctx):

    await ctx.send(
        BOT_ACIKLAMASI,
        view=AnaMenu()
    )


# ==================================================
# !YARDIM
# ==================================================

@bot.command()
async def yardim(ctx):

    await ctx.send(

        "🛠️ **YARDIM MERKEZİ**\n\n"
        "💬 Sorunu doğrudan yazabilirsin.\n"
        "🤖 Yerel AI'ya soru sorabilirsin.\n"
        "📚 Son sorularını görebilirsin.\n"
        "⭐ Geri bildirim bırakabilirsin.\n\n"
        "Menüyü açmak için aşağıdaki butonları "
        "kullanabilirsin.",

        view=AnaMenu()
    )


# ==================================================
# MEVCUT KOMUTLAR
# ==================================================

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
        sorular["teslimat ne kadar sürer"]
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
        + str(yazili_soru_sayisi)
        + "\n"
        "🎤 Sesli sorular: "
        + str(sesli_soru_sayisi)
        + "\n"
        "🤖 AI soruları: "
        + str(ai_soru_sayisi)
        + "\n"
        "🗄️ Toplam kayıt: "
        + str(toplam)
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

        if isinstance(soru, (tuple, list)):
            metin = str(soru[0])
        else:
            metin = str(soru)

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
async def ai(ctx, *, soru=None):

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

        "🛠️ **TEKNİK SERVİS ASİSTANI**\n\n"
        "📚 Hazır cevap sistemi\n"
        "🤖 Yerel yapay zekâ\n"
        "🗄️ Veritabanı sistemi\n"
        "📊 İstatistik sistemi\n"
        "⭐ Geri bildirim sistemi\n"
        "🔐 Yönetici sistemi\n"
        "🌐 Web sitesi bağlantısı\n"
        "📞 Teknik destek telefonu"
    )


@bot.command()
async def ping(ctx):

    gecikme = round(
        bot.latency * 1000
    )

    await ctx.send(

        "🏓 **Pong!**\n\n"
        "📡 Bot gecikmesi: "
        + str(gecikme)
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
        + str(toplam)
        + "\n"
        "💬 Yazılı soru: "
        + str(yazili_soru_sayisi)
        + "\n"
        "🎤 Sesli soru: "
        + str(sesli_soru_sayisi)
        + "\n"
        "🤖 AI sorusu: "
        + str(ai_soru_sayisi)
    )


# ==================================================
# YENİ 20 KOMUT
# ==================================================

@bot.command()
async def telefonsorun(ctx):

    await ctx.send(
        yeni_cevaplar["telefon sorunları"]
    )


@bot.command()
async def bilgisayarsorun(ctx):

    await ctx.send(
        yeni_cevaplar["bilgisayar sorunları"]
    )


@bot.command()
async def wifisorun(ctx):

    await ctx.send(
        yeni_cevaplar["wifi sorunları"]
    )


@bot.command()
async def sarj(ctx):

    await ctx.send(
        yeni_cevaplar["şarj sorunları"]
    )


@bot.command()
async def pil(ctx):

    await ctx.send(
        yeni_cevaplar["pil batarya"]
    )


@bot.command()
async def ekransorun(ctx):

    await ctx.send(
        yeni_cevaplar["ekran sorunları"]
    )


@bot.command()
async def klavyesorun(ctx):

    await ctx.send(
        yeni_cevaplar["klavye sorunları"]
    )


@bot.command()
async def mousesorun(ctx):

    await ctx.send(
        yeni_cevaplar["mouse sorunları"]
    )


@bot.command()
async def yazicisorun(ctx):

    await ctx.send(
        yeni_cevaplar["yazıcı sorunları"]
    )


@bot.command()
async def depolamasorun(ctx):

    await ctx.send(
        yeni_cevaplar["depolama sorunları"]
    )


@bot.command()
async def ses(ctx):

    await ctx.send(
        yeni_cevaplar["ses sorunları"]
    )


@bot.command()
async def kamera(ctx):

    await ctx.send(
        yeni_cevaplar["kamera sorunları"]
    )


@bot.command()
async def bluetooth(ctx):

    await ctx.send(
        yeni_cevaplar["bluetooth sorunları"]
    )


@bot.command()
async def guncelleme(ctx):

    await ctx.send(
        yeni_cevaplar["güncelleme sorunları"]
    )


@bot.command()
async def guvenlik(ctx):

    await ctx.send(
        yeni_cevaplar["güvenlik sorunları"]
    )


@bot.command()
async def hesapguvenligi(ctx):

    await ctx.send(
        yeni_cevaplar["hesap güvenliği"]
    )


@bot.command()
async def teslimalma(ctx):

    await ctx.send(
        yeni_cevaplar["teslim alma"]
    )


@bot.command()
async def faturasorun(ctx):

    await ctx.send(
        yeni_cevaplar["fatura sorunları"]
    )


@bot.command()
async def odemes(ctx):

    await ctx.send(
        yeni_cevaplar["ödeme sorunları"]
    )


@bot.command()
async def musterihizmetleri(ctx):

    await ctx.send(
        yeni_cevaplar["müşteri hizmetleri"]
    )


# ==================================================
# YÖNETİCİ HATA
# ==================================================

@yonetici.error
async def yonetici_hata(ctx, hata):

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


# ==================================================
# GENEL KOMUT HATASI
# ==================================================

@bot.event
async def on_command_error(ctx, hata):

    if hasattr(ctx.command, "on_error"):
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


# ==================================================
# VERİTABANI
# ==================================================

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


# ==================================================
# TOKEN KONTROLÜ
# ==================================================

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
            DISCORD_TOKEN
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

# Discord botunu başlat.
bot.run("TOKEN")


        
    



   
        







