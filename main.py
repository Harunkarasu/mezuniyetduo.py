
import discord
from discord.ext import commands
from openai import OpenAI

import os
import time


from config import DISCORD_TOKEN
from config import OPENAI_API_KEY
from config import OPENAI_MODEL
from config import PREFIX

from database import veritabani_olustur
from database import soru_kaydet
from database import soru_sayisi
from database import kullanici_gecmisi


# --------------------------------------------------
# DISCORD AYARLARI
# --------------------------------------------------

# Discord izinlerini oluşturuyoruz
intents = discord.Intents.default()

# Botun mesajları okuyabilmesini sağlıyoruz
intents.message_content = True


# Discord botunu oluşturuyoruz
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents
)


# --------------------------------------------------
# OPENAI AYARLARI
# --------------------------------------------------

# OpenAI bağlantısını oluşturuyoruz
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)


# --------------------------------------------------
# İSTATİSTİKLER
# --------------------------------------------------

# Yazılı soru sayısını tutar
yazili_soru_sayisi = 0

# Sesli soru sayısını tutar
sesli_soru_sayisi = 0

# Yapay zekâya gönderilen soru sayısını tutar
ai_soru_sayisi = 0


# --------------------------------------------------
# SIKÇA SORULAN SORULAR
# --------------------------------------------------

sorular = {

    "nasıl alışveriş yapabilirim":
        "Alışveriş yapmak için, ilgilendiğiniz ürünü seçip "
        "\"Alışveriş Sepetine Ekle\" butonuna tıklayın. "
        "Ardından Alışveriş Sepetine gidin ve satın alma işlemini "
        "tamamlamak için yönergeleri takip edin.",

    "siparişimin durumunu nasıl öğrenebilirim":
        "Siparişinizin durumunu öğrenmek için internet sitemizdeki "
        "hesabınıza giriş yapın ve \"Siparişlerim\" bölümüne gidin. "
        "Orada, siparişinizin mevcut durumunu görebilirsiniz.",

    "bir siparişi nasıl iptal edebilirim":
        "Siparişinizi iptal etmek istiyorsanız, lütfen en kısa sürede "
        "müşteri hizmetlerimizle iletişime geçin. Siparişiniz "
        "gönderilmeden önce iptal işleminizde size yardımcı olmaya "
        "çalışacağız.",

    "siparişim hasarlı gelirse ne yapmalıyım":
        "Hasarlı bir ürün aldıysanız, lütfen hemen müşteri "
        "hizmetlerimizle iletişime geçin ve hasarın fotoğraflarını "
        "sağlayın. Ürünü değiştirmeniz veya iade etmeniz konusunda "
        "size yardımcı olacağız.",

    "teknik destekle nasıl iletişime geçebilirim":
        "Teknik destekle, internet sitemizde yer alan telefon "
        "numarasını arayarak iletişime geçebilirsiniz. Alternatif "
        "olarak, sohbet robotumuz üzerinden de bizimle iletişim "
        "kurabilirsiniz.",

    "ödeme sırasında teslimat yöntemini değiştirebilir miyim":
        "Evet, ödeme sayfasında teslimat bilgilerini değiştirebilirsiniz. "
        "Kullanılabilir teslimat yöntemleri ve şartları orada "
        "listelenecektir."
}


# --------------------------------------------------
# SSS ALTERNATİF KELİMELERİ
# --------------------------------------------------

# Kullanıcının farklı şekilde sorduğu soruları yakalamaya çalışır
sss_anahtarlari = {

    "nasıl alışveriş yapabilirim": [
        "alışveriş",
        "satın alma",
        "ürün nasıl alırım",
        "nasıl satın alırım",
        "ürün satın"
    ],

    "siparişimin durumunu nasıl öğrenebilirim": [
        "siparişim nerede",
        "sipariş durum",
        "siparişimi takip",
        "kargom nerede",
        "siparişimi nasıl takip"
    ],

    "bir siparişi nasıl iptal edebilirim": [
        "sipariş iptal",
        "siparişi iptal",
        "siparişimi iptal",
        "ürünü iptal"
    ],

    "siparişim hasarlı gelirse ne yapmalıyım": [
        "hasarlı ürün",
        "ürün hasarlı",
        "ürün kırık",
        "sipariş hasarlı",
        "kırık geldi"
    ],

    "teknik destekle nasıl iletişime geçebilirim": [
        "teknik destek",
        "destek ekibi",
        "destekle iletişim",
        "teknik servis",
        "servise nasıl ulaşırım"
    ],

    "ödeme sırasında teslimat yöntemini değiştirebilir miyim": [
        "teslimat yöntemi",
        "teslimat değiştirme",
        "kargo yöntemini değiştir",
        "teslimatı değiştirebilir",
        "kargo seçeneği"
    ]
}


# --------------------------------------------------
# HAZIR CEVAP BULMA
# --------------------------------------------------

def hazir_cevap_bul(soru):

    # Soruyu küçük harfe çeviriyoruz
    soru = soru.lower()

    # Türkçe karakterleri de kontrol ediyoruz
    soru = soru.strip()


    # Önce doğrudan soruları kontrol ediyoruz
    for anahtar in sorular:

        if anahtar in soru:

            return sorular[anahtar]


    # Daha sonra alternatif kelimeleri kontrol ediyoruz
    for anahtar in sss_anahtarlari:

        for kelime in sss_anahtarlari[anahtar]:

            if kelime in soru:

                return sorular[anahtar]


    # Cevap bulunamadı
    return None


# --------------------------------------------------
# YAPAY ZEKA
# --------------------------------------------------

def yapay_zeka_cevabi(soru):

    global ai_soru_sayisi

    # Yapay zekâ soru sayısını artırıyoruz
    ai_soru_sayisi += 1


    # OpenAI'dan cevap istiyoruz
    cevap = openai_client.responses.create(

        model=OPENAI_MODEL,

        input=[
            {
                "role": "system",
                "content":
                    "Sen bir teknik servis botusun. "
                    "Türkçe cevap ver. "
                    "Kısa, anlaşılır ve yardımcı ol. "
                    "Bilmediğin şirket bilgilerini uydurma."
            },

            {
                "role": "user",
                "content": soru
            }
        ]
    )


    # Cevabı geri döndürüyoruz
    return cevap.output_text


# --------------------------------------------------
# SESLİ MESAJI YAZIYA ÇEVİRME
# --------------------------------------------------

def sesli_mesaji_yaziya_cevir(dosya_adi):

    # Ses dosyasını açıyoruz
    with open(dosya_adi, "rb") as ses_dosyasi:

        # OpenAI transkripsiyon sistemini kullanıyoruz
        cevap = openai_client.audio.transcriptions.create(

            model="gpt-4o-mini-transcribe",

            file=ses_dosyasi
        )


    # Yazıya çevrilmiş metni döndürüyoruz
    return cevap.text


# --------------------------------------------------
# SSS BUTONLARI
# --------------------------------------------------

class SSSView(discord.ui.View):

    # Butonların 10 dakika çalışmasını sağlıyoruz
    def __init__(self):

        super().__init__(
            timeout=600
        )


    # ----------------------------------------------
    # ALIŞVERİŞ
    # ----------------------------------------------

    @discord.ui.button(
        label="Alışveriş",
        style=discord.ButtonStyle.primary,
        emoji="🛒"
    )
    async def alisveris(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "nasıl alışveriş yapabilirim"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # SİPARİŞ DURUMU
    # ----------------------------------------------

    @discord.ui.button(
        label="Sipariş Durumu",
        style=discord.ButtonStyle.primary,
        emoji="📦"
    )
    async def siparis_durumu(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "siparişimin durumunu nasıl öğrenebilirim"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # SİPARİŞ İPTALİ
    # ----------------------------------------------

    @discord.ui.button(
        label="Sipariş İptali",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def siparis_iptal(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "bir siparişi nasıl iptal edebilirim"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # HASARLI ÜRÜN
    # ----------------------------------------------

    @discord.ui.button(
        label="Hasarlı Ürün",
        style=discord.ButtonStyle.danger,
        emoji="⚠️"
    )
    async def hasarli_siparis(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "siparişim hasarlı gelirse ne yapmalıyım"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # TEKNİK DESTEK
    # ----------------------------------------------

    @discord.ui.button(
        label="Teknik Destek",
        style=discord.ButtonStyle.success,
        emoji="🔧"
    )
    async def teknik_destek(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "teknik destekle nasıl iletişime geçebilirim"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # TESLİMAT
    # ----------------------------------------------

    @discord.ui.button(
        label="Teslimat",
        style=discord.ButtonStyle.secondary,
        emoji="🚚"
    )
    async def teslimat_butonu(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "ödeme sırasında teslimat yöntemini değiştirebilir miyim"
            ],

            ephemeral=True
        )


# --------------------------------------------------
# BOT HAZIR
# --------------------------------------------------

@bot.event
async def on_ready():

    print("--------------------------------")
    print("TEKNİK SERVİS BOTU ÇALIŞIYOR!")
    print("Bot:", bot.user)
    print("Toplam soru:", soru_sayisi())
    print("--------------------------------")


# --------------------------------------------------
# MESAJ SİSTEMİ
# --------------------------------------------------

@bot.event
async def on_message(message):

    global yazili_soru_sayisi
    global sesli_soru_sayisi


    # Botun kendi mesajlarını görmezden geliyoruz
    if message.author == bot.user:

        return


    # Komutların çalışmasını sağlıyoruz
    await bot.process_commands(message)


    # Komutları normal soru sistemiyle işlemiyoruz
    if message.content.startswith(PREFIX):

        return


    # --------------------------------------------------
    # SESLİ MESAJ
    # --------------------------------------------------

    if len(message.attachments) > 0:

        for dosya in message.attachments:

            # Dosyanın sesli mesaj olup olmadığını kontrol ediyoruz
            if dosya.is_voice_message():

                try:

                    await message.channel.send(
                        "🎤 Sesli mesajını yazıya çeviriyorum..."
                    )


                    # Geçici dosyanın adını oluşturuyoruz
                    dosya_adi = (
                        "gecici_ses_"
                        + str(message.author.id)
                        + "_"
                        + str(int(time.time()))
                        + ".ogg"
                    )


                    # Ses dosyasını indiriyoruz
                    await dosya.save(
                        dosya_adi
                    )


                    # Sesi yazıya çeviriyoruz
                    soru = sesli_mesaji_yaziya_cevir(
                        dosya_adi
                    )


                    # Sesli soru sayısını artırıyoruz
                    sesli_soru_sayisi += 1


                    # Soruyu veritabanına kaydediyoruz
                    soru_kaydet(

                        message.author.id,

                        str(message.author),

                        soru
                    )


                    # Hazır cevap arıyoruz
                    cevap = hazir_cevap_bul(
                        soru
                    )


                    # Hazır cevap bulunamadıysa AI kullanıyoruz
                    if cevap is None:

                        cevap = yapay_zeka_cevabi(
                            soru
                        )


                    # Cevabı gönderiyoruz
                    await message.channel.send(

                        "📝 **Algılanan soru:**\n"
                        + soru
                        + "\n\n"
                        + "🤖 **Cevap:**\n"
                        + cevap
                    )


                    # Geçici ses dosyasını siliyoruz
                    if os.path.exists(dosya_adi):

                        os.remove(
                            dosya_adi
                        )


                except Exception as hata:

                    print(
                        "SES HATASI:",
                        hata
                    )


                    # Hata olduğunda dosyayı silmeye çalışıyoruz
                    if os.path.exists(dosya_adi):

                        os.remove(
                            dosya_adi
                        )


                    await message.channel.send(

                        "❌ Sesli mesajı işleyemedim.\n"
                        "Lütfen tekrar deneyin."
                    )


                return


    # --------------------------------------------------
    # YAZILI MESAJ
    # --------------------------------------------------

    soru = message.content


    # Yazılı soru sayısını artırıyoruz
    yazili_soru_sayisi += 1


    # Soruyu veritabanına kaydediyoruz
    soru_kaydet(

        message.author.id,

        str(message.author),

        soru
    )


    # Hazır cevaplarda arıyoruz
    cevap = hazir_cevap_bul(
        soru
    )


    # Hazır cevap yoksa AI kullanıyoruz
    if cevap is None:

        try:

            cevap = yapay_zeka_cevabi(
                soru
            )

        except Exception as hata:

            print(
                "OPENAI HATASI:",
                hata
            )


            cevap = (
                "❌ Üzgünüm, şu anda yapay zekâ "
                "servisine ulaşamıyorum."
            )


    # Cevabı gönderiyoruz
    await message.channel.send(
        cevap
    )


# --------------------------------------------------
# 1 - HELLO
# --------------------------------------------------

@bot.command()
async def hello(ctx):

    await ctx.send(

        "👋 **Merhaba! Ben teknik servis botuyum.**\n\n"

        "**Komutlarım:**\n\n"

        "`!hello` - Botun komutlarını gösterir.\n"
        "`!yardim` - Yardım menüsünü gösterir.\n"
        "`!siparis` - Sipariş durumu.\n"
        "`!iptal` - Sipariş iptali.\n"
        "`!hasar` - Hasarlı ürün yardımı.\n"
        "`!teknikdestek` - Teknik destek.\n"
        "`!teslimat` - Teslimat bilgisi.\n"
        "`!istatistik` - İstatistikleri gösterir.\n"
        "`!gecmis` - Son 5 sorunu gösterir.\n"
        "`!ai soru` - Yapay zekâya soru sorar.\n"
        "`!destek` - Destek talebi oluşturur.\n"
        "`!yonetici` - Yönetici bilgilerini gösterir.\n\n"

        "📚 **Sıkça Sorulan Sorular**\n"
        "Sorunuzun cevabını görmek için aşağıdaki "
        "butonlardan birine basabilirsiniz.",

        view=SSSView()
    )


# --------------------------------------------------
# 2 - YARDIM
# --------------------------------------------------

@bot.command()
async def yardim(ctx):

    await ctx.send(

        "🛠️ **Teknik Servis Yardım Menüsü**\n\n"

        "`!hello` - Komutları gösterir.\n"
        "`!yardim` - Yardım menüsü.\n"
        "`!siparis` - Sipariş durumu.\n"
        "`!iptal` - Sipariş iptali.\n"
        "`!hasar` - Hasarlı ürün.\n"
        "`!teknikdestek` - Teknik destek.\n"
        "`!teslimat` - Teslimat bilgisi.\n"
        "`!istatistik` - Bot istatistikleri.\n"
        "`!gecmis` - Soru geçmişi.\n"
        "`!ai soru` - Yapay zekâ.\n"
        "`!destek` - Destek talebi."
    )


# --------------------------------------------------
# 3 - SİPARİŞ
# --------------------------------------------------

@bot.command()
async def siparis(ctx):

    await ctx.send(

        "📦 **Sipariş Durumu**\n\n"

        "Siparişinizin durumunu öğrenmek için internet "
        "sitemizdeki hesabınıza giriş yapın ve "
        "\"Siparişlerim\" bölümüne gidin."
    )


# --------------------------------------------------
# 4 - İPTAL
# --------------------------------------------------

@bot.command()
async def iptal(ctx):

    await ctx.send(

        "❌ **Sipariş İptali**\n\n"

        "Siparişinizi iptal etmek istiyorsanız en kısa "
        "sürede müşteri hizmetleriyle iletişime geçin."
    )


# --------------------------------------------------
# 5 - HASAR
# --------------------------------------------------

@bot.command()
async def hasar(ctx):

    await ctx.send(

        "📸 **Hasarlı Ürün**\n\n"

        "Ürününüz hasarlı geldiyse müşteri hizmetleriyle "
        "iletişime geçin ve hasarın fotoğraflarını sağlayın."
    )


# --------------------------------------------------
# 6 - TEKNİK DESTEK
# --------------------------------------------------

@bot.command()
async def teknikdestek(ctx):

    await ctx.send(

        "🔧 **Teknik Destek**\n\n"

        "Teknik destek için internet sitemizdeki telefon "
        "numarasını kullanabilir veya sohbet robotumuzdan "
        "yardım alabilirsiniz."
    )


# --------------------------------------------------
# 7 - TESLİMAT
# --------------------------------------------------

@bot.command()
async def teslimat(ctx):

    await ctx.send(

        "🚚 **Teslimat Yöntemi**\n\n"

        "Ödeme sayfasında kullanılabilir teslimat "
        "yöntemlerini görebilir ve uygun olanı seçebilirsiniz."
    )


# --------------------------------------------------
# 8 - İSTATİSTİK
# --------------------------------------------------

@bot.command()
async def istatistik(ctx):

    toplam = soru_sayisi()


    await ctx.send(

        "📊 **Teknik Servis Botu İstatistikleri**\n\n"

        "💬 Yazılı sorular: "
        + str(yazili_soru_sayisi)
        + "\n"

        "🎤 Sesli sorular: "
        + str(sesli_soru_sayisi)
        + "\n"

        "🤖 Yapay zekâya gönderilenler: "
        + str(ai_soru_sayisi)
        + "\n"

        "🗄️ Veritabanındaki toplam soru: "
        + str(toplam)
    )


# --------------------------------------------------
# 9 - GEÇMİŞ
# --------------------------------------------------

@bot.command()
async def gecmis(ctx):

    gecmis = kullanici_gecmisi(
        ctx.author.id
    )


    if len(gecmis) == 0:

        await ctx.send(
            "📭 Henüz kayıtlı bir soru geçmişin bulunmuyor."
        )

        return


    mesaj = (
        "📚 **Son 5 Sorun**\n\n"
    )


    for soru in gecmis:

        mesaj += (
            "• "
            + soru[0]
            + "\n"
        )


    await ctx.send(
        mesaj
    )


# --------------------------------------------------
# 10 - AI
# --------------------------------------------------

@bot.command()
async def ai(ctx, *, soru=None):

    if soru is None:

        await ctx.send(

            "🤖 Bir soru yazmalısın.\n\n"

            "Örnek:\n"

            "`!ai Teknik destek ne işe yarar?`"
        )

        return


    try:

        cevap = yapay_zeka_cevabi(
            soru
        )


        soru_kaydet(

            ctx.author.id,

            str(ctx.author),

            soru
        )


        await ctx.send(
            cevap
        )


    except Exception as hata:

        print(
            "OPENAI HATASI:",
            hata
        )

    await ctx.send(

            "❌ OpenAI servisine şu anda "
            "ulaşılamıyor."
        )


  
       


# --------------------------------------------------
# 11 - DESTEK
# --------------------------------------------------

@bot.command()
async def destek(ctx):

    await ctx.send(

        "🎫 **Müşteri Desteği**\n\n"

        "Sorununuzu buraya yazabilir veya "
        "🎤 sesli mesaj gönderebilirsiniz.\n\n"

        "Bot sorununuzu otomatik olarak analiz "
        "etmeye çalışacaktır.\n\n"

        "Daha fazla yardıma ihtiyacınız varsa "
        "müşteri hizmetleriyle iletişime geçebilirsiniz."
    )


# --------------------------------------------------
# 12 - YÖNETİCİ
# --------------------------------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def yonetici(ctx):

    await ctx.send(

        "🔐 **Yönetici Menüsü**\n\n"

        "Bu komutu yalnızca sunucu yöneticileri "
        "kullanabilir.\n\n"

        "📊 Toplam soru: "
        + str(soru_sayisi())
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


# --------------------------------------------------
# YÖNETİCİ HATASI
# --------------------------------------------------

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
            "yönetici olmalısın."
        )


# --------------------------------------------------
# GENEL HATA SİSTEMİ
# --------------------------------------------------

@bot.event
async def on_command_error(
    ctx,
    hata
):

    # Komut bulunamadığında
    if isinstance(
        hata,
        commands.CommandNotFound
    ):

        await ctx.send(
            "❓ Böyle bir komut bulunamadı.\n"
            "`!yardim` yazarak komutları görebilirsin."
        )

        return


    # Eksik komut olduğunda
    if isinstance(
        hata,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            "❌ Komutu eksik kullandın."
        )

        return


    # Diğer hataları terminale yazdırıyoruz
    print(
        "KOMUT HATASI:",
        hata
    )


# --------------------------------------------------
# VERİTABANI
# --------------------------------------------------

veritabani_olustur()


# --------------------------------------------------
# TOKEN KONTROLÜ
# --------------------------------------------------

if DISCORD_TOKEN == "":

    print(
        "HATA: config.py dosyasına Discord tokeni "
        "eklenmemiş."
    )

else:

    # Botu Discord'a bağlıyoruz
     bot.run("TOKEN")
