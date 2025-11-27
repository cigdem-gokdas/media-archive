import sys
import webbrowser
import os

# --- MODÜLLERİN İÇE AKTARILMASI ---
try:
    # 1. Kaşif (Senin az önce attığın kod)
    from search_manager import find_link

    # 2. Scraper (Önceki adımda İngilizce hazırladığımız kod)
    # Eğer fonksiyon adın 'verileri_cek' ise burayı değiştir
    from scraper import scrape_media_data

    # 3. Görselci (Resim indiren kod)
    # Eğer fonksiyon adın 'poster_download' ise burayı değiştir
    from poster_manager import posteri_indir

except ImportError as e:
    print("❌ HATA: Modüllerden biri bulunamadı!")
    print(f"Detay: {e}")
    print("Lütfen dosya isimlerinin (scraper.py, poster_manager.py) doğru olduğundan emin olun.")
    sys.exit()


def main():
    print("\n" + "="*50)
    print("🎬  MEDIA ARCHIVE - OTOMASYON BAŞLATILIYOR  🎬")
    print("="*50 + "\n")

    # --- ADIM 1: Kullanıcıdan Veri Al ---
    movie_name = input("🔍 Aramak istediğiniz Film/Dizi adı: ").strip()

    if not movie_name:
        print("❌ Boş giriş yapıldı. Program kapatılıyor.")
        return

    # --- ADIM 2: Linki Bul (Search Manager) ---
    # Senin attığın find_link fonksiyonunu kullanıyoruz
    target_url = find_link(movie_name)

    if not target_url:
        print("❌ Film bulunamadı veya link alınamadı.")
        return

    # --- ADIM 3: Verileri Çek (Scraper) ---
    # Bulunan linke gidip detayları çekiyoruz
    media_data = scrape_media_data(target_url)

    if not media_data:
        print("❌ Veri çekilemedi.")
        return

    # --- ADIM 4: Sonuçları Ekrana Bas ---
    print("\n" + "-"*30)
    print(f"🎥 BAŞLIK:  {media_data.get('title')}")
    print(f"📅 YIL:     {media_data.get('year')}")
    print(f"⭐ PUAN:    {media_data.get('rating')}")
    print(f"🔗 URL:     {media_data.get('page_url')}")
    print("-"*30 + "\n")

    # --- ADIM 5: Posteri İndir (Poster Manager) ---
    poster_url = media_data.get('poster_url')
    local_image_path = None

    if poster_url:
        print("🖼️  Poster indiriliyor...")
        # Başlık ve URL'yi gönderiyoruz
        local_image_path = posteri_indir(poster_url, media_data.get('title'))
    else:
        print("⚠️  Bu filmin posteri yok.")

    # --- ADIM 6: Final (Kullanıcıya Göster) ---
    print("\n✅ İşlem Tamamlandı!")

    choice = input(
        "🌐 Sonucu nerede açmak istersin? (1: Tarayıcıda Link, 2: İnen Resmi Aç, q: Çıkış): ")

    if choice == '1':
        webbrowser.open(target_url)
    elif choice == '2' and local_image_path:
        # İnen resmi işletim sisteminin varsayılan programıyla açar
        webbrowser.open('file://' + os.path.abspath(local_image_path))
    else:
        print("Güle güle! 👋")


if __name__ == "__main__":
    main()
