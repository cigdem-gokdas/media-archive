def main():
    print("--- IMDb Film Bilgi Getirici ---")
    print("Çıkmak için 'q' tuşuna basıp Enter yapabilirsin.\n")

    while True:
        movie_name = input("Film adını girin: ").strip()

        if movie_name.lower() == 'q':
            print("Program kapatılıyor...")
            break

        if not movie_name:
            continue

        # 1. ADIM: Linki Bul (Search Manager)
        print(f"\n🔍 '{movie_name}' aranıyor...")
        found_url = find_link(movie_name)

        if found_url:
            # 2. ADIM: Veriyi Çek (Scraper)
            print("📥 Veriler çekiliyor...")
            movie_data = scrape_media_data(found_url)

            if movie_data:
                # 3. ADIM: Sonucu Ekrana Bas
                print("\n" + "="*40)
                print(f"🎬 BAŞLIK:  {movie_data.get('title')}")
                print(f"📅 YIL:     {movie_data.get('year')}")
                print(f"⭐ PUAN:    {movie_data.get('rating')}")
                print(f"🔗 URL:     {movie_data.get('page_url')}")
                print("="*40 + "\n")
            else:
                print("❌ Link bulundu ama veriler çekilemedi.")
        else:
            print("❌ Film bulunamadı, lütfen isimi kontrol edin.")

if __name__ == "__main__":
    main()