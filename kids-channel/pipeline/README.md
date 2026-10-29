# Lulu & Bobo üretim hattı

Bölüm YAML'ı → şarkı → vokal → sahne görseli → Wan2GP klipleri → FFmpeg montaj → metadata + kontrol listesi.

```
pipeline/
  config.yaml            araç komut şablonları (ACE-Step, Demucs, görsel, Wan2GP i2v/s2v)
  bible/characters.yaml  karakter görünüşü, LoRA, tetik kelime — tutarlılık kaynağı
  episodes/week01/*.yaml haftanın 7 bölümü (söz, sahne, prompt, başlık, etiket — TR/EN)
  kc.py                  orkestratör
  trends.py              haftalık YouTube trend taraması (yeni + hızlı büyüyen kanallar)
  out/<bölüm>/<dil>/     çıktılar (git'e girmez)
```

## Kurulum
1. Python 3.10+, `pip install pyyaml`, `ffmpeg`.
2. GPU makinede: [Wan2GP](https://github.com/deepbeepmeep/Wan2GP), [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5), `pip install demucs`, görsel üretim (ComfyUI veya diffusers + Flux/SDXL).
3. `config.yaml > tools` içindeki komutları kendi kurulumuna göre düzenle. Şablonlar örnektir;
   Wan2GP ve ACE-Step CLI argümanları sürüme göre değişir — kendi sürümünün `--help` çıktısına göre uyarla.
4. Karakter LoRA'larını eğit (`bible/characters.yaml > lora`): her karakter için 20–30 tutarlı referans görsel.
5. `assets/jingle.wav` (3 sn "Lu-lu-Bo-bo!") ekle — her videonun sonuna eklenir.

## Kullanım
```bash
python kc.py validate episodes/week01                 # şema + süre kontrolü
python kc.py plan     episodes/week01 --lang tr       # prompt, altyazı, metadata, checklist
python kc.py run      episodes/week01 --lang tr --dry-run      # komutları out/*/jobs.sh'a yaz
python kc.py run      episodes/week01 --lang tr                # gerçek üretim (GPU)
python kc.py run      episodes/week01 --lang tr --placeholder  # GPU'suz uçtan uca test
python kc.py run      episodes/week01 --lang en                # İngilizce versiyon
```
- Var olan çıktılar atlanır: yarıda kalan iş aynı komutla devam eder. Beğenmediğin bir klibi sil, tekrar çalıştır.
- `sing: true` sahneler vokal parçasıyla S2V (ağız senkronu), diğerleri I2V ile üretilir.
- Derleme bölümü (`compile:`) önce listelenen bölümlerin bitmiş olmasını ister; dikey Shorts'u bulanık arka planla 16:9'a yerleştirir.

## Her bölüm için çıktı
| Dosya | İçerik |
|---|---|
| `<id>_<dil>.mp4` | Yayına hazır video (altyazı + -14 LUFS + jingle) |
| `metadata.json` | Başlık, açıklama (+AI beyanı), etiketler, Made for Kids, thumbnail prompt'u |
| `checklist.md` | Yayın öncesi insan kontrolü — **işaretlenmeden yükleme yok** |
| `jobs.sh` | Çalıştırılan/çalıştırılacak araç komutları |

## Haftalık döngü
| Gün | İş |
|---|---|
| Pzt | `python trends.py trends.json` → yeni ve hızlı büyüyen kanallar |
| Sal | En iyi 3 kancayı seç, `episodes/weekNN/` altında YAML yaz (week01 şablon) |
| Çar–Cmt | Üretim + kontrol listesi |
| Paz | Gelecek haftanın 7 videosunu YouTube Studio'da zamanla (stokta hep 7 gün) |

## Hafta 1 yayın takvimi
| Gün | Bölüm | Süre | Kanca |
|---|---|---|---|
| Pzt | Havuç – Carrot (sebzeler, iki dilli) | 20 sn | Telugu Learning with Anika |
| Sal | Lolipop seviyor musun? (sürpriz çilek) | 13 sn | Father-daughter show |
| Çar | Lulu'nun sabah rutini | 34 sn | SM Bangla Daily |
| Per | Sihirli top makinesi (renkler) | 25 sn | Jugnu Kids |
| Cum | Kemerini tak, klik klik! | 30 sn | Bubu Arabic / Lunito |
| Cmt | Minik Mimi yardıma koşuyor | 50 sn | Agile Mind Cartoons |
| Paz | Haftanın derlemesi (16:9) | ~3 dk | Dino World / Cocomelon |

Önerilen yayın saati (TR): hafta içi 17:00–18:00, hafta sonu 09:00–10:00 (ebeveyn ekran saatleri).
İlk haftadan sonra YouTube Studio > Analytics > "İzleyicileriniz ne zaman YouTube'da" verisine göre ayarla.
