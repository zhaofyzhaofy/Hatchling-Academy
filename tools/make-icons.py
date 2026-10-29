#!/usr/bin/env python3
"""生成「小蛋壳学堂」的应用图标（180 / 192 / 512）。

用法：python3 tools/make-icons.py
输出到仓库根目录：icon-180.png、icon-192.png、icon-512.png
设计：天空渐变底 + 暖色光晕 + 白色蛋壳笑脸，主体控制在中心 80% 内，
      这样既能当普通图标，也能当 maskable 图标用。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = (180, 192, 512)
SS = 4  # 超采样倍数，缩小时自然获得抗锯齿

SKY_TOP = (191, 227, 255)      # #bfe3ff
SKY_MID = (230, 246, 255)      # #e6f6ff
SKY_BOT = (255, 246, 232)      # #fff6e8
HILL = (182, 236, 176)         # #b6ecb0
SHELL = (255, 253, 247)
SHELL_EDGE = (233, 227, 214)
INK = (59, 59, 82)             # #3b3b52
BEAK = (255, 176, 58)          # #ffb03a
CHEEK = (255, 143, 171)        # #ff8fab


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(size):
    """竖直三段渐变，和网页 body 的背景一致。"""
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        if t < 0.45:
            c = lerp(SKY_TOP, SKY_MID, t / 0.45)
        else:
            c = lerp(SKY_MID, SKY_BOT, (t - 0.45) / 0.55)
        d.line([(0, y), (size, y)], fill=c)
    return img


def sun(img, size):
    """右上角柔和光晕。"""
    glow = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(glow)
    cx, cy, r = size * 0.80, size * 0.16, size * 0.30
    steps = 26
    for i in range(steps, 0, -1):
        rr = r * i / steps
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                  fill=round(90 * (1 - i / steps) ** 1.6))
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.02))
    warm = Image.new("RGB", (size, size), (255, 214, 92))
    img.paste(warm, (0, 0), glow)


def hill(img, size):
    """底部一圈淡绿草地，呼应网页里的 .hill。"""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([-size * 0.35, size * 0.80, size * 1.35, size * 1.60],
              fill=HILL + (150,))
    img.paste(layer, (0, 0), layer)


def egg_mask(size, cx, cy, a, b):
    """蛋形：底部饱满、顶部略收，比纯椭圆更像蛋壳。"""
    layer = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(layer)
    pts = []
    steps = 720
    for i in range(steps):
        t = 2 * math.pi * i / steps
        taper = 1 - 0.20 * (0.5 + 0.5 * math.cos(t))   # t=0 在顶部，收窄 20%
        pts.append((cx + a * math.sin(t) * taper, cy - b * math.cos(t)))
    d.polygon(pts, fill=255)
    return layer


def egg(img, size):
    cx, cy = size * 0.50, size * 0.545
    a, b = size * 0.215, size * 0.265        # 主体宽度 ≈ 43%，留足安全区

    # 落地阴影
    shadow = Image.new("L", (size, size), 0)
    ImageDraw.Draw(shadow).ellipse(
        [cx - a * 0.95, cy + b * 0.88, cx + a * 0.95, cy + b * 1.06], fill=70)
    shadow = shadow.filter(ImageFilter.GaussianBlur(size * 0.016))
    img.paste(Image.new("RGB", (size, size), (120, 140, 170)), (0, 0), shadow)

    mask = egg_mask(size, cx, cy, a, b)

    # 蛋壳本体：上浅下略暖，做出一点体积感
    body = Image.new("RGB", (size, size), SHELL)
    d = ImageDraw.Draw(body)
    for y in range(size):
        t = max(0.0, min(1.0, (y - (cy - b)) / (2 * b)))
        d.line([(0, y), (size, y)], fill=lerp((255, 255, 252), SHELL_EDGE, t * 0.55))
    img.paste(body, (0, 0), mask)

    # 描边
    edge = mask.filter(ImageFilter.FIND_EDGES).filter(
        ImageFilter.GaussianBlur(size * 0.002))
    img.paste(Image.new("RGB", (size, size), (226, 218, 203)), (0, 0), edge.point(lambda v: v * 2))

    d = ImageDraw.Draw(img)

    # 眼睛
    eye_r = size * 0.030
    for sx in (-1, 1):
        ex, ey = cx + sx * size * 0.078, cy - size * 0.030
        d.ellipse([ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r], fill=INK)
        g = eye_r * 0.34
        d.ellipse([ex - g * 0.8 + eye_r * 0.30, ey - eye_r * 0.55,
                   ex + g * 0.8 + eye_r * 0.30, ey - eye_r * 0.55 + g * 1.6],
                  fill=(255, 255, 255))

    # 腮红
    cheek = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(cheek)
    cr = size * 0.042
    for sx in (-1, 1):
        ccx, ccy = cx + sx * size * 0.135, cy + size * 0.030
        cd.ellipse([ccx - cr, ccy - cr * 0.75, ccx + cr, ccy + cr * 0.75],
                   fill=CHEEK + (110,))
    cheek = cheek.filter(ImageFilter.GaussianBlur(size * 0.006))
    img.paste(cheek, (0, 0), cheek)

    # 小尖嘴
    bw, bh = size * 0.036, size * 0.030
    by = cy + size * 0.038
    d.polygon([(cx - bw, by), (cx + bw, by), (cx, by + bh)], fill=BEAK)

    # 头顶两笔裂纹，暗示「小蛋壳」
    d.line([(cx - size * 0.055, cy - b * 0.90), (cx - size * 0.018, cy - b * 0.80),
            (cx + size * 0.012, cy - b * 0.90), (cx + size * 0.048, cy - b * 0.79)],
           fill=SHELL_EDGE, width=max(2, round(size * 0.008)), joint="curve")


def build(target):
    size = target * SS
    img = sky(size)
    sun(img, size)
    hill(img, size)
    egg(img, size)
    return img.resize((target, target), Image.LANCZOS)


def main():
    for s in SIZES:
        out = os.path.join(ROOT, "icon-%d.png" % s)
        build(s).save(out, optimize=True)
        print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
