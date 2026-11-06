# Siftahçı Kulüpler

Futbolculara ilk golünü **yediren** kulüplerin sıralaması. Bir oyuncunun bir kategorideki ilk golü bir kez
atılır ve hiç değişmez; o golü yiyen kulüp siftahçıdır.

Kapsam: Premier League, Serie A, LaLiga, Bundesliga, Ligue 1, Liga Portugal, Pro League, Eredivisie ve
Süper Lig kulüpleri, 2012/13 – 2025/26.

## Kategoriler
- Kariyerdeki ilk gol (lig + Şampiyonlar Ligi / Avrupa Ligi / Konferans Ligi maçları)
- Ligdeki ilk gol
- Avrupa kupalarındaki ilk gol (ŞL, AL, KL ve elemeleri)
- Şampiyonlar Ligi / Avrupa Ligi / Konferans Ligi'ndeki ilk gol
- Sezondaki ilk gol
- Toplam: seçilen kategorilerin toplamı

Ölçüler: siftah sayısı, maç başına siftah, ilk gol oranı (siftah ÷ yenen gol), ortalama siftah yaşı.
Sekmeler: Sıralama, Kulüp, Rekorlar (en yaşlı/genç siftah, en geç/erken dakika, bir sezonda/maçta en çok siftah), Tablo.

## Çalıştırma
İşlenmiş veri (`data/processed/`) depoda hazır geliyor:
```
pip install -r requirements.txt
streamlit run app.py
```

Veriyi baştan üretmek için [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets)
CSV'lerini (ZIP) indirip `data/raw/` içine açın, sonra:
```
python src/build_data.py
```

## Kurallar
- Sadece lig maçları ve ŞL / AL / KL (elemeler dahil) sayılır. Yerel kupalar ve süper kupalar sayılmaz.
- Kendi kalesine goller sayılmaz.
- Siftahçı kulüp, golü yediği sezonda 9 ligden birinde oynuyor olmalı. Oyuncunun ilk golü başka bir ligde
  atıldıysa (ör. önce Rusya'da gol atıp sonra Süper Lig'e gelen oyuncu) sonraki golü siftah sayılmaz.
- Emin olunmayan ilk goller sayılmaz:
  - turnuvanın veride başladığı sezonda (çoğunlukla 2012/13) zaten oynayanlar,
  - kariyer / lig: veride ilk kez 21 yaşından büyük görünenler, doğum tarihi bilinmeyenler ve ilk golünden
    önce 200 günden uzun süre veriden kaybolanlar,
  - Avrupa: Temmuz 2012'de 20 yaşından büyük olanlar.

Eşikler `src/build_data.py` içinde (`MAX_DEBUT_AGE`, `MAX_AGE_AT_START`, `MAX_GAP_DAYS`).

## Sınırlar
Veride alt ligler yok; alt ligde atılan goller görünmez. Dakikalarda uzatma süresi ayrılmaz (90+3 → 90).

## Veri ve lisans
Veri: [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) (CC0-1.0), Temmuz 2026'ya kadar.
