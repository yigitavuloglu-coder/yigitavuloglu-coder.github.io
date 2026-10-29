#!/usr/bin/env python3
"""Lulu & Bobo üretim hattı orkestratörü.

  python kc.py validate episodes/week01
  python kc.py plan     episodes/week01 --lang tr
  python kc.py run      episodes/week01/d1_havuc.yaml --lang tr [--dry-run] [--placeholder]
  python kc.py assemble episodes/week01/d1_havuc.yaml --lang tr [--placeholder]

`run` = plan + müzik + vokal ayrımı + görsel + video + montaj. Var olan çıktılar atlanır,
bu yüzden yarıda kalan bir iş aynı komutla devam ettirilir.
`--placeholder` GPU olmadan tüm zinciri test etmek için eksik görsel/klip/şarkı yerine
renkli kart ve sessizlik üretir.
"""
import argparse, json, math, shlex, shutil, subprocess, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
LANGS = ("tr", "en", "es", "ar", "pt", "id")
SCENE_KEYS = {"dur", "chars", "image", "motion"}


def load(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


CFG = load(ROOT / "config.yaml")
CHARS = load(ROOT / "bible/characters.yaml")
OUT = ROOT / CFG["paths"]["out"]


def episodes(target):
    p = Path(target)
    files = sorted(p.glob("*.yaml")) if p.is_dir() else [p]
    return [(f, load(f)) for f in files]


def loc(field, lang):
    """Çok dilli alanlarda istenen dil, yoksa İngilizce, yoksa Türkçe."""
    if isinstance(field, dict):
        return field.get(lang) or field.get("en") or field.get("tr") or ""
    return field or ""


# ---------- doğrulama ----------

def validate(ep, path):
    errs = []
    for k in ("id", "day", "format", "title", "description", "tags", "hook"):
        if k not in ep:
            errs.append(f"eksik alan: {k}")
    if ep.get("format") not in ("short", "long"):
        errs.append("format short|long olmalı")
    for i, s in enumerate(ep.get("scenes", [])):
        miss = SCENE_KEYS - s.keys()
        if miss:
            errs.append(f"sahne {i+1}: eksik {sorted(miss)}")
        for c in s.get("chars", []):
            if c not in CHARS:
                errs.append(f"sahne {i+1}: bilinmeyen karakter {c}")
    if not ep.get("scenes") and not ep.get("compile"):
        errs.append("scenes veya compile gerekli")
    total = sum(s.get("dur", 0) for s in ep.get("scenes", []))
    if ep.get("format") == "short" and total > 60:
        errs.append(f"Shorts 60 sn'yi geçiyor ({total} sn)")
    return [f"{path.name}: {e}" for e in errs], total


# ---------- planlama ----------

def scene_prompt(scene):
    chars = ", ".join(CHARS[c]["look"].strip() for c in scene["chars"])
    return f"{CFG['style'].strip()}, {chars}, {scene['image'].strip()}"


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def plan(ep, lang):
    d = OUT / ep["id"] / lang
    d.mkdir(parents=True, exist_ok=True)
    clip_s = CFG["video"]["clip_seconds"]
    scenes, t, srt = [], 0.0, []
    for i, s in enumerate(ep.get("scenes", []), 1):
        sub = loc(s.get("sub"), lang)
        if sub:
            srt.append(f"{len(srt)+1}\n{srt_time(t)} --> {srt_time(t+s['dur'])}\n{sub}\n")
        scenes.append({
            "n": i, "dur": s["dur"], "start": t, "sing": bool(s.get("sing")),
            "clips": math.ceil(s["dur"] / clip_s),
            "image_prompt": scene_prompt(s), "motion": s["motion"].strip(),
            "loras": ",".join(CHARS[c]["lora"] for c in s["chars"]),
        })
        t += s["dur"]
    (d / "subs.srt").write_text("\n".join(srt), encoding="utf-8")
    music = ep.get("music")
    if music:
        (d / "lyrics.txt").write_text(loc(music["lyrics"], lang).strip() + "\n", encoding="utf-8")
    meta = {
        "title": loc(ep["title"], lang), "description": loc(ep["description"], lang)
        + "\n\n" + loc(DISCLOSURE, lang),
        "tags": ep["tags"].get(lang, ep["tags"].get("en", [])) if isinstance(ep["tags"], dict) else ep["tags"],
        "madeForKids": True, "alteredOrSynthetic": True,
        "thumbnail_prompt": f"{CFG['style'].strip()}, {ep.get('thumbnail', '')}",
    }
    (d / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "checklist.md").write_text(CHECKLIST.format(id=ep["id"], lang=lang), encoding="utf-8")
    p = {"id": ep["id"], "lang": lang, "format": ep["format"], "duration": t, "scenes": scenes,
         "music": music and {"style": music["style"], "duration": music.get("duration", math.ceil(t))},
         "compile": ep.get("compile")}
    (d / "plan.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    return d, p


DISCLOSURE = {
    "tr": "Bu video AI araçları yardımıyla üretilmiş; senaryo ve sözler ekibimizce yazılıp her kare denetlenmiştir.",
    "en": "Made with the help of AI tools; scripts and lyrics are written and every frame is reviewed by our team.",
    "es": "Hecho con ayuda de herramientas de IA; guiones y letras escritos y revisados por nuestro equipo.",
}

CHECKLIST = """# Yayın öncesi kontrol — {id} ({lang})
- [ ] Anatomi: fazla parmak / eriyen yüz / göz kayması yok
- [ ] Korkutucu ifade, tehlikeli davranış özendirmesi yok
- [ ] Karakterler bible ile tutarlı (renk, kıyafet)
- [ ] Sözler anadil konuşanı tarafından kontrol edildi
- [ ] Altyazı senkronu doğru
- [ ] Ses -14 LUFS civarı, ani gürültü yok
- [ ] Başka markaya benzeyen öğe yok (karakter, logo, thumbnail)
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
    if p["compile"]:
        return d, p
    r = Runner(d, dry)
    w, h = size(ep["format"])
    song = d / "song.wav"
    vocals = d / "stems/htdemucs/song/vocals.wav"
    if p["music"]:
        ok = r.tool("music", song, style=p["music"]["style"], lyrics_file=d / "lyrics.txt",
                    duration=p["music"]["duration"])
        if not ok and placeholder:
            ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", p["duration"], song)
        if song.exists():
            r.tool("stems", vocals, out_dir=d / "stems", song=song)
    for s in p["scenes"]:
        img = d / f"img/s{s['n']:02}.png"
        if not r.tool("image", img, prompt=s["image_prompt"].replace('"', "'"), negative=CFG["negative"],
                      loras=s["loras"], w=w, h=h) and placeholder:
            img.parent.mkdir(exist_ok=True)
            ff("-f", "lavfi", "-i", f"color=c={COLORS[s['n'] % len(COLORS)]}:s={w}x{h}",
               "-vf", f"drawtext=text='Sahne {s['n']}':fontsize={w//10}:x=(w-tw)/2:y=(h-th)/2",
               "-frames:v", 1, img)
        for c in range(s["clips"]):
            clip = d / f"clips/s{s['n']:02}_{c}.mp4"
            if s["sing"] and vocals.exists():
                seg = d / f"clips/s{s['n']:02}_{c}.wav"
                if not seg.exists():
                    seg.parent.mkdir(exist_ok=True)
                    ff("-ss", s["start"] + c * CFG["video"]["clip_seconds"], "-t",
                       CFG["video"]["clip_seconds"], "-i", vocals, seg)
                ok = r.tool("s2v", clip, image=img, audio=seg, prompt=s["motion"])
            else:
                ok = r.tool("i2v", clip, image=img, prompt=s["motion"].replace('"', "'"),
                            seconds=CFG["video"]["clip_seconds"])
            if not ok and placeholder and img.exists():
                clip.parent.mkdir(exist_ok=True)
                ff("-loop", 1, "-i", img, "-t", CFG["video"]["clip_seconds"], "-r", CFG["video"]["fps"],
                   "-vf", f"scale={w}:{h},zoompan=z='1+0.002*on':d=1:s={w}x{h}", "-pix_fmt", "yuv420p", clip)
    return d, p


# ---------- montaj ----------

def assemble(ep, lang, placeholder=False, burn_subs=True):
    d, p = produce(ep, lang, dry=True, placeholder=True) if placeholder else plan(ep, lang)
    w, h = size(ep["format"])
    fps = CFG["video"]["fps"]
    final = d / f"{ep['id']}_{lang}.mp4"
    parts = []
    if p["compile"]:
        for ref in p["compile"]:
            f = OUT / ref / lang / f"{ref}_{lang}.mp4"
            if not f.exists():
                sys.exit(f"derleme için önce {ref} birleştirilmeli: {f}")
            fit = d / f"fit_{ref}.mp4"
            # dikey Shorts'u bulanık arka planlı 16:9'a yerleştir
            ff("-i", f, "-filter_complex",
               f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20[bg];"
               f"[0:v]scale=-2:{h}[fg];[bg][fg]overlay=(W-w)/2:0,fps={fps},format=yuv420p[v]",
               "-map", "[v]", "-map", "0:a", "-c:a", "aac", "-ar", 44100, "-ac", 2, fit)
            parts.append(fit)
        concat(parts, final)
        print(f"✓ {final}")
        return final
    scene_files = []
    for s in p["scenes"]:
        clips = [d / f"clips/s{s['n']:02}_{c}.mp4" for c in range(s["clips"])]
        missing = [c for c in clips if not c.exists()]
        if missing:
            sys.exit(f"eksik klip: {missing[0]} (önce `run`, GPU yoksa --placeholder)")
        out = d / f"scene_{s['n']:02}.mp4"
        lst = d / f"scene_{s['n']:02}.txt"
        lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
        ff("-f", "concat", "-safe", 0, "-i", lst, "-t", s["dur"], "-an",
           "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},format=yuv420p",
           out)
        scene_files.append(out)
    lst = d / "scenes.txt"
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in scene_files))
    video = d / "video_only.mp4"
    ff("-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", video)
    song = d / "song.wav"
    audio = ["-i", song] if song.exists() else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    vf = []
    subs = d / "subs.srt"
    if burn_subs and subs.stat().st_size:
        vf = ["-vf", f"subtitles={subs}:force_style='Fontsize=18,Bold=1,Outline=2,MarginV=60'"]
    body = d / "body.mp4"
    ff("-i", video, *audio, *vf, "-map", "0:v", "-map", "1:a", "-t", p["duration"],
       "-af", "loudnorm=I=-14:TP=-1.5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-ar", 44100, "-ac", 2, body)
    jingle = ROOT / CFG["paths"]["jingle"]
    if jingle.exists():
        logo = d / "jingle.mp4"
        ff("-f", "lavfi", "-i", f"color=c=0xFFB3C7:s={w}x{h}:r={fps}", "-i", jingle, "-shortest",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", 44100, "-ac", 2, logo)
        concat([body, logo], final)
    else:
        shutil.copy(body, final)
    print(f"✓ {final}")
    return final


def concat(parts, final):
    lst = final.with_suffix(".txt")
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in parts))
    ff("-f", "concat", "-safe", 0, "-i", lst, "-c:v", "libx264", "-pix_fmt", "yuv420p",
       "-c:a", "aac", final)


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["validate", "plan", "run", "assemble"])
    ap.add_argument("target", help="bölüm .yaml dosyası veya klasörü")
    ap.add_argument("--lang", default="tr", choices=LANGS)
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
            print(("✗ " if errs else "✓ ") + f"{f.name}: {ep.get('format')} {total:.0f} sn, "
                  f"{len(ep.get('scenes', []))} sahne" + "".join(f"\n    {e}" for e in errs))
        sys.exit(1 if bad else 0)
    for f, ep in eps:
        if a.cmd == "plan":
            d, p = plan(ep, a.lang)
            print(f"✓ {ep['id']}: {p['duration']:.0f} sn, {sum(s['clips'] for s in p['scenes'])} klip → {d}")
        elif a.cmd == "run":
            produce(ep, a.lang, a.dry_run or a.placeholder, a.placeholder)
            if not a.dry_run:
                assemble(ep, a.lang, False, not a.no_subs)
        else:
            assemble(ep, a.lang, a.placeholder, not a.no_subs)


if __name__ == "__main__":
    main()
