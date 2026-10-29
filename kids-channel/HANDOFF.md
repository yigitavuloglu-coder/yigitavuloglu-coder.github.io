# DEVİR — Lulu & Bobo çocuk kanalı

> Bu dosya bulut oturumundan kullanıcının Windows PC'sindeki yeni Claude Code oturumuna devir içindir.
> Yeni oturum: önce bu dosyayı, sonra `PLAN.md` ve `pipeline/README.md`'yi oku. Kullanıcıyla Türkçe konuş.
> Tarih: 29 Ekim 2026. Branch: `ccr-77e59dfe-ec4l4h` (PR #1, taslak).

## 1. Proje bir paragrafta

Global (EN + ES, sonra PT) 0–6 yaş çocuk şarkıları kanalı: **Lulu & Bobo**. Özgün 4 karakter
(Lulu kirpi kız, Bobo ayı baba, Zippy kurbağa, Mimi karınca). Viral kancalar YouTube trend taramasından
1:1 alınır, ama söz, melodi ve karakterler özgündür. Üretim AI ile (ACE-Step şarkı, Wan2GP animasyon),
her video yayından önce insan kontrolünden geçer. **Önce uzun video**: her şarkı ~2 dk 16:9 üretilir,
şarkılar ≥8 dk derlemelere dizilir (reklam arası), Shorts şarkıların bölümlerinden otomatik 9:16 kesilir.

## 2. Kullanıcının verdiği kararlar (yeniden tartışma)

| Karar | Ayrıntı |
|---|---|
| Araç | Wan2GP (yerel GPU) + açık kaynak, ticari lisanslı modeller |
| Kanca | Viral formatlar 1:1 kopyalanır; karakterler/söz/melodi özgün |
| Diller | Türkçe şart değil. EN + ES ile başla, PT 3. hafta |
| Format | Uzun video öncelikli; Shorts uzun videodan kesilir, uzun videoya yönlendirir |
| Skill | `jakeschincariol/youtube-agent-skill` → `.claude/skills/yt-*` olarak kuruldu |
| Çalışma yeri | Üretim kullanıcının PC'sinde (bulutta GPU yok) |

**Açık karar (kullanıcıya sor):** Kullanıcı "her gün 1 uzun + 3 Shorts" önerdi. Benim önerim:
Hafta 1–2'de günde 3 Shorts + haftada 2–3 uzun video; katalog ~25–30 şarkıya ulaşınca günde 1 uzun
(her birinde ≥1–2 yeni şarkı). Gerekçe: 6 şarkıyla her gün yeni uzun video = aynı şarkıların
karışımı → "reused/inauthentic content" riski ve videoların birbirini yemesi. Bunun için haftalık
üretimi 6 → 8–10 şarkıya çıkarmak gerekir. `episodes/week01/schedule.yaml` şu an eski takvimde
(günde 1 Shorts, 4. ve 7. gün uzun); karar gelince güncelle.

## 3. Repo haritası

```
CLAUDE.md                         → bu dosyaya yönlendirir
.claude/skills/yt-*/              youtube-agent-skill (MIT, commit a2feb21): yt-script, yt-package,
                                  yt-seo, yt-shorts, yt-plan, yt-viral, yt-retention, yt-chapters, yt-audit...
kids-channel/
  PLAN.md                         iş planı, trend kanıtları, dil açılımı, politikalar, KPI, riskler
  HANDOFF.md                      bu dosya
  voice.md                        kanal ses profili (yt-* skill'leri için)
  pipeline/
    kc.py                         orkestratör: validate / plan / run / assemble
    config.yaml                   araç komut ŞABLONLARI (doğrulanmadı, bkz. §5)
    bible/characters.yaml         karakter görünüşü, LoRA yolu, tetik kelime
    episodes/week01/              s1–s6 şarkılar (EN/ES/PT söz + sahneler), c1/c2 derlemeler, schedule.yaml
    trends.py                     YouTube trend tarayıcı (API anahtarı gerektirmez)
```

## 4. Durum

**Bitti ve test edildi (bulutta, GPU'suz `--placeholder` modu):**
- `kc.py validate episodes/week01` → 8/8 geçer.
- `kc.py run episodes/week01 --lang es --placeholder` → 6 şarkı (1920×1080, 116–135 sn),
  7 Shorts (1080×1920, 17–40 sn), c1 8,4 dk, c2 16,9 dk. Altyazı/sahne eşleşmesi kontrol edildi.
- Hafta 1 içerik: 6 şarkı × 3 dil söz, sahne prompt'ları, başlık/açıklama/etiket, 7 Shorts başlığı.

**Hiç çalıştırılmadı (asıl iş burada):**
- Gerçek ACE-Step, Demucs, görsel üretim ve Wan2GP komutları. `config.yaml > tools` örnek şablondur.
- `tools/gen_image.py` **yok** — config ona işaret ediyor, yazılması gerekiyor.
- Karakter LoRA'ları yok (`loras/*.safetensors`). `assets/jingle.wav` yok (yoksa atlanır).
- Windows'ta hiç denenmedi. Altyazı yolu için Windows düzeltmesi var (`subs_filter`), ama test edilmedi.

## 5. PC'de ilk görev: ilk uzun videoyu yayına hazır hale getir

Hedef: **`c1_trucks_peekaboo_mix` (EN)** — s1 Trucks + s3 Peekaboo + s2 Medicine + s4 Dance, ~8,5 dk —
ve bu dört şarkıdan çıkan 4 Shorts. Bitince kullanıcıya kontrol için gönder.

1. **Donanımı öğren:** `nvidia-smi` (GPU modeli, VRAM), boş disk (modeller ~60–100 GB tutar).
   12 GB altı VRAM'de Wan 2.2 5B / düşük VRAM profilleri; 24 GB'de 14B I2V.
2. **Kur:** Python 3.10/3.11, ffmpeg (PATH'te), Git. Sonra:
   - Wan2GP: https://github.com/deepbeepmeep/Wan2GP — README'deki Windows kurulumunu izle.
   - ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5 — MIT lisans.
   - `pip install demucs pyyaml`
   - Görsel: diffusers (Flux.1-dev lisansı ticari kısıtlı! → FLUX.1-schnell Apache 2.0 veya SDXL) ya da ComfyUI.
3. **Araç komutlarını doğrula ve `config.yaml > tools`'u düzelt.** Her aracın gerçek CLI'ını `--help` ile
   kontrol et. Wan2GP bir Gradio arayüzüdür; toplu iş için CLI/kuyruk desteği yoksa `gradio_client`
   ile çağıran küçük bir `tools/wan_i2v.py` yaz. Aynısı ACE-Step için. Şablon yer tutucuları:
   music `{style} {lyrics_file} {bpm} {duration} {out}`, stems `{out_dir} {song}`,
   image `{prompt} {negative} {loras} {w} {h} {out}`, i2v `{image} {prompt} {seconds} {out}`,
   s2v `{image} {audio} {prompt} {out}`.
4. **Karakter tutarlılığı (kullanıcıya seçenek sun):**
   a) Hızlı: LoRA'sız; her karakter için bir referans görsel üret, sahne görsellerini
      görsel-düzenleme/referans modeliyle (ör. Qwen-Image-Edit, Flux Kontext — lisansları kontrol et)
      bu referanstan türet.
   b) Sağlam: karakter başına 20–30 görsellik set → LoRA eğit (ai-toolkit / kohya_ss) → `bible`'daki yollar.
5. **Önce tek şarkı:** `python kc.py run episodes/week01/s1_trucks.yaml --lang en`. Şarkıyı dinle,
   5–6 sahneye bak, kullanıcıya göster, onay al. Sonra kalan 3 şarkı, sonra
   `python kc.py assemble episodes/week01/c1_mix.yaml --lang en`.
6. **Yayın paketi:** her video için `checklist.md`'yi gerçekten kontrol et; `metadata.json`'daki başlığı
   `/yt-package` ile lint et; thumbnail üret (`thumbnail_prompt`); `/yt-seo` ile açıklamayı son haline getir.
7. **Kullanıcıya gönder:** final mp4'ler, thumbnail'ler, başlık/açıklama/etiketler. YouTube'a yükleme
   kullanıcının işi (yt-* skill'leri de yayınlamaz).

## 6. Bilinen riskler / dikkat

- **Altyazı senkronu:** sahneler bpm'den hesaplanır ve gerçek şarkı süresine orantılı esnetilir;
  ACE-Step tempoyu tutmazsa kayar. Gerekirse şarkıya whisper ile zaman hizalaması ekle.
- **Dil başına üretim:** her dil için görseller ayrı üretilir. GPU tasarrufu için EN'deki `img/` ve
  `clips/`'i diğer dillere kopyala; sadece `sing: true` S2V klipleri dile özel olmalı.
- **Made for Kids:** kart/bitiş ekranı/yorum kapalı. Shorts'taki "ilgili video" bağlantısı MFK'da
  çalışıyor mu — ilk yüklemede Studio'da kontrol edilecek, doğrulanmadı.
- **Lisanslar:** ACE-Step (MIT), Wan 2.x (Apache 2.0), Demucs (MIT). MusicGen, LeVo, YuE2, FLUX.1-dev
  ticari kullanımda sorunlu — kullanma.
- **yt-plan çakışması:** `/yt-plan` skill'i "haftada 3 yükleme" der; bu kanalın stratejisi farklı
  (çocuk kanalları yüksek frekansla büyür). PLAN.md önceliklidir.
- **Repo büyük ihtimalle herkese açık** (`*.github.io`). Plan ve senaryolar görünür. Kullanıcı isterse
  özel repoya taşı. `out/`, `loras/`, `*.safetensors` git'e girmez (`.gitignore`).

## 7. Sonraki haftalar (PLAN.md'de ayrıntı)

- Hafta 2: yeni 6–10 şarkı (her pazartesi `python pipeline/trends.py trends.json` ile trend taraması).
- Hafta 3: Noel şarkıları (Kasım ortası–Aralık en yüksek trafik), PT kanalı.
- Hafta 4: "Christmas Songs for Kids" uzun derleme.
