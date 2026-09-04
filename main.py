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


# ==================================================
# DISCORD AYARLARI
# ==================================================

intents = discord.Intents.default()

intents.message_content = True


bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents
)


# ==================================================
# OPENAI
# ==================================================

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==================================================
# İSTATİSTİKLER
# ==================================================

yazili_soru_sayisi = 0
sesli_soru_sayisi = 0
ai_soru_sayisi = 0


# ==================================================
# BOT AÇIKLAMASI
# ==================================================

BOT_ACIKLAMASI = (
    "🛠️ **Teknik Servis Asistanı**\n\n"
    "Merhaba! Ben teknik servis destek botuyum.\n\n"

    "📚 Sıkça sorulan soruları hazır cevaplarla "
    "yanıtlayabilirim.\n"

    "🤖 Hazır cevap bulunamadığında yapay zekâ "
    "ile cevap oluşturabilirim.\n"

    "🎤 Sesli mesajları yazıya çevirip "
    "sorunuzu analiz edebilirim.\n"

    "🗄️ Sorularınızı veritabanına kaydedebilir "
    "ve geçmiş sorularınızı gösterebilirim.\n"

    "📊 Botun kullanım istatistiklerini "
    "gösterebilirim.\n"

    "⭐ Hizmet hakkında geri bildirim "
    "bırakabilirsiniz.\n\n"

    "Aşağıdaki butonlardan yapmak istediğiniz "
    "işlemi seçebilirsiniz."
)


# ==================================================
# SIKÇA SORULAN SORULAR
# ==================================================

sorular = {

    "nasıl alışveriş yapabilirim":
        "Alışveriş yapmak için ilgilendiğiniz ürünü "
        "seçip \"Alışveriş Sepetine Ekle\" butonuna "
        "tıklayın. Ardından sepetinize giderek "
        "satın alma işlemini tamamlayabilirsiniz.",

    "siparişimin durumunu nasıl öğrenebilirim":
        "Siparişinizin durumunu öğrenmek için "
        "internet sitemizdeki hesabınıza giriş yapın "
        "ve \"Siparişlerim\" bölümüne gidin.",

    "bir siparişi nasıl iptal edebilirim":
        "Siparişinizi iptal etmek istiyorsanız en kısa "
        "sürede müşteri hizmetleriyle iletişime geçin. "
        "Sipariş gönderilmeden önce iptal konusunda "
        "yardımcı olmaya çalışacağız.",

    "siparişim hasarlı gelirse ne yapmalıyım":
        "Hasarlı bir ürün aldıysanız müşteri "
        "hizmetleriyle iletişime geçin ve hasarın "
        "fotoğraflarını gönderin.",

    "teknik destekle nasıl iletişime geçebilirim":
        "Teknik destek için internet sitemizdeki "
        "telefon numarasını kullanabilir veya "
        "bu teknik servis botundan yardım alabilirsiniz.",

    "ödeme sırasında teslimat yöntemini değiştirebilir miyim":
        "Evet. Ödeme sayfasında kullanılabilir "
        "teslimat yöntemlerinden uygun olanı "
        "seçebilirsiniz.",

    "iade nasıl yapılır":
        "İade işlemi hakkında bilgi almak için "
        "müşteri hizmetleriyle iletişime geçebilirsiniz. "
        "İade şartları ürüne ve sipariş durumuna göre "
        "değişebilir.",

    "garanti süresi ne kadar":
        "Garanti süresi ürünlere göre değişebilir. "
        "Ürünün garanti bilgilerini ürün sayfasından "
        "veya satın alma belgelerinizden kontrol "
        "edebilirsiniz.",

    "ödeme başarısız oldu":
        "Ödeme sırasında sorun yaşıyorsanız kart "
        "bilgilerinizi kontrol edip tekrar deneyin. "
        "Sorun devam ederse müşteri hizmetleriyle "
        "iletişime geçebilirsiniz.",

    "fatura nasıl alınır":
        "Faturanıza hesabınızdaki \"Siparişlerim\" "
        "bölümünden ulaşabilirsiniz."
}


# ==================================================
# SSS ALTERNATİF KELİMELERİ
# ==================================================

sss_anahtarlari = {

    "nasıl alışveriş yapabilirim": [
        "alışveriş",
        "alisveris",
        "satın alma",
        "satin alma",
        "ürün nasıl alırım",
        "urun nasil alirim",
        "ürün satın",
        "urun satin",
        "ürün almak",
        "urun almak"
    ],

    "siparişimin durumunu nasıl öğrenebilirim": [
        "siparişim nerede",
        "siparisim nerede",
        "sipariş durumu",
        "siparis durumu",
        "siparişimi takip",
        "siparisimi takip",
        "kargom nerede",
        "kargo nerede"
    ],

    "bir siparişi nasıl iptal edebilirim": [
        "sipariş iptal",
        "siparis iptal",
        "siparişi iptal",
        "siparisi iptal",
        "siparişimi iptal",
        "siparisimi iptal",
        "ürünü iptal",
        "urunu iptal"
    ],

    "siparişim hasarlı gelirse ne yapmalıyım": [
        "hasarlı ürün",
        "hasarli urun",
        "ürün hasarlı",
        "urun hasarli",
        "ürün kırık",
        "urun kirik",
        "sipariş hasarlı",
        "siparis hasarli",
        "kırık geldi",
        "kirik geldi",
        "bozuk ürün",
        "bozuk urun"
    ],

    "teknik destekle nasıl iletişime geçebilirim": [
        "teknik destek",
        "teknikdestek",
        "destek ekibi",
        "destekle iletişim",
        "destekle iletisim",
        "teknik servis",
        "müşteri hizmetleri",
        "musteri hizmetleri"
    ],

    "ödeme sırasında teslimat yöntemini değiştirebilir miyim": [
        "teslimat yöntemi",
        "teslimat yontemi",
        "teslimat değiştirme",
        "teslimat degistirme",
        "kargo yöntemini değiştir",
        "kargo yontemini degistir",
        "kargo seçeneği",
        "kargo secenegi"
    ],

    "iade nasıl yapılır": [
        "iade",
        "ürünü iade",
        "urunu iade",
        "ürün iade",
        "urun iade",
        "para iadesi",
        "paramı geri",
        "parami geri"
    ],

    "garanti süresi ne kadar": [
        "garanti",
        "garanti süresi",
        "garanti suresi",
        "garantisi var mı",
        "garantisi var mi",
        "garanti ne kadar"
    ],

    "ödeme başarısız oldu": [
        "ödeme",
        "odeme",
        "ödeme yapamıyorum",
        "odeme yapamiyorum",
        "ödeme başarısız",
        "odeme basarisiz",
        "kart çalışmıyor",
        "kart calismiyor",
        "kart geçmiyor",
        "kart gecmiyor"
    ],

    "fatura nasıl alınır": [
        "fatura",
        "faturam",
        "fatura almak",
        "faturayı nasıl",
        "faturayi nasil",
        "faturam nerede"
    ]
}


# ==================================================
# SORUYU TEMİZLEME
# ==================================================

def soruyu_temizle(soru):

    soru = soru.lower()

    soru = soru.strip()

    noktalama = "?!.,;:()[]{}\"'"

    for karakter in noktalama:

        soru = soru.replace(
            karakter,
            ""
        )

    soru = " ".join(
        soru.split()
    )

    return soru


# ==================================================
# HAZIR CEVAP BULMA
# ==================================================

def hazir_cevap_bul(soru):

    soru = soruyu_temizle(
        soru
    )

    # Ana soruları kontrol et

    for anahtar in sorular:

        if anahtar in soru:

            return sorular[anahtar]


    # Alternatif kelimeleri kontrol et

    for anahtar in sss_anahtarlari:

        for kelime in sss_anahtarlari[anahtar]:

            if kelime in soru:

                return sorular[anahtar]


    return None


# ==================================================
# YAPAY ZEKA
# ==================================================

def yapay_zeka_cevabi(soru):

    global ai_soru_sayisi

    ai_soru_sayisi += 1

    cevap = openai_client.responses.create(

        model=OPENAI_MODEL,

        input=[

            {
                "role": "system",

                "content":
                    "Sen bir teknik servis destek "
                    "botusun. Türkçe cevap ver. "
                    "Kısa, anlaşılır ve yardımcı ol. "
                    "Bilmediğin şirket bilgilerini "
                    "uydurma. Teknik servis, alışveriş, "
                    "sipariş, teslimat, ödeme, garanti "
                    "ve iade konularında yardımcı ol."
            },

            {
                "role": "user",

                "content": soru
            }
        ]
    )

    return cevap.output_text


# ==================================================
# SESLİ MESAJI YAZIYA ÇEVİRME
# ==================================================

def sesli_mesaji_yaziya_cevir(dosya_adi):

    with open(
        dosya_adi,
        "rb"
    ) as ses_dosyasi:

        cevap = openai_client.audio.transcriptions.create(

            model="gpt-4o-mini-transcribe",

            file=ses_dosyasi
        )

    return cevap.text


# ==================================================
# GERİ BİLDİRİM MODALI
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


        if puan not in ["1", "2", "3", "4", "5"]:

            await interaction.response.send_message(

                "❌ Lütfen 1 ile 5 arasında bir puan girin.",

                ephemeral=True
            )

            return


        if yorum == "":

            yorum = "Yorum bırakılmadı."


        print(
            "GERİ BİLDİRİM:",
            str(interaction.user),
            "| Puan:",
            puan,
            "| Yorum:",
            yorum
        )


        await interaction.response.send_message(

            "⭐ **Geri bildirimin için teşekkürler!**\n\n"
            "Puanın: "
            + puan
            + "/5\n\n"
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


        self.add_item(
            self.soru
        )


    async def on_submit(
        self,
        interaction
    ):

        soru = str(
            self.soru.value
        )


        await interaction.response.defer(
            ephemeral=True
        )


        try:

            cevap = yapay_zeka_cevabi(
                soru
            )


            soru_kaydet(

                interaction.user.id,

                str(interaction.user),

                soru,

                cevap
            )


            await interaction.followup.send(

                "🤖 **Yapay Zekâ Cevabı:**\n\n"
                + cevap,

                ephemeral=True
            )


        except Exception as hata:

            print(
                "AI HATASI:",
                hata
            )


            await interaction.followup.send(

                "❌ Yapay zekâ servisine şu anda "
                "ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",

                ephemeral=True
            )


# ==================================================
# ANA MENÜ BUTONLARI
# ==================================================

class AnaMenu(discord.ui.View):

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
        emoji="🛒",
        row=0
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
        emoji="📦",
        row=0
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
        emoji="❌",
        row=0
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
        emoji="⚠️",
        row=0
    )
    async def hasarli(
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
        emoji="🔧",
        row=0
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
        emoji="🚚",
        row=1
    )
    async def teslimat(
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


    # ----------------------------------------------
    # İADE
    # ----------------------------------------------

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

        await interaction.response.send_message(

            sorular[
                "iade nasıl yapılır"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # GARANTİ
    # ----------------------------------------------

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

        await interaction.response.send_message(

            sorular[
                "garanti süresi ne kadar"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # ÖDEME
    # ----------------------------------------------

    @discord.ui.button(
        label="Ödeme",
        style=discord.ButtonStyle.secondary,
        emoji="💳",
        row=1
    )
    async def odeme(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "ödeme başarısız oldu"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # FATURA
    # ----------------------------------------------

    @discord.ui.button(
        label="Fatura",
        style=discord.ButtonStyle.secondary,
        emoji="🧾",
        row=1
    )
    async def fatura(
        self,
        interaction,
        button
    ):

        await interaction.response.send_message(

            sorular[
                "fatura nasıl alınır"
            ],

            ephemeral=True
        )


    # ----------------------------------------------
    # SORU GEÇMİŞİ
    # ----------------------------------------------

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

        gecmis = kullanici_gecmisi(
            interaction.user.id
        )


        if len(gecmis) == 0:

            await interaction.response.send_message(

                "📭 Henüz kayıtlı bir soru geçmişin "
                "bulunmuyor.",

                ephemeral=True
            )

            return


        mesaj = "📚 **Son 5 Sorun**\n\n"

        sayac = 1


        for soru in gecmis:

            mesaj += (

                str(sayac)
                + ". "
                + soru[0]
                + "\n"
            )

            sayac += 1


        await interaction.response.send_message(

            mesaj,

            ephemeral=True
        )


    # ----------------------------------------------
    # İSTATİSTİK
    # ----------------------------------------------

    @discord.ui.button(
        label="İstatistik",
        style=discord.ButtonStyle.primary,
        emoji="📊",
        row=2
    )
    async def istatistik(
        self,
        interaction,
        button
    ):

        toplam = soru_sayisi()


        mesaj = (

            "📊 **Teknik Servis Botu İstatistikleri**\n\n"

            "💬 Yazılı sorular: "
            + str(yazili_soru_sayisi)
            + "\n"

            "🎤 Sesli sorular: "
            + str(sesli_soru_sayisi)
            + "\n"

            "🤖 Yapay zekâ soruları: "
            + str(ai_soru_sayisi)
            + "\n"

            "🗄️ Toplam kayıtlı soru: "
            + str(toplam)
        )


        await interaction.response.send_message(

            mesaj,

            ephemeral=True
        )


    # ----------------------------------------------
    # YAPAY ZEKA
    # ----------------------------------------------

    @discord.ui.button(
        label="Yapay Zekâ",
        style=discord.ButtonStyle.success,
        emoji="🤖",
        row=2
    )
    async def ai(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            AIsoruModal()
        )


    # ----------------------------------------------
    # GERİ BİLDİRİM
    # ----------------------------------------------

    @discord.ui.button(
        label="Geri Bildirim",
        style=discord.ButtonStyle.secondary,
        emoji="⭐",
        row=3
    )
    async def geri_bildirim(
        self,
        interaction,
        button
    ):

        await interaction.response.send_modal(
            GeriBildirimModal()
        )


    # ----------------------------------------------
    # YÖNETİCİ
    # ----------------------------------------------

    @discord.ui.button(
        label="Yönetici",
        style=discord.ButtonStyle.danger,
        emoji="🔐",
        row=3
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


        await interaction.response.send_message(

            "🔐 **Yönetici Paneli**\n\n"

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
            + str(ai_soru_sayisi),

            ephemeral=True
        )


    # ----------------------------------------------
    # ANA MENÜ
    # ----------------------------------------------

    @discord.ui.button(
        label="Ana Menü",
        style=discord.ButtonStyle.primary,
        emoji="🏠",
        row=3
    )
    async def ana_menu(
        self,
        interaction,
        button
    ):

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
    print("Toplam soru:", soru_sayisi())
    print("--------------------------------")


# ==================================================
# MESAJ SİSTEMİ
# ==================================================

@bot.event
async def on_message(message):

    global yazili_soru_sayisi
    global sesli_soru_sayisi


    if message.author == bot.user:

        return


    await bot.process_commands(
        message
    )


    # Komutları normal soru olarak işleme

    if message.content.startswith(
        PREFIX
    ):

        return


    # ==================================================
    # SESLİ MESAJ
    # ==================================================

    if len(message.attachments) > 0:

        for dosya in message.attachments:

            try:

                sesli_mi = dosya.is_voice_message()

            except Exception:

                sesli_mi = False


            if sesli_mi:

                dosya_adi = ""


                try:

                    await message.channel.send(

                        "🎤 Sesli mesajını yazıya "
                        "çeviriyorum..."
                    )


                    dosya_adi = (

                        "gecici_ses_"

                        + str(message.author.id)

                        + "_"

                        + str(int(time.time()))

                        + ".ogg"
                    )


                    await dosya.save(
                        dosya_adi
                    )


                    soru = sesli_mesaji_yaziya_cevir(
                        dosya_adi
                    )


                    sesli_soru_sayisi += 1


                    cevap = hazir_cevap_bul(
                        soru
                    )


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
                                "❌ Sorunuzu algıladım fakat "
                                "şu anda yapay zekâ servisine "
                                "ulaşamıyorum."
                            )


                    soru_kaydet(

                        message.author.id,

                        str(message.author),

                        soru,

                        cevap
                    )


                    await message.channel.send(

                        "📝 **Algılanan soru:**\n"
                        + soru
                        + "\n\n"
                        + "🤖 **Cevap:**\n"
                        + cevap
                    )


                except Exception as hata:

                    print(
                        "SES HATASI:",
                        hata
                    )


                    await message.channel.send(

                        "❌ Sesli mesajı işleyemedim.\n"
                        "Lütfen tekrar deneyin."
                    )


                finally:

                    if dosya_adi != "":

                        if os.path.exists(
                            dosya_adi
                        ):

                            os.remove(
                                dosya_adi
                            )


                return


    # ==================================================
    # YAZILI MESAJ
    # ==================================================

    soru = message.content.strip()


    if soru == "":

        return


    yazili_soru_sayisi += 1


    cevap = hazir_cevap_bul(
        soru
    )


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


    try:

        soru_kaydet(

            message.author.id,

            str(message.author),

            soru,

            cevap
        )

    except Exception as hata:

        print(
            "VERİTABANI HATASI:",
            hata
        )


    await message.channel.send(
        cevap
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

        "🛠️ **Teknik Servis Yardım Merkezi**\n\n"

        "Aşağıdaki butonlardan yardım almak "
        "istediğiniz konuyu seçebilirsiniz.\n\n"

        "💬 Yazılı soru göndererek de doğrudan "
        "botla konuşabilirsiniz.\n"

        "🎤 Sesli mesaj göndererek sorunuzu "
        "anlatabilirsiniz.\n\n"

        "🤖 Hazır cevap bulunamazsa yapay zekâ "
        "devreye girer.\n\n"

        "⭐ Hizmet hakkında geri bildirim "
        "bırakabilirsiniz.",

        view=AnaMenu()
    )


# ==================================================
# !SİPARİŞ
# ==================================================

@bot.command()
async def siparis(ctx):

    await ctx.send(

        sorular[
            "siparişimin durumunu nasıl öğrenebilirim"
        ]
    )


# ==================================================
# !İPTAL
# ==================================================

@bot.command()
async def iptal(ctx):

    await ctx.send(

        sorular[
            "bir siparişi nasıl iptal edebilirim"
        ]
    )


# ==================================================
# !HASAR
# ==================================================

@bot.command()
async def hasar(ctx):

    await ctx.send(

        sorular[
            "siparişim hasarlı gelirse ne yapmalıyım"
        ]
    )


# ==================================================
# !TEKNİKDESTEK
# ==================================================

@bot.command()
async def teknikdestek(ctx):

    await ctx.send(

        sorular[
            "teknik destekle nasıl iletişime geçebilirim"
        ]
    )


# ==================================================
# !TESLİMAT
# ==================================================

@bot.command()
async def teslimat(ctx):

    await ctx.send(

        sorular[
            "ödeme sırasında teslimat yöntemini değiştirebilir miyim"
        ]
    )


# ==================================================
# !İSTATİSTİK
# ==================================================

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

        "🤖 Yapay zekâ soruları: "
        + str(ai_soru_sayisi)
        + "\n"

        "🗄️ Veritabanındaki toplam soru: "
        + str(toplam)
    )


# ==================================================
# !GEÇMİŞ
# ==================================================

@bot.command()
async def gecmis(ctx):

    gecmis = kullanici_gecmisi(
        ctx.author.id
    )


    if len(gecmis) == 0:

        await ctx.send(

            "📭 Henüz kayıtlı bir soru geçmişin "
            "bulunmuyor."
        )

        return


    mesaj = "📚 **Son 5 Sorun**\n\n"

    sayac = 1


    for soru in gecmis:

        mesaj += (

            str(sayac)
            + ". "
            + soru[0]
            + "\n"
        )

        sayac += 1


    await ctx.send(
        mesaj
    )


# ==================================================
# !AI
# ==================================================

@bot.command()
async def ai(ctx, *, soru=None):

    if soru is None:

        await ctx.send(

            "🤖 Bir soru yazmalısın.\n\n"

            "Örnek:\n"

            "`!ai Bilgisayarım neden açılmıyor?`"
        )

        return


    try:

        cevap = yapay_zeka_cevabi(
            soru
        )


        soru_kaydet(

            ctx.author.id,

            str(ctx.author),

            soru,

            cevap
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


# ==================================================
# !DESTEK
# ==================================================

@bot.command()
async def destek(ctx):

    await ctx.send(

        "🎫 **Teknik Servis Destek Merkezi**\n\n"

        "Sorununuzu buraya yazabilirsiniz.\n\n"

        "🎤 Sesli mesaj göndererek de "
        "sorununuzu anlatabilirsiniz.\n\n"

        "🤖 Bot mesajınızı analiz eder ve "
        "uygun bir cevap vermeye çalışır.\n\n"

        "⭐ Hizmet hakkında geri bildirim "
        "bırakabilirsiniz.\n\n"

        "Aşağıdaki menüyü kullanarak da "
        "destek konunuzu seçebilirsiniz.",

        view=AnaMenu()
    )


# ==================================================
# !YÖNETİCİ
# ==================================================

@bot.command()
@commands.has_permissions(
    administrator=True
)
async def yonetici(ctx):

    await ctx.send(

        "🔐 **Yönetici Paneli**\n\n"

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


# ==================================================
# YÖNETİCİ KOMUT HATASI
# ==================================================

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


# ==================================================
# GENEL KOMUT HATASI
# ==================================================

@bot.event
async def on_command_error(
    ctx,
    hata
):

    if isinstance(
        hata,
        commands.CommandNotFound
    ):

        await ctx.send(

            "❓ Böyle bir komut bulunamadı.\n"
            "`!hello` yazarak buton menüsünü açabilirsin."
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


    print(
        "KOMUT HATASI:",
        hata
    )


# ==================================================
# VERİTABANI
# ==================================================

veritabani_olustur()


# ==================================================
# TOKEN KONTROLÜ
# ==================================================

if DISCORD_TOKEN == "":

    print(
        "HATA: config.py dosyasına Discord tokeni eklenmemiş."
    )

else:

    print(
        "Discord botuna bağlanılıyor..."
    )

# Botu Discord'a bağlıyoruz
    bot.run("TOKEN")


        
    



   
        








