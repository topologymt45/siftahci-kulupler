# Siftahçı Kulüpler

Futbolculara siftah yaptıran kulüpler. Bir oyuncu bir kategorideki ilk golünü bir kez atar ve bu hiç
değişmez; o ilk golü attıran kulüp siftahçıdır. Bu proje, hangi kulüplerin en çok oyuncuya siftah
yaptırdığını inceliyor.

## Ne inceleniyor
Kapsam: Premier League, Serie A, LaLiga, Bundesliga, Ligue 1, Liga Portugal, Pro League, Eredivisie ve
Süper Lig kulüpleri, 2012/13 – 2025/26. Sadece lig maçları ile Şampiyonlar Ligi, Avrupa Ligi ve Konferans
Ligi maçları (elemeler dahil) sayılır; yerel kupalar sayılmaz.

Kategoriler:
- Kariyerdeki ilk gol
- Ligdeki ilk gol
- Avrupa kupalarındaki ilk gol
- Şampiyonlar Ligi, Avrupa Ligi ve Konferans Ligi'ndeki ilk gol
- Sezondaki ilk gol
- Toplam: seçilen kategorilerin toplamı

Her kulüp için siftah sayısı, maç başına siftah, ilk gol oranı (siftahların yenen gollere oranı) ve
siftah yapan oyuncuların ortalama yaşı hesaplanır. Rekorlar bölümünde en yaşlı ve en genç siftahlar, en
geç ve en erken dakikada gelen siftahlar, bir sezonda ve bir maçta en çok siftah yaptıran kulüpler yer alır.

Bir golün gerçekten oyuncunun ilk golü olduğundan emin olunamıyorsa o gol sayılmaz. Örneğin 2012/13'te
zaten oynayan, başka bir ligden gelen ya da araya kiralık dönemi giren oyuncular hesaba katılmaz.
Kendi kalesine goller de sayılmaz.

## Veri kaynağı
Tüm maç ve gol verisi [Transfermarkt](https://www.transfermarkt.com) kaynaklıdır ve David Cariboo'nun açık
veri projesi [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets) üzerinden
alınmıştır ([Kaggle](https://www.kaggle.com/datasets/davidcariboo/player-scores)). Veri seti
[CC0-1.0](https://github.com/dcaribou/transfermarkt-datasets/blob/master/LICENSE) lisanslıdır ve Temmuz 2026'ya
kadar günceldir. Bu proje Transfermarkt ile bağlantılı değildir.
