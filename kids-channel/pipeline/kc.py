#!/usr/bin/env python3
"""Lulu & Bobo üretim hattı orkestratörü — önce uzun video, Shorts ondan kesilir.

  python kc.py validate episodes/week01
  python kc.py plan     episodes/week01 --lang en
  python kc.py run      episodes/week01 --lang en [--dry-run] [--placeholder]
  python kc.py assemble episodes/week01/s1_trucks.yaml --lang es

İki bölüm türü var:
  type: song         2–3 dk'lık 16:9 şarkı. Bölümler (intro, verse1, chorus…) sahnelere,
                     sözün her satırı bir sahneye eşlenir; tekrar eden nakarat bir kez render edilir.
                     `shorts:` listesindeki bölüm aralıkları 9:16'ya kırpılıp ayrı Shorts olarak çıkar.
  type: compilation  Şarkıları art arda dizen ≥8 dk'lık uzun video (reklam arası eşiği).

`run` var olan çıktıları atlar; yarıda kalan iş aynı komutla devam eder.
`--placeholder` GPU olmadan tüm zinciri test etmek için eksikleri renkli kart ve sessizlikle doldurur.
"""
import argparse, json, math, shutil, subprocess, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
LANGS = ("en", "es", "pt", "hi", "ar", "id", "tr")
LYRIC_FREE = ("intro", "outro", "instrumental")
MIDROLL_SECONDS = 480


def load(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


CFG = load(ROOT / "config.yaml")
CHARS = load(ROOT / "bible/characters.yaml")
OUT = ROOT / CFG["paths"]["out"]


def episodes(target):
    p = Path(target)
    files = sorted(p.glob("*.yaml")) if p.is_dir() else [p]
    eps = [(f, load(f)) for f in files]
    eps = [(f, e) for f, e in eps if isinstance(e, dict) and e.get("type") in ("song", "compilation")]
    # şarkılar derlemelerden önce üretilmeli
    return sorted(eps, key=lambda fe: fe[1]["type"] != "song")


def loc(field, lang):
    """Çok dilli alanlarda istenen dil, yoksa İngilizce."""
    if isinstance(field, dict):
        return field.get(lang) or field.get("en") or ""
    return field or ""


def line_seconds(ep):
    return ep.get("beats_per_line", 8) * 60 / ep["bpm"]


# ---------- zaman çizelgesi ----------

def timeline(ep, lang, scale=1.0):
    """structure → [{key, section, dur, start, sub, scene}]; aynı key aynı klip demektir."""
    ls = line_seconds(ep)
    lyr = ep["lyrics"].get(lang, {})
    items, t = [], 0.0
    for occ, sec in enumerate(ep["structure"]):
        for i, sc in enumerate(ep["scenes"][sec]):
            if sec in LYRIC_FREE:
                dur, sub = sc.get("beats", 8) * 60 / ep["bpm"], ""
            else:
                dur, sub = ls, lyr[sec][i]
            dur *= scale
            items.append({"key": f"{sec}_{i}", "section": sec, "occ": occ, "dur": dur, "start": t,
                          "sub": sub, "scene": sc})
            t += dur
    return items, t


def short_range(ep, sh, tl):
    """Shorts'un ilk geçtiği yerdeki [başlangıç, süre] aralığı."""
    st, n = ep["structure"], len(sh["sections"])
    for i in range(len(st) - n + 1):
        if st[i:i + n] == sh["sections"]:
            break
    else:
        return None
    span = [it for it in tl if i <= it["occ"] < i + n]
    start = span[0]["start"]
    end = span[-1]["start"] + span[-1]["dur"]
    return start, end - start


# ---------- doğrulama ----------

def validate(ep, path):
    errs, total = [], 0.0
    for k in ("id", "type", "title", "description", "tags"):
        if k not in ep:
            errs.append(f"eksik alan: {k}")
    if ep.get("type") == "song":
        for k in ("bpm", "style", "structure", "scenes", "lyrics", "hook"):
            if k not in ep:
                errs.append(f"eksik alan: {k}")
        if errs:
            return [f"{path.name}: {e}" for e in errs], 0
        for sec in set(ep["structure"]):
            if sec not in ep["scenes"]:
                errs.append(f"sahnesi olmayan bölüm: {sec}")
                continue
            for sc in ep["scenes"][sec]:
                for c in sc.get("chars", []):
                    if c not in CHARS:
                        errs.append(f"{sec}: bilinmeyen karakter {c}")
                if not {"chars", "image", "motion"} <= sc.keys():
                    errs.append(f"{sec}: sahnede chars/image/motion eksik")
            if sec in LYRIC_FREE:
                continue
            for lang, lyr in ep["lyrics"].items():
                if len(lyr.get(sec, [])) != len(ep["scenes"][sec]):
                    errs.append(f"{lang}/{sec}: {len(lyr.get(sec, []))} satır ≠ {len(ep['scenes'][sec])} sahne")
        if errs:
            return [f"{path.name}: {e}" for e in errs], 0
        tl, total = timeline(ep, "en")
        for sh in ep.get("shorts", []):
            r = short_range(ep, sh, tl)
            if not r:
                errs.append(f"short {sh['id']}: {sh['sections']} structure içinde ardışık değil")
            elif r[1] > 58:
                errs.append(f"short {sh['id']}: {r[1]:.0f} sn > 58 sn")
    elif ep.get("type") == "compilation":
        songs = {e["id"]: e for _, e in episodes(path.parent) if e["type"] == "song"}
        for s in ep.get("items", []):
            if s not in songs:
                errs.append(f"bilinmeyen şarkı: {s}")
            else:
                total += timeline(songs[s], "en")[1]
        if total and total < MIDROLL_SECONDS:
            errs.append(f"{total/60:.1f} dk < 8 dk (reklam arası alamaz)")
    else:
        errs.append("type song|compilation olmalı")
    return [f"{path.name}: {e}" for e in errs], total


# ---------- planlama ----------

def scene_prompt(scene):
    chars = ", ".join(CHARS[c]["look"].strip() for c in scene["chars"])
    return f"{CFG['style'].strip()}, {chars}, {scene['image'].strip()}"


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def write_srt(path, items, offset=0.0):
    out = []
    for it in items:
        if it["sub"]:
            a = it["start"] - offset
            out.append(f"{len(out)+1}\n{srt_time(a)} --> {srt_time(a+it['dur'])}\n{it['sub']}\n")
    path.write_text("\n".join(out), encoding="utf-8")


def ace_lyrics(ep, lang):
    """ACE-Step formatında söz: [verse] / [chorus] etiketleri, structure sırasıyla."""
    out = []
    for sec in ep["structure"]:
        if sec in LYRIC_FREE:
            out.append(f"[{'inst' if sec != 'outro' else 'outro'}]")
        else:
            tag = "chorus" if sec.startswith("chorus") else "bridge" if sec.startswith("bridge") else "verse"
            out.append(f"[{tag}]\n" + "\n".join(ep["lyrics"][lang][sec]))
    return "\n\n".join(out) + "\n"


def media_len(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def write_meta(d, name, src, lang, kind):
    tags = src.get("tags", {})
    meta = {
        "kind": kind, "title": loc(src["title"], lang),
        "description": loc(src["description"], lang) + "\n\n" + loc(DISCLOSURE, lang),
        "tags": tags.get(lang, tags.get("en", [])) if isinstance(tags, dict) else tags,
        "madeForKids": True, "alteredOrSynthetic": True,
    }
    if src.get("thumbnail"):
        meta["thumbnail_prompt"] = f"{CFG['style'].strip()}, {src['thumbnail']}"
    (d / f"{name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def plan(ep, lang):
    d = OUT / ep["id"] / lang
    d.mkdir(parents=True, exist_ok=True)
    (d / "checklist.md").write_text(CHECKLIST.format(id=ep["id"], lang=lang), encoding="utf-8")
    if ep["type"] == "compilation":
        write_meta(d, "metadata", ep, lang, "long")
        return d, {"id": ep["id"], "type": "compilation", "items": ep["items"]}
    song = d / "song.wav"
    planned = timeline(ep, lang)[1]
    # şarkı üretildiyse sahneleri gerçek şarkı süresine orantılı yay
    scale = media_len(song) / planned if song.exists() and media_len(song) else 1.0
    tl, total = timeline(ep, lang, scale)
    (d / "lyrics.txt").write_text(ace_lyrics(ep, lang), encoding="utf-8")
    write_srt(d / "subs.srt", tl)
    clip_s = CFG["video"]["clip_seconds"]
    renders = {}
    for it in tl:
        r = renders.setdefault(it["key"], {
            "key": it["key"], "first_start": it["start"], "dur": it["dur"],
            "clips": math.ceil(it["dur"] / clip_s - 1e-6), "sing": bool(it["scene"].get("sing")),
            "image_prompt": scene_prompt(it["scene"]), "motion": it["scene"]["motion"].strip(),
            "loras": ",".join(CHARS[c]["lora"] for c in it["scene"]["chars"]),
        })
        r["uses"] = r.get("uses", 0) + 1
    write_meta(d, "metadata", ep, lang, "song")
    shorts = []
    for sh in ep.get("shorts", []):
        start, dur = short_range(ep, sh, tl)
        shorts.append({"id": sh["id"], "start": start, "dur": dur})
        write_meta(d, f"short_{sh['id']}", sh, lang, "short")
    p = {"id": ep["id"], "type": "song", "lang": lang, "duration": total, "scale": scale,
         "music": {"style": ep["style"], "bpm": ep["bpm"], "duration": math.ceil(planned)},
         "timeline": [{k: v for k, v in it.items() if k != "scene"} for it in tl],
         "renders": list(renders.values()), "shorts": shorts}
    (d / "plan.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    return d, p


DISCLOSURE = {
    "en": "Made with the help of AI tools; songs and stories are written and every frame is reviewed by our team.",
    "es": "Hecho con ayuda de herramientas de IA; canciones y cuentos escritos y revisados cuadro por cuadro por nuestro equipo.",
    "pt": "Feito com ajuda de ferramentas de IA; músicas e histórias escritas e revisadas quadro a quadro pela nossa equipe.",
    "tr": "AI araçları yardımıyla üretildi; şarkı ve hikâyeler ekibimizce yazılıp her kare denetlendi.",
}

CHECKLIST = """# Yayın öncesi kontrol — {id} ({lang})
- [ ] Anatomi: fazla parmak / eriyen yüz / göz kayması yok
- [ ] Korkutucu ifade, tehlikeli davranış özendirmesi yok
- [ ] Karakterler bible ile tutarlı (renk, kıyafet)
- [ ] Sözler anadil konuşanı tarafından kontrol edildi, altyazı senkronu doğru
- [ ] 9:16 kesimde karakter kadrajın içinde
- [ ] Ses -14 LUFS civarı, ani gürültü yok
- [ ] Başka markaya benzeyen öğe yok (karakter, logo, thumbnail, melodi)
- [ ] Made for Kids = evet, Altered/synthetic beyanı işaretli
"""


# ---------- araç çalıştırma ----------

class Runner:
    def __init__(self, d, dry):
        self.d, self.dry = d, dry
        self.jobs = d / "jobs.sh"
        self.jobs.write_text("#!/bin/sh\nset -e\n")

    def tool(self, name, out, **kw):
        out = Path(out)
        if out.exists():
            return True
        tmpl = (CFG["tools"].get(name) or "").strip()
        if not tmpl:
            return False
        cmd = tmpl.format(out=out, **kw)
        with self.jobs.open("a") as f:
            f.write(cmd + "\n")
        if self.dry:
            return False
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(cmd, shell=True, cwd=ROOT)
        if r.returncode:
            print(f"  ! {name} başarısız ({r.returncode}): {cmd}", file=sys.stderr)
        return out.exists()


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], check=True)


def size(fmt):
    v = CFG["video"][fmt]
    return v["w"], v["h"]


COLORS = ["0xFFB3C7", "0xB3E5FC", "0xC8E6C9", "0xFFF59D", "0xD1C4E9", "0xFFCCBC"]


def produce(ep, lang, dry=False, placeholder=False):
    d, p = plan(ep, lang)
    if p["type"] != "song":
        return d, p
    r = Runner(d, dry)
    w, h = size("long")
    song = d / "song.wav"
    vocals = d / "stems/htdemucs/song/vocals.wav"
    ok = r.tool("music", song, style=p["music"]["style"], lyrics_file=d / "lyrics.txt",
                duration=p["music"]["duration"], bpm=p["music"]["bpm"])
    if not ok and placeholder:
        ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", p["duration"], song)
    if song.exists():
        if p["scale"] == 1.0 and not placeholder:
            d, p = plan(ep, lang)  # gerçek şarkı süresine göre yeniden zamanla
        r.tool("stems", vocals, out_dir=d / "stems", song=song)
    clip_s = CFG["video"]["clip_seconds"]
    for n, s in enumerate(p["renders"]):
        img = d / f"img/{s['key']}.png"
        if not r.tool("image", img, prompt=s["image_prompt"].replace('"', "'"), negative=CFG["negative"],
                      loras=s["loras"], w=w, h=h) and placeholder:
            img.parent.mkdir(exist_ok=True)
            ff("-f", "lavfi", "-i", f"color=c={COLORS[n % len(COLORS)]}:s={w}x{h}",
               "-vf", f"drawtext=text='{s['key']}':fontsize={h//8}:x=(w-tw)/2:y=(h-th)/2",
               "-frames:v", 1, img)
        for c in range(s["clips"]):
            clip = d / f"clips/{s['key']}_{c}.mp4"
            if s["sing"] and vocals.exists():
                seg = d / f"clips/{s['key']}_{c}.wav"
                if not seg.exists():
                    seg.parent.mkdir(exist_ok=True)
                    ff("-ss", s["first_start"] + c * clip_s, "-t", clip_s, "-i", vocals, seg)
                ok = r.tool("s2v", clip, image=img, audio=seg, prompt=s["motion"].replace('"', "'"))
            else:
                ok = r.tool("i2v", clip, image=img, prompt=s["motion"].replace('"', "'"), seconds=clip_s)
            if not ok and placeholder and img.exists():
                clip.parent.mkdir(exist_ok=True)
                ff("-loop", 1, "-i", img, "-t", clip_s, "-r", CFG["video"]["fps"],
                   "-vf", f"scale={w}:{h}", "-pix_fmt", "yuv420p", clip)
    return d, p


# ---------- montaj ----------

ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", 44100, "-ac", 2]


def subs_filter(srt, vertical=False):
    style = "Fontsize=14,Bold=1,Outline=2,MarginV=40" if vertical else "Fontsize=22,Bold=1,Outline=2,MarginV=30"
    # Windows'ta "C:/..." içindeki iki nokta ffmpeg filtre ayırıcısıyla çakışır
    path = Path(srt).resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
    return f"subtitles={path}:force_style='{style}'"


def jingle(d, fmt):
    src = ROOT / CFG["paths"]["jingle"]
    if not src.exists():
        return None
    w, h = size(fmt)
    out = d / f"jingle_{fmt}.mp4"
    if not out.exists():
        ff("-f", "lavfi", "-i", f"color=c=0xFFB3C7:s={w}x{h}:r={CFG['video']['fps']}", "-i", src,
           "-shortest", *ENC, out)
    return out


def concat(parts, final):
    lst = final.with_suffix(".txt")
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in parts))
    ff("-f", "concat", "-safe", 0, "-i", lst, *ENC, final)


def assemble(ep, lang, burn_subs=True):
    d, p = plan(ep, lang)
    w, h = size("long")
    fps = CFG["video"]["fps"]
    if p["type"] == "compilation":
        parts = []
        for ref in p["items"]:
            f = OUT / ref / lang / f"{ref}_{lang}.mp4"
            if not f.exists():
                sys.exit(f"derleme için önce {ref} birleştirilmeli: {f}")
            parts.append(f)
        j = jingle(d, "long")
        final = d / f"{ep['id']}_{lang}.mp4"
        concat(parts + ([j] if j else []), final)
        print(f"✓ {final} ({media_len(final)/60:.1f} dk)")
        return
    segs = {}
    for s in p["renders"]:
        clips = [d / f"clips/{s['key']}_{c}.mp4" for c in range(s["clips"])]
        missing = [c for c in clips if not c.exists()]
        if missing:
            sys.exit(f"eksik klip: {missing[0]} (önce `run`, GPU yoksa --placeholder)")
        seg = d / f"seg_{s['key']}.mp4"
        lst = d / f"seg_{s['key']}.txt"
        lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
        ff("-f", "concat", "-safe", 0, "-i", lst, "-t", f"{s['dur']:.3f}", "-an",
           "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},format=yuv420p",
           seg)
        segs[s["key"]] = seg
    lst = d / "timeline.txt"
    lst.write_text("".join(f"file '{segs[it['key']].resolve()}'\n" for it in p["timeline"]))
    video = d / "video_only.mp4"
    ff("-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", video)
    song = d / "song.wav"
    audio = ["-i", song] if song.exists() else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    clean = d / "clean.mp4"  # altyazısız: Shorts buradan kesilir
    ff("-i", video, *audio, "-map", "0:v", "-map", "1:a", "-t", f"{p['duration']:.3f}",
       "-af", "loudnorm=I=-14:TP=-1.5", *ENC, clean)
    final = d / f"{ep['id']}_{lang}.mp4"
    if burn_subs and (d / "subs.srt").stat().st_size:
        ff("-i", clean, "-vf", subs_filter(d / "subs.srt"), "-c:a", "copy", "-c:v", "libx264",
           "-pix_fmt", "yuv420p", final)
    else:
        shutil.copy(clean, final)
    print(f"✓ {final} ({media_len(final):.0f} sn)")
    sw, sh_ = size("short")
    for sh in p["shorts"]:
        items = [it for it in p["timeline"] if sh["start"] - 1e-3 <= it["start"] < sh["start"] + sh["dur"] - 1e-3]
        srt = d / f"short_{sh['id']}.srt"
        write_srt(srt, items, offset=sh["start"])
        vf = f"crop=ih*9/16:ih,scale={sw}:{sh_},fps={fps},format=yuv420p"
        if burn_subs and srt.stat().st_size:
            vf += "," + subs_filter(srt, vertical=True)
        body = d / f"short_{sh['id']}_body.mp4"
        ff("-ss", f"{sh['start']:.3f}", "-t", f"{sh['dur']:.3f}", "-i", clean, "-vf", vf, *ENC, body)
        out = d / f"short_{sh['id']}_{lang}.mp4"
        j = jingle(d, "short")
        concat([body, j], out) if j else shutil.copy(body, out)
        print(f"  ✓ Shorts {out.name} ({media_len(out):.0f} sn)")


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["validate", "plan", "run", "assemble"])
    ap.add_argument("target", help="bölüm .yaml dosyası veya klasörü")
    ap.add_argument("--lang", default="en", choices=LANGS)
    ap.add_argument("--dry-run", action="store_true", help="komutları yalnızca jobs.sh'a yaz")
    ap.add_argument("--placeholder", action="store_true", help="GPU olmadan test: eksikleri kartla doldur")
    ap.add_argument("--no-subs", action="store_true")
    a = ap.parse_args()
    eps = episodes(a.target)
    if a.cmd == "validate":
        bad = 0
        for f, ep in eps:
            errs, total = validate(ep, f)
            bad += len(errs)
            extra = f", {len(ep.get('shorts', []))} Shorts" if ep.get("type") == "song" else ""
            print(("✗ " if errs else "✓ ") + f"{f.name}: {ep.get('type')} {total/60:.1f} dk{extra}"
                  + "".join(f"\n    {e}" for e in errs))
        sys.exit(1 if bad else 0)
    for f, ep in eps:
        if a.cmd == "plan":
            d, p = plan(ep, a.lang)
            if p["type"] == "song":
                print(f"✓ {ep['id']}: {p['duration']:.0f} sn, {len(p['renders'])} benzersiz sahne, "
                      f"{sum(r['clips'] for r in p['renders'])} klip, {len(p['shorts'])} Shorts → {d}")
            else:
                print(f"✓ {ep['id']}: derleme {len(p['items'])} şarkı → {d}")
        elif a.cmd == "run":
            produce(ep, a.lang, a.dry_run or a.placeholder, a.placeholder)
            if not a.dry_run:
                assemble(ep, a.lang, not a.no_subs)
        else:
            assemble(ep, a.lang, not a.no_subs)


if __name__ == "__main__":
    main()
