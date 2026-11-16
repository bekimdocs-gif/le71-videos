#!/usr/bin/env bash
# Installation de l'atelier LE 71 Flash News dans un environnement neuf.
# Usage : bash setup.sh   (depuis le dossier qui contient le71.py et d71.json)
set -e
KIT="$(cd "$(dirname "$0")" && pwd)"
pip install -q --break-system-packages pycairo piper-tts numpy >/dev/null 2>&1 || pip install -q pycairo piper-tts numpy
mkdir -p ~/.fonts "$KIT/voice"
for f in BlackItalic ExtraBoldItalic BoldItalic; do
  [ -f ~/.fonts/BarlowCondensed-$f.ttf ] || curl -sSfL -o ~/.fonts/BarlowCondensed-$f.ttf \
    https://raw.githubusercontent.com/google/fonts/main/ofl/barlowcondensed/BarlowCondensed-$f.ttf
done
if ! fc-list | grep -qi "Inter"; then
  for f in Inter-Bold Inter-Medium; do
    curl -sSfL -o ~/.fonts/$f.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf" && break
  done
fi
fc-cache -f >/dev/null
for e in onnx onnx.json; do
  [ -f "$KIT/voice/fr_FR-siwis-medium.$e" ] || curl -sSfL -o "$KIT/voice/fr_FR-siwis-medium.$e" \
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.$e"
done
which ffmpeg >/dev/null || (apt-get install -y -qq ffmpeg >/dev/null 2>&1 || true)
echo "Atelier LE 71 prêt."
