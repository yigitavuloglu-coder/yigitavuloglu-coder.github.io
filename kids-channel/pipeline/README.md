# Lulu & Bobo üretim hattı

Önce uzun video, Shorts ondan kesilir:

```
şarkı YAML'ı (söz EN/ES/PT + sahneler)
  → ACE-Step şarkı (dil başına) → Demucs vokal
  → Flux/SDXL + karakter LoRA görseller (16:9, karakter ortada)
  → Wan2GP: I2V sahneler + S2V/InfiniteTalk şarkı söyleyen sahneler (nakarat bir kez render edilir)
  → FFmpeg: 16:9 şarkı videosu + altyazı + -14 LUFS
       ├─ shorts: bölüm aralığı → 9:16 merkez kırpma + altyazı + jingle
       └─ compilation: şarkılar art arda ≥8 dk + jingle
```

```
pipeline/
  config.yaml            araç komut şablonları (ACE-Step, Demucs, görsel, Wan2GP i2v/s2v)
  bible/characters.yaml  karakter görünüşü, LoRA, tetik kelime, dillerdeki adları
  episodes/week01/       6 şarkı (s*.yaml), 2 derleme (c*.yaml), schedule.yaml
  kc.py                  orkestratör
  trends.py              haftalık YouTube trend taraması
  out/<id>/<dil>/        çıktılar (git'e girmez)
```

## Kurulum
1. Python 3.10+, `pip install pyyaml`, `ffmpeg`.
2. GPU makinede: [Wan2GP](https://github.com/deepbeepmeep/Wan2GP), [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5), `pip install demucs`, görsel üretim (ComfyUI veya diffusers + Flux/SDXL).
3. `config.yaml > tools` komutlarını kendi kurulumuna göre düzenle. Şablonlar örnektir; Wan2GP ve
   ACE-Step argümanları sürüme göre değişir — kendi sürümünün `--help` çıktısına göre uyarla.
4. Karakter LoRA'larını eğit (`bible/characters.yaml > lora`): karakter başına 20–30 tutarlı referans görsel.
5. `assets/jingle.wav` (3 sn "Lu-lu-Bo-bo!") ekle.

## Kullanım
```bash
python kc.py validate episodes/week01                       # şema, satır=sahne, Shorts ≤58 sn, derleme ≥8 dk
python kc.py plan     episodes/week01 --lang en             # prompt, söz, altyazı, metadata, checklist
python kc.py run      episodes/week01 --lang en --dry-run   # komutları out/*/jobs.sh'a yaz
python kc.py run      episodes/week01 --lang en             # gerçek üretim (GPU)
python kc.py run      episodes/week01 --lang es             # İspanyolca: aynı görseller değil, aynı prompt'lar
python kc.py run      episodes/week01 --lang en --placeholder   # GPU'suz uçtan uca test
```
- Var olan çıktılar atlanır; beğenmediğin klibi sil, tekrar çalıştır.
- Şarkı üretildikten sonra sahne süreleri gerçek şarkı süresine orantılı yayılır. ACE-Step tempoyu
  birebir tutmazsa altyazı kayabilir — kontrol listesinde senkronu mutlaka izle.
- Görseller dil klasörüne göre ayrı üretilir. GPU tasarrufu için EN'deki `img/` ve `clips/` klasörlerini
  diğer dillere kopyalayabilirsin; sadece `sing: true` sahnelerin S2V klipleri dile özel kalmalı.

## Bölüm şeması (`type: song`)
```yaml
id: s1_colorful_trucks
type: song
bpm: 100                 # beats_per_line (vars. 8) ile her söz satırı = 1 sahne süresi
structure: [intro, verse1, chorus, verse2, chorus, verse3, chorus, outro]
scenes:                  # bölüm başına sahne listesi; intro/outro'da `beats` ile süre
  verse1: [{chars: [lulu], image: "...", motion: "...", sing: true}, ...]
lyrics:                  # her dilde her bölümün satır sayısı = o bölümün sahne sayısı
  en: {verse1: [...], chorus: [...]}
  es: {...}
shorts:                  # structure içinde ardışık bölümler; ilk geçtiği yerden kesilir
  - {id: trucks_chorus, sections: [chorus], title: {en: ..., es: ...}, ...}
```

## Her şarkı için çıktı (`out/<id>/<dil>/`)
| Dosya | İçerik |
|---|---|
| `<id>_<dil>.mp4` | 16:9 şarkı videosu (derlemelerin yapı taşı) |
| `short_<shortid>_<dil>.mp4` + `.json` | Yayına hazır Shorts + başlık/açıklama/etiket |
| `metadata.json`, `checklist.md` | Metadata (Made for Kids, AI beyanı) ve yayın öncesi kontrol |
| `lyrics.txt`, `subs.srt`, `jobs.sh` | ACE-Step sözü, altyazı, araç komutları |

## Hafta 1 yayın takvimi (`episodes/week01/schedule.yaml`)
| Gün | Shorts | Uzun video |
|---|---|---|
| 1 | Beep beep! Colorful trucks 🚚 | — |
| 2 | Where is Lulu? Peekaboo 🙈 | — |
| 3 | Boppy boppy boom boom! 💃 | — |
| 4 | Is it candy? STOP! 💊 | **Trucks + Peekaboo + Boppy Dance** (~8,5 dk) |
| 5 | One big bite... POP! 🦷 | — |
| 6 | One for you, one for me 🍪 | — |
| 7 | Share my umbrella ☔ | **Lulu & Bobo Kids Songs** (~17 dk) |

EN ve ES kanallarına aynı gün; saatler hedef pazarın yerel saatine göre (`schedule.yaml`).
İlk haftadan sonra Studio > Analytics > "İzleyicileriniz ne zaman YouTube'da" verisine göre ayarla.

## Haftalık döngü
| Gün | İş |
|---|---|
| Pzt | `python trends.py trends.json` → bu ay yükselen kancalar ve yeni kanallar |
| Sal | En güçlü 4–6 kancayı seç, `episodes/weekNN/` altında şarkı YAML'larını yaz (week01 şablon) |
| Çar–Cmt | Üretim + kontrol listesi (EN önce, sonra ES/PT) |
| Paz | Gelecek haftanın 7 Shorts + 2 uzun videosunu zamanla (stokta hep 1 hafta) |
