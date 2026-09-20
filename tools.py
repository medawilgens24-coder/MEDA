#!/usr/bin/env python3
"""Zouti pou bati APK MEDA a.
  python3 tools.py web      -> kreye www/index.html (index.html + pon Android)
  python3 tools.py android  -> mete MainActivity, ikòn ak splash nan android/
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BG = (0, 40, 150)

BRIDGE = r"""
<script>
/* --- Android bridge (enjekte pa build APK a) --- */
(function(){
  var origPrint = window.print ? window.print.bind(window) : null;
  window.print = function(){
    if (window.AndroidBridge && window.AndroidBridge.print) { window.AndroidBridge.print(); }
    else if (origPrint) { origPrint(); }
  };
  var origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function(){
    var a = this;
    if (window.AndroidBridge && window.AndroidBridge.saveFile && a.download && a.href && a.href.indexOf('blob:') === 0) {
      fetch(a.href).then(function(r){ return r.blob(); }).then(function(b){
        var fr = new FileReader();
        fr.onloadend = function(){
          var data = String(fr.result).split(',')[1] || '';
          window.AndroidBridge.saveFile(a.download, data, b.type || 'application/octet-stream');
        };
        fr.readAsDataURL(b);
      });
      return;
    }
    return origClick.apply(this, arguments);
  };
})();
</script>
"""


def web():
    with open(os.path.join(ROOT, 'index.html'), encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'<head[^>]*>', html, re.I)
    if not m:
        sys.exit('Pa jwenn <head> nan index.html')
    html = html[:m.end()] + BRIDGE + html[m.end():]
    www = os.path.join(ROOT, 'www')
    os.makedirs(www, exist_ok=True)
    with open(os.path.join(www, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('www/index.html kreye')


def android():
    from PIL import Image, ImageDraw, ImageFilter
    import shutil

    main = os.path.join(ROOT, 'android', 'app', 'src', 'main')
    res = os.path.join(main, 'res')

    # 1) MainActivity (enprime + telechajman fichye)
    jdir = os.path.join(main, 'java', 'com', 'imo', 'jesyonlekol')
    os.makedirs(jdir, exist_ok=True)
    shutil.copyfile(os.path.join(ROOT, 'MainActivity.java'), os.path.join(jdir, 'MainActivity.java'))
    print('MainActivity.java ranplase')

    # 2) Netwaye ansyen ikòn .webp ak ansyen splash yo
    for d, _, files in os.walk(res):
        for f in files:
            if re.match(r'ic_launcher.*\.webp$', f) or f == 'splash.png':
                os.remove(os.path.join(d, f))

    # 3) Logo -> kwen nwa yo vin transparan
    src = Image.open(os.path.join(ROOT, 'logo.png')).convert('RGB')
    w, h = src.size
    marker = src.copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(marker, seed, (255, 0, 255), thresh=40)
    mk = marker.load()
    alpha = Image.new('L', (w, h), 255)
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            if mk[x, y] == (255, 0, 255):
                ap[x, y] = 0
    alpha = alpha.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2))
    logo = src.convert('RGBA')
    logo.putalpha(alpha)

    def resized(im, size):
        return im.resize((size, size), Image.LANCZOS)

    def round_icon(size):
        canvas = Image.new('RGBA', (size, size), BG + (255,))
        inner = resized(logo, int(size * 0.88))
        off = (size - inner.width) // 2
        canvas.alpha_composite(inner, (off, off))
        mask = Image.new('L', (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
        canvas.putalpha(mask.resize((size, size), Image.LANCZOS))
        return canvas

    def foreground(size):  # 108dp ; logo = 70dp (zòn ki an sekirite)
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        inner = resized(logo, int(round(size * 70 / 108)))
        off = (size - inner.width) // 2
        canvas.alpha_composite(inner, (off, off))
        return canvas

    densities = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
    for name, d in densities.items():
        folder = os.path.join(res, 'mipmap-' + name)
        os.makedirs(folder, exist_ok=True)
        resized(logo, int(48 * d)).save(os.path.join(folder, 'ic_launcher.png'))
        round_icon(int(48 * d)).save(os.path.join(folder, 'ic_launcher_round.png'))
        foreground(int(108 * d)).save(os.path.join(folder, 'ic_launcher_fg.png'))

    any_dir = os.path.join(res, 'mipmap-anydpi-v26')
    os.makedirs(any_dir, exist_ok=True)
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
           '    <background android:drawable="@color/ic_launcher_bg_color"/>\n'
           '    <foreground android:drawable="@mipmap/ic_launcher_fg"/>\n'
           '</adaptive-icon>\n')
    for n in ('ic_launcher.xml', 'ic_launcher_round.xml'):
        with open(os.path.join(any_dir, n), 'w') as f:
            f.write(xml)

    val = os.path.join(res, 'values')
    os.makedirs(val, exist_ok=True)
    with open(os.path.join(val, 'ic_launcher_bg.xml'), 'w') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                '    <color name="ic_launcher_bg_color">#002896</color>\n</resources>\n')

    # 4) Splash screen (yon sèl fichye nan drawable/)
    splash = Image.new('RGBA', (1600, 1600), BG + (255,))
    splash.alpha_composite(resized(logo, 760), (420, 420))
    dr = os.path.join(res, 'drawable')
    os.makedirs(dr, exist_ok=True)
    splash.convert('RGB').save(os.path.join(dr, 'splash.png'), optimize=True)
    print('ikòn + splash kreye')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'web':
        web()
    elif cmd == 'android':
        android()
    else:
        sys.exit('Itilizasyon: python3 tools.py web|android')
