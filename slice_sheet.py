#!/usr/bin/env python3
import pygame as pg, os, glob
pg.init()

SRC      = "sprites"          # folder with the big sprite sheets
DEST     = "sprite_frames"    # where single frames will go
FRAME_W  = 32                 # width of one frame (pixels)
FRAME_H  = 32                 # height of one frame (pixels)

os.makedirs(DEST, exist_ok=True)

for file in glob.glob(os.path.join(SRC, "*.png")):
    sheet = pg.image.load(file).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()
    cols = sheet_w // FRAME_W
    rows = sheet_h // FRAME_H
    base_name = os.path.basename(file).replace(".png", "")

    for r in range(rows):
        for c in range(cols):
            frame = sheet.subsurface((c * FRAME_W, r * FRAME_H, FRAME_W, FRAME_H))
            out_path = os.path.join(DEST, f"{base_name}_{r:02}_{c:02}.png")
            pg.image.save(frame, out_path)

print("Done – frames are in", DEST)
