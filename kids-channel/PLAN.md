# Lulu & Bobo — Çocuk Kanalı İşletme Planı

> Hedef: 0–6 yaş, çok dilli (TR → EN → ES → AR → PT → ID), AI destekli ama insan
> denetimli 3D çizgi film kanalı. İlk 90 günde YPP (para kazanma) kabulü.

## 1. Marka

| Öğe | Karar |
|---|---|
| Kanal adı | **Lulu & Bobo** (her dilde okunur; yayından önce marka/isim taraması yapılacak) |
| Slogan | TR "Söyle, Öğren, Gül!" · EN "Sing, Learn, Giggle!" |
| Görsel stil | Yumuşak 3D, yuvarlak hatlar, doygun pastel, tek düz arka plan, büyük gözler |
| Ses | Kanal sesi: sıcak, neşeli genç kadın vokal (sabit ACE-Step ayarı / LoRA) |
| Jingle | 3 sn'lik "Lu-lu-Bo-bo!" — her videonun sonunda (marka hafızası) |

### Karakterler (özgün — mevcut hiçbir markaya benzetilmez)
- **Lulu** — 3 yaşında kirpi kız. Mercan rengi dikenleri, sarı tulum, meraklı, biraz yaramaz. Kancaların öznesi.
- **Bobo** — Lulu'nun babası, iri, sakin, kahverengi ayı. Yeşil kazak. "Ebeveyn + çocuk" kancası.
- **Zıpzıp** — Mavi kurbağa arkadaş. Komik düşmeler, ses efektleri.
- **Mimi** — Küçük beyaz karınca. Değerler hikâyelerinde "küçük ama yardımsever".

Karakter tutarlılığı: her karakter için 20–30 görsellik referans seti → Flux/SDXL karakter LoRA'sı →
tüm sahne görselleri bu LoRA ile üretilir → Wan2GP image-to-video. (`pipeline/bible/characters.yaml`)

## 2. İçerik stratejisi

**Kanca kopyalama kuralı:** Viral formatı (konu, süre, ritim, kanca saniyesi, kamera, başlık kalıbı) 1:1
alırız. Rakibin özgün söz/melodisini, karelerini, karakter tasarımını ve thumbnail'ini **almayız**.
Halk malı tekerlemeler serbesttir; melodiyi kendimiz üretiriz.

### Yayın takvimi (her gün)
| Gün | Format | Süre | Kanca kaynağı |
|---|---|---|---|
| Pzt | İki dilli kelime şarkısı | 20 sn Shorts | Telugu Learning with Anika |
| Sal | Ebeveyn-çocuk sürpriz | 10–15 sn Shorts | Father-daughter show |
| Çar | Komik günlük rutin | 30–40 sn Shorts | SM Bangla Daily |
| Per | Renk öğrenme makinesi | 25 sn Shorts | Jugnu Kids |
| Cum | Güvenlik/alışkanlık şarkısı | 30 sn Shorts + 2–3 dk uzun | Bubu Arabic, Lunito |
| Cmt | Değerler masalı | 60 sn Shorts | Agile Mind, Leo & PawPaw |
| Paz | **Uzun derleme** | 15–30 dk (16:9) | Dino World, Cocomelon (gelir) |

Shorts büyütür, uzun video para kazandırır. Her Shorts'un 16:9 versiyonu derlemeye girer.

### Dil açılımı
1. Ay 1: Sadece TR+EN iki dilli içerik (tek kanal).
2. Ay 2: Tutan (>100K izlenme) videoların EN-only ve ES kanalları.
3. Ay 3+: AR, PT, ID. Her dil **ayrı seslendirme + yerelleştirilmiş söz** (aynı dosyanın kopyası değil).

## 3. Üretim hattı (pipeline)

```
trend taraması (haftalık) → kanca çıkarma → bölüm YAML'ı (söz, sahne, prompt)
   → ACE-Step şarkı → Demucs vokal ayrımı
   → Flux + karakter LoRA sahne görselleri
   → Wan2GP: Wan 2.2 I2V (sahne) + S2V/InfiniteTalk (şarkı söyleyen ağız)
   → FFmpeg: Shorts 9:16 + uzun 16:9 + jingle + altyazı
   → thumbnail + metadata (çok dilli)
   → İNSAN KONTROLÜ (zorunlu checklist) → zamanlanmış yükleme
```
Kod: `pipeline/` — ayrıntı `pipeline/README.md`.

### Donanım ve süre tahmini
| Kaynak | Öneri |
|---|---|
| GPU | Min. RTX 3060 12 GB (Wan2GP düşük VRAM modu); ideal RTX 4090 24 GB |
| Bir Shorts (6–8 klip × 5 sn) | 4090: ~30–60 dk · 3060: 2–4 saat |
| Haftalık iş gücü | 1 kişi: ~10–15 saat (prompt + kontrol + yükleme) |

Tahminler kaba; ilk hafta gerçek sürelerle güncellenecek.

## 4. Kanalın ayakta kalması — zorunlu kurallar

### YouTube politikaları
- [ ] Tüm videolar **"Made for Kids"** işaretli (COPPA). Yorum yok, kişiselleştirilmiş reklam yok — bilinçli kabul.
- [ ] **Altered/synthetic content** beyanı gerektiğinde işaretlenir; açıklamada "AI araçlarıyla üretildi, ekibimiz tarafından yazıldı ve denetlendi."
- [ ] **Inauthentic content** koruması: her video farklı konu + farklı söz + farklı mekân. Günde en fazla 1–2 yükleme. Aynı videonun dil kopyaları ayrı seslendirme ile.
- [ ] Telif: yalnız lisanslı/ticari modeller (ACE-Step MIT/Apache, Wan Apache 2.0). MusicGen, LeVo, YuE2 **yasak**.
- [ ] Başka marka karakterine benzeyen tasarım, isim, thumbnail **yasak**.

### Çocuk güvenliği (her video, yayından önce)
- [ ] Bozuk anatomi yok (fazla parmak, eriyen yüz, göz kayması)
- [ ] Korkutucu ifade, tehlikeli davranış özendirmesi yok (yükseklik, prize dokunma, yalnız yüzme)
- [ ] Gıda/şeker içeriğinde dengeli mesaj (dişler fırçalanır, sebze de yenir)
- [ ] Sözler dil bilgisi ve anlam olarak doğru (anadil konuşanı kontrol eder)
- [ ] Ses seviyesi -14 LUFS, ani gürültü yok

### Gelir çeşitlendirme
1. YouTube reklam (Made for Kids RPM düşük: ~0,3–2 $)
2. Şarkıların Spotify/Apple Music'e dağıtımı (DistroKid vb. — AI müzik politikasını kontrol et)
3. Boyama sayfaları / PDF etkinlik kitapları (Etsy, Gumroad)
4. Uzun vadede: karakter lisansı, YouTube Kids dışı platformlar (TikTok, Instagram — 13+ ebeveyn hesapları)

## 5. KPI ve karar kuralları

| Metrik | Hedef (Ay 1) | Karar |
|---|---|---|
| Shorts ortalama izlenme | 10K | 3 gün üst üste <1K → formatı değiştir |
| Shorts izlenme oranı (viewed vs swiped) | >70% | <60% → ilk 1 sn kancayı güçlendir |
| Uzun video ort. izlenme süresi | >40% | <25% → tempo/şarkı sırası değişir |
| Abone | 1.000 (YPP eşiği) | — |
| İzlenme saati / Shorts izlenme | 4.000 saat **veya** 10M Shorts / 90 gün | — |

Haftalık döngü: Pazartesi trend taraması → Salı en iyi 3 kancayı seç → Çar–Paz üretim (1 hafta önden).
Her zaman **7 günlük stok** tutulur.

## 6. Riskler

| Risk | Önlem |
|---|---|
| YPP reddi (inauthentic) | Özgün karakter, insan kontrolü, düşük frekans, çeşitlilik |
| Kanal kapanması (çocuk güvenliği) | Checklist, şüpheli kare varsa yayınlama |
| Telif ihtarı | Sadece halk malı/özgün melodi, model lisans takibi |
| Algoritma değişimi | Çok dil, çok platform, müzik dağıtımı |
| GPU/üretim darboğazı | 7 gün stok, bulut GPU (RunPod vb.) yedek |
