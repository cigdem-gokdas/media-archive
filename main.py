import os
import time

# MODÜLLER
from search_manager import find_link
from scraper import scrape_media_data
from data_storage import save_to_mongodb, list_movies, get_database, collection
from poster_manager import PosterManager


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    print("🔌 Sistem başlatılıyor...")

    # 1. Veritabanı Kontrolü
    db = get_database()
    if db is None:
        print("❌ Veritabanı bağlantısı yok. Program durduruluyor.")
        return

    poster_manager = PosterManager()

    while True:
        print("\n" + "="*45)
        print("🎬 FİLM ARŞİV SİSTEMİ (OTOMASYON)")
        print("="*45)
        print("1. 🔎 İsimle Film Ara ve Ekle")
        print("2. 📋 Kayıtlı Filmleri Listele")
        print("3. 🖼️  İndirilen Posterler")
        print("4. 🚪 Çıkış")

        secim = input("\nSeçiminiz (1-4): ")

        if secim == '1':
            # --- FİLM ARAMA MODÜLÜ ---
            movie_name = input("\n🎬 Film ismini giriniz (Örn: Gladiator):\n👉 ")

            if not movie_name.strip():
                print("❌ İsim boş olamaz.")
                continue

            # 1. ADIM: Arama yap (Artık bir sözlük dönüyor)
            search_result = find_link(movie_name)

            # Sözlük içindeki 'status' anahtarını kontrol ediyoruz
            if search_result["status"] == "success":
                found_url = search_result["url"]
                print(f"✅ Link bulundu: {found_url}")

                # Veritabanında zaten var mı?
                existing = collection.find_one({"page_url": found_url})

                if existing:
                    print(
                        f"\nℹ️  Bu film zaten arşivinizde: {existing.get('title')}")
                else:
                    print("\n🕷️  Detaylar çekiliyor...")

                    # 2. ADIM: Scraper ile verileri al
                    movie_data = scrape_media_data(found_url)

                    if movie_data:
                        print(f"\n✅ Veri Alındı:")
                        print(f"   Film: {movie_data.get('title')}")
                        print(f"   Yıl : {movie_data.get('year')}")
                        print(f"   Puan: ⭐ {movie_data.get('rating')}")

                        # 3. ADIM: Veritabanına Kaydet
                        save_to_mongodb(movie_data)

                        # 4. ADIM: Posteri İndir
                        poster_url = movie_data.get('poster_url')
                        if poster_url:
                            poster_manager.download_poster(
                                poster_url, movie_data.get('title'))
                        else:
                            print("⚠️ Poster bulunamadı.")
                    else:
                        print("❌ Veri çekilemedi.")
            else:
                # Hata varsa sebebini yazdır
                print(f"❌ Film bulunamadı. Hata: {search_result.get('error')}")

        elif secim == '2':
            list_movies()
            input("\nDevam etmek için Enter'a basın...")

        elif secim == '3':
            print("\n📂 İndirilen Posterler:")
            posters = poster_manager.get_downloaded_posters()
            if posters:
                for i, p in enumerate(posters, 1):
                    print(f" {i}. {p}")
            else:
                print("📭 Klasör boş.")
            input("\nDevam etmek için Enter'a basın...")

        elif secim == '4':
            print("👋 Çıkış yapılıyor...")
            break

        else:
            print("❌ Geçersiz seçim.")

        clear_screen()


if __name__ == "__main__":
    main()
