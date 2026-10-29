# Lulu & Bobo — Çocuk Kanalı İşletme Planı

> Hedef: 0–6 yaş, global, çok dilli (EN + ES → PT → HI/ID/AR), AI destekli ama insan
> denetimli 3D çizgi film kanalı. Önce uzun video; Shorts uzun videodan kesilir. İlk 90 günde YPP kabulü.

## 1. Marka

| Öğe | Karar |
|---|---|
| Kanal adı | **Lulu & Bobo** (her dilde okunur; yayından önce marka/isim taraması yapılacak) |
| Slogan | EN "Sing, Learn, Giggle!" · ES "¡Canta, Aprende, Ríe!" · PT "Cante, Aprenda, Ria!" |
| Görsel stil | Yumuşak 3D, yuvarlak hatlar, doygun pastel, tek düz arka plan, büyük gözler |
| Ses | Kanal sesi: sıcak, neşeli genç kadın vokal (sabit ACE-Step ayarı / LoRA) |
| Jingle | 3 sn'lik "Lu-lu-Bo-bo!" — her videonun sonunda (marka hafızası) |

### Karakterler (özgün — mevcut hiçbir markaya benzetilmez)
- **Lulu** — 3 yaşında kirpi kız. Mercan rengi dikenleri, sarı tulum, meraklı, biraz yaramaz. Kancaların öznesi.
- **Bobo** — Lulu'nun babası, iri, sakin, kahverengi ayı. Yeşil kazak. "Ebeveyn + çocuk" kancası.
- **Zippy / Zipi** (TR: Zıpzıp) — Mavi kurbağa arkadaş. Komik düşmeler, ses efektleri.
- **Mimi** — Küçük beyaz karınca. Değerler hikâyelerinde "küçük ama yardımsever".

Karakter tutarlılığı: her karakter için 20–30 görsellik referans seti → Flux/SDXL karakter LoRA'sı →
tüm sahne görselleri bu LoRA ile üretilir → Wan2GP image-to-video. (`pipeline/bible/characters.yaml`)

## 2. İçerik stratejisi

**Kanca kopyalama kuralı:** Viral formatı (konu, süre, ritim, kanca anı, kamera, başlık kalıbı) 1:1
alırız. Rakibin özgün söz/melodisini, karelerini, karakter tasarımını ve thumbnail'ini **almayız**.
Halk malı tekerlemeler serbesttir; melodiyi kendimiz üretiriz.

### Model: önce uzun video, Shorts ondan
```
Haftada 6 yeni şarkı (her biri ~2 dk, 16:9)
  ├─ 2 uzun derleme: Perşembe ~8,5 dk (4 şarkı) · Pazar ~17 dk (6 şarkı + 2 tekrar)  → reklam arası (≥8 dk)
  └─ 7 Shorts: her şarkının en güçlü 20–40 sn'lik bölümü, otomatik 9:16 kesim     → keşif/büyüme
```
- Bir şarkı → 1–2 Shorts + birden fazla derlemede tekrar kullanım. Haftada 8 şarkı üretmek yerine 6.
- Shorts'ta duyulan nakarat uzun videodakiyle aynı: çocuk tanır, ebeveyn uzun videoyu açar.
- **Made for Kids kısıtı:** kart, bitiş ekranı ve yorum kapalı; Shorts'taki "ilgili video" bağlantısının
  çalışıp çalışmadığını ilk yüklemede Studio'da kontrol et. Çalışmıyorsa köprü = aynı karakter, aynı
  thumbnail dili, şarkı adının başlıkta aynen geçmesi ve oynatma listeleri.
- 2. haftadan itibaren derlemeler eski şarkılarla büyür: 4. haftada 20–30 dk, 8. haftada 45–60 dk.

### Hafta 1 — Ekim 2026 trend taramasına göre seçilen kancalar
(Tarama: 28 sorgu × 3 filtre, 13 dil, son 30 gün, 1.617 video / 591 kanal — `pipeline/trends.py`)

| Şarkı | Kanca | Trend kanıtı |
|---|---|---|
| Colorful Trucks 🚚 | Araçlar + renk öğrenme | Miuki "Naik Truk" 11M (bu ay), RoboSquad 22 dk araç derlemesi |
| Medicine Is Not Candy 💊 | Güvenlik masalı, "Dur!" anı | More Good Stories (ES): 69 günde günlük ~1,8M izlenme |
| Peekaboo 🙈 | Saklambaç + kıkırdama | Dino World "Peekaboo" 17 dk; NIOMAGIC 29 dk "Baby Giggles" |
| Boppy Boom Dance 💃 | Viral dans chant'ı (özgün) | "Dudi Dudi Dam Dam" dansı: 10M + 2,3M + 1,4M (ID/HI, bu ay) |
| My Wiggly Tooth 🦷 | Diş düştü anı + fırçalama | KingFoo Kids (ES) "¡Se le cayó un diente!" |
| I Share With You 🤝 | Paylaşma değeri | Leo & PawPaw (PT) tek video 15M; Minjee "Te Comparto" (ES) |

**Mevsim:** Kasım ortasından itibaren Noel/yılbaşı şarkıları çocuk kanallarında yılın en yüksek
trafiğini alır → 3. hafta Noel şarkıları (Jingle Bells gibi halk malı melodiler + özgün sözler),
4. hafta "Christmas Songs for Kids" uzun derlemesi.

### Dil açılımı
| Faz | Diller | Neden |
|---|---|---|
| Hafta 1 | **EN + ES** (iki ayrı kanal, aynı gün) | En büyük çocuk izleyicisi; ES'te yeni kanallar hızla büyüyor (More Good Stories, Ye-Ye Yeti, Lunito) |
| Hafta 3 | **PT** (Brezilya) | Leo & PawPaw örneği: 20 videoyla 26M; rekabet EN'den düşük |
| Ay 2+ | HI, ID, AR | Hacim çok yüksek ama RPM düşük ve klon kanalı dolu; ancak EN/ES tuttuktan sonra |

Her dil = ayrı kanal + ayrı seslendirme + yerelleştirilmiş söz (aynı dosyanın kopyası değil — "inauthentic
content" riskini azaltır). Görüntü dillerde ortak; sadece ses, altyazı ve metadata değişir.
Söz satır sayıları dillerde eşit tutulur, böylece aynı sahneler tüm dillerde senkron kalır.

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
| Shorts ortalama izlenme | 10K | 3 gün üst üste <1K → o kancayı bırak |
| Shorts → uzun video geçişi | Uzun videonun "trafik kaynakları"nda Shorts payı | düşükse başlık/thumbnail köprüsünü güçlendir |
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
