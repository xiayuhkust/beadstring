# -*- coding: utf-8 -*-
"""串珠 PWA 图标：暗底 + 金线垂弧 + 双珠一结（4x 超采样抗锯齿）"""
from PIL import Image, ImageDraw

S = 2048  # 4x of 512
img = Image.new('RGB', (S, S), (28, 23, 34))
d = ImageDraw.Draw(img)

# 背景微渐变（上冷下暖）
for y in range(S):
    t = y / S
    r = int(28 + t * 62)
    g = int(23 + t * 38)
    b = int(34 + t * 18)
    d.line([(0, y), (S, y)], fill=(r, g, b))

# 金线：二次贝塞尔 (x0,y0)=(0.16,0.34) ctrl=(0.5,0.78) (x1,y1)=(0.84,0.34)
def bez(t, a, c, b):
    return (1-t)**2 * a + 2*(1-t)*t * c + t**2 * b
pts = []
for i in range(101):
    t = i / 100
    x = bez(t, 0.16, 0.50, 0.84) * S
    y = bez(t, 0.34, 0.80, 0.34) * S
    pts.append((x, y))
gold = (245, 205, 138)
for i in range(len(pts) - 1):
    d.line([pts[i], pts[i+1]], fill=gold, width=int(S * 0.012))

# 双珠
r1 = int(S * 0.085)
d.ellipse([int(0.16*S)-r1, int(0.34*S)-r1, int(0.16*S)+r1, int(0.34*S)+r1], fill=(245, 205, 138))
d.ellipse([int(0.84*S)-r1, int(0.34*S)-r1, int(0.84*S)+r1, int(0.34*S)+r1], fill=(232, 167, 92))
# 珠上高光
hl = int(S * 0.025)
d.ellipse([int(0.135*S)-hl, int(0.31*S)-hl, int(0.135*S)+hl, int(0.31*S)+hl], fill=(255, 240, 210))
d.ellipse([int(0.815*S)-hl, int(0.31*S)-hl, int(0.815*S)+hl, int(0.31*S)+hl], fill=(255, 228, 185))
# 中点结
r2 = int(S * 0.022)
mx, my = int(0.5*S), int(bez(0.5, 0.34, 0.80, 0.34) * S)
d.ellipse([mx-r2, my-r2, mx+r2, my+r2], fill=(253, 243, 227))

for size, name in [(512, 'icon-512.png'), (192, 'icon-192.png'), (180, 'icon-180.png')]:
    img.resize((size, size), Image.LANCZOS).save(f'../chuanzhu/{name}')
    print(name, 'ok')
