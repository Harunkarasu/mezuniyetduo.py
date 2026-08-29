import sqlite3

from config import DATABASE_NAME


# Veritabanını oluşturur
def veritabani_olustur():

    baglanti = sqlite3.connect(DATABASE_NAME)

    imlec = baglanti.cursor()

    imlec.execute("""
        CREATE TABLE IF NOT EXISTS sorular (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id TEXT,
            kullanici_adi TEXT,
            soru TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    baglanti.commit()

    baglanti.close()


# Kullanıcının sorduğu soruyu kaydeder
def soru_kaydet(kullanici_id, kullanici_adi, soru):

    baglanti = sqlite3.connect(DATABASE_NAME)

    imlec = baglanti.cursor()

    imlec.execute("""
        INSERT INTO sorular
        (kullanici_id, kullanici_adi, soru)
        VALUES (?, ?, ?)
    """, (
        str(kullanici_id),
        kullanici_adi,
        soru
    ))

    baglanti.commit()

    baglanti.close()


# Toplam soru sayısını bulur
def soru_sayisi():

    baglanti = sqlite3.connect(DATABASE_NAME)

    imlec = baglanti.cursor()

    imlec.execute(
        "SELECT COUNT(*) FROM sorular"
    )

    sonuc = imlec.fetchone()[0]

    baglanti.close()

    return sonuc


# Kullanıcının son 5 sorusunu getirir
def kullanici_gecmisi(kullanici_id):

    baglanti = sqlite3.connect(DATABASE_NAME)

    imlec = baglanti.cursor()

    imlec.execute("""
        SELECT soru
        FROM sorular
        WHERE kullanici_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (str(kullanici_id),))

    sonuc = imlec.fetchall()

    baglanti.close()

    return sonuc
