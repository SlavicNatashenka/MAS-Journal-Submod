init -1 python in journal:
    import os
    import re
    import shutil
    import store

    try:
        basestring
    except NameError:
        basestring = str

    REL_ROOT = "Submods/Journal Submod"
    REL_IMAGES = REL_ROOT + "/Images"
    REL_PHOTOS = REL_ROOT + "/Photos"
    REL_PAGES = REL_ROOT + "/pages"

    PHOTO_EXTS = (".png", ".jpg", ".jpeg", ".webp")
    CLOSED_BOOK = REL_IMAGES + "/Closed-book.png"

    COVER_COLORS = [
        ("#1a2b45", "Navy"),
        ("#4a1c28", "Burgundy"),
        ("#2d4a3e", "Forest"),
        ("#1c1c1c", "Black"),
        ("#6b3a4a", "Rose"),
        ("#3d2b1f", "Brown"),
        ("#2a3a5c", "Indigo"),
        ("#5c4033", "Cognac"),
    ]

    PAGE_CREAM = "#FFF8EE"
    PAGE_LINE = "#E8DCC8"
    INK = "#2b2118"

    def _pick_page_font():
        # Nunito (Comfy UI) covers Latin + Ukrainian/Russian Cyrillic.
        # If Comfy UI is missing, keep the journal usable with engine/MAS fonts.
        candidates = (
            "comfy_ui/fonts/Nunito-SemiBold.ttf",
            "DejaVuSans.ttf",
            "gui/font/Aller_Rg.ttf",
        )
        for fn in candidates:
            try:
                if renpy.loadable(fn):
                    return fn
            except Exception:
                continue
        return "gui/font/Aller_Rg.ttf"

    page_font = _pick_page_font()

    MAX_TEXT = 1200
    MAX_PHOTOS_PER_SPREAD = 12

    class LinedPaper(renpy.Displayable):
        """
        Notebook lines without a screen-language `for` loop.
        Ren'Py 6.99 can crash (SLCache.values) when hiding screens that use for+vbox.
        """

        def __init__(self, width=280, height=360, line_color=(232, 220, 200), spacing=18, **kwargs):
            renpy.Displayable.__init__(self, **kwargs)
            self.width = int(width)
            self.height = int(height)
            self.line_color = line_color
            self.spacing = int(spacing)

        def render(self, width, height, st, at):
            import pygame
            w = self.width if width < 2 else int(width)
            h = self.height if height < 2 else int(height)
            r = renpy.Render(w, h)
            try:
                surf = r.canvas().get_surface()
                y = self.spacing
                while y < h:
                    pygame.draw.line(surf, self.line_color, (0, y), (w, y), 1)
                    y += self.spacing
            except Exception:
                pass
            return r

    def lined_paper(page_w=280, page_h=360):
        return LinedPaper(width=page_w, height=page_h)

    def _abs(rel_path):
        return os.path.normpath(
            os.path.join(renpy.config.gamedir, rel_path.replace("/", os.sep))
        )

    def ensure_folders():
        for rel in (REL_IMAGES, REL_PHOTOS, REL_PAGES):
            path = _abs(rel)
            if not os.path.isdir(path):
                try:
                    os.makedirs(path)
                except Exception:
                    pass

    def closed_book_path():
        p = CLOSED_BOOK
        if renpy.loadable(p) or os.path.isfile(_abs(p)):
            return p
        return None

    def photos_folder_hint():
        return _abs(REL_PHOTOS)

    def list_photos():
        """Return sorted photo filenames from the Photos inbox."""
        ensure_folders()
        folder = _abs(REL_PHOTOS)
        found = []
        if not os.path.isdir(folder):
            return found
        try:
            for name in os.listdir(folder):
                low = name.lower()
                if low.endswith(PHOTO_EXTS) and not name.startswith("."):
                    found.append(name)
        except Exception:
            return []
        found.sort(key=lambda n: n.lower())
        return found

    def photo_rel(filename):
        return REL_PHOTOS + "/" + filename

    def photo_path(filename):
        rel = photo_rel(filename)
        abs_path = _abs(rel)
        if renpy.loadable(rel):
            return rel
        if os.path.isfile(abs_path):
            return abs_path.replace("\\", "/")
        return None

    def fitted(path, max_w, max_h):
        if not path:
            return store.Null()
        try:
            w, h = renpy.image_size(path)
        except Exception:
            try:
                return store.im.Scale(path, max_w, max_h)
            except Exception:
                return store.Null()
        if w <= 0 or h <= 0:
            return store.Null()
        scale = min(float(max_w) / float(w), float(max_h) / float(h))
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))
        try:
            return store.im.Scale(path, nw, nh)
        except Exception:
            return store.Null()

    def _blank_spread(spread_id):
        return {
            "id": spread_id,
            "left_text": "",
            "right_text": "",
            "photos": [],
        }

    def _next_id(spreads):
        n = 1
        used = set()
        for s in spreads:
            used.add(s.get("id", ""))
        while True:
            cand = "spread_{0:04d}".format(n)
            if cand not in used:
                return cand
            n += 1

    def ensure_spreads():
        if store.persistent._journal_spreads is None or len(store.persistent._journal_spreads) == 0:
            store.persistent._journal_spreads = [_blank_spread("spread_0001")]
            store.persistent._journal_spread_index = 0
        if store.persistent._journal_spread_index is None:
            store.persistent._journal_spread_index = 0
        idx = store.persistent._journal_spread_index
        if idx < 0:
            idx = 0
        if idx >= len(store.persistent._journal_spreads):
            idx = len(store.persistent._journal_spreads) - 1
        store.persistent._journal_spread_index = idx
        return store.persistent._journal_spreads

    def current_spread():
        spreads = ensure_spreads()
        return spreads[store.persistent._journal_spread_index]

    def spread_count():
        return len(ensure_spreads())

    def add_spread():
        spreads = ensure_spreads()
        new_id = _next_id(spreads)
        spreads.append(_blank_spread(new_id))
        store.persistent._journal_spread_index = len(spreads) - 1
        return current_spread()

    def goto_spread(delta):
        spreads = ensure_spreads()
        idx = store.persistent._journal_spread_index + delta
        if idx < 0 or idx >= len(spreads):
            return False
        store.persistent._journal_spread_index = idx
        return True

    def _as_text(text):
        """Keep unicode so Ukrainian/Russian survive MAS's Python 2."""
        if text is None:
            return u""
        if isinstance(text, unicode):
            return text
        if isinstance(text, str):
            try:
                return text.decode("utf-8")
            except Exception:
                try:
                    return text.decode("cp1251")
                except Exception:
                    pass
        try:
            return unicode(text)
        except Exception:
            return u""

    def set_text(side, text):
        sp = current_spread()
        text = _as_text(text)
        if len(text) > MAX_TEXT:
            text = text[:MAX_TEXT]
        if side == "left":
            sp["left_text"] = text
        else:
            sp["right_text"] = text

    def get_text(side):
        sp = current_spread()
        if side == "left":
            return _as_text(sp.get("left_text", u""))
        return _as_text(sp.get("right_text", u""))

    def escape_text(text):
        """
        Escape Ren'Py interpolation / text tags in player-written journal text.
        '[' starts substitutions like [player]; '{' starts text tags.
        """
        s = _as_text(text)
        if not s:
            return u""
        return s.replace(u"{", u"{{").replace(u"[", u"[[")

    def draw_path(side):
        sp = current_spread()
        return REL_PAGES + "/" + sp["id"] + "_" + side + ".png"

    def draw_abs(side):
        return _abs(draw_path(side))

    def has_drawing(side):
        return drawing_has_ink(side)

    def clear_drawing(side):
        path = draw_abs(side)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def drawing_has_ink(side, sp=None):
        """True only if the saved doodle file exists and isn't a blank transparent PNG."""
        if sp is None:
            sp = current_spread()
        sid = sp.get("id", "")
        path = _abs(REL_PAGES + "/" + sid + "_" + side + ".png")
        if not os.path.isfile(path):
            return False
        try:
            import pygame
            img = pygame.image.load(path)
            if surface_is_blank(img):
                # Leftover empty PNG from an old clear — remove it
                try:
                    os.remove(path)
                except Exception:
                    pass
                return False
            return True
        except Exception:
            return False

    def surface_is_blank(surf):
        """True if every pixel is fully transparent (or surface missing)."""
        if surf is None:
            return True
        try:
            w, h = surf.get_size()
            # Full scan — pages are small (~300x380)
            for y in range(h):
                for x in range(w):
                    c = surf.get_at((x, y))
                    # SRCALPHA: index 3 is alpha
                    if len(c) >= 4:
                        if c[3] > 0:
                            return False
                    else:
                        # Opaque RGB surface with any non-white? treat as ink
                        if c[0] < 250 or c[1] < 250 or c[2] < 250:
                            return False
            return True
        except Exception:
            return False

    def add_photo(filename, side="left", x=0.15, y=0.15, scale=0.45, crop=None):
        sp = current_spread()
        photos = sp.setdefault("photos", [])
        if len(photos) >= MAX_PHOTOS_PER_SPREAD:
            return False
        photos.append({
            "file": filename,
            "side": side,
            "x": float(x),
            "y": float(y),
            "scale": float(scale),
            "crop": crop,
        })
        return True

    def update_photo(index, **kwargs):
        sp = current_spread()
        photos = sp.get("photos", [])
        if index < 0 or index >= len(photos):
            return False
        photos[index].update(kwargs)
        return True

    def remove_photo(index):
        sp = current_spread()
        photos = sp.get("photos", [])
        if index < 0 or index >= len(photos):
            return False
        photos.pop(index)
        return True

    def photos_on_side(side):
        sp = current_spread()
        out = []
        for i, p in enumerate(sp.get("photos", [])):
            if p.get("side") == side:
                out.append((i, p))
        return out

    def _scale_any(img_or_path, path, crop, max_w, max_h):
        try:
            if crop:
                src = store.im.Crop(path, tuple(crop))
                cw, ch = int(crop[2]), int(crop[3])
                if cw <= 0 or ch <= 0:
                    return store.Null()
                scale = min(float(max_w) / float(cw), float(max_h) / float(ch))
                nw = max(1, int(cw * scale))
                nh = max(1, int(ch * scale))
                return store.im.Scale(src, nw, nh)
            return fitted(path, max_w, max_h)
        except Exception:
            return store.Null()

    def drawing_image(side):
        """Path Ren'Py can show for a saved page doodle (fresh files included)."""
        rel = draw_path(side)
        abs_path = draw_abs(side)
        if not os.path.isfile(abs_path):
            return None
        if renpy.loadable(rel):
            return rel
        return abs_path.replace("\\", "/")

    def photo_sized(filename, crop, scale, page_w, page_h):
        """Scale photo relative to page size (scale 0-1 of page width)."""
        path = photo_path(filename)
        if not path:
            return store.Null(), 0, 0
        try:
            if crop:
                ow, oh = int(crop[2]), int(crop[3])
                src = store.im.Crop(path, tuple(crop))
            else:
                ow, oh = renpy.image_size(path)
                src = path
            if ow <= 0 or oh <= 0:
                return store.Null(), 0, 0
            target_w = max(20, int(page_w * float(scale)))
            ratio = float(oh) / float(ow)
            target_h = max(20, int(target_w * ratio))
            # Clamp to page
            if target_h > page_h * 0.95:
                target_h = int(page_h * 0.95)
                target_w = max(20, int(target_h / ratio))
            return store.im.Scale(src, target_w, target_h), target_w, target_h
        except Exception:
            return store.Null(), 0, 0

    def cover_color():
        c = store.persistent._journal_cover_color
        if not c:
            c = "#1a2b45"
            store.persistent._journal_cover_color = c
        return c

    def set_cover_color(hex_color):
        store.persistent._journal_cover_color = hex_color

    def spread_has_content(sp=None):
        if sp is None:
            sp = current_spread()
        if (sp.get("left_text") or "").strip():
            return True
        if (sp.get("right_text") or "").strip():
            return True
        photos = sp.get("photos") or []
        if len(photos) > 0:
            return True
        for side in ("left", "right"):
            if drawing_has_ink(side, sp):
                return True
        return False

    def content_summary(sp=None):
        """Rough summary for Monika's Show reactions."""
        if sp is None:
            sp = current_spread()
        has_text = bool((sp.get("left_text") or "").strip() or (sp.get("right_text") or "").strip())
        has_photos = bool(sp.get("photos"))
        has_draw = drawing_has_ink("left", sp) or drawing_has_ink("right", sp)
        kinds = []
        if has_text:
            kinds.append("text")
        if has_draw:
            kinds.append("draw")
        if has_photos:
            kinds.append("photo")
        return kinds


# Folders / blank spreads — unique init body so Ren'Py 6.99 IDs stay distinct
init 6 python:
    # journal_core_ensure
    store.journal.ensure_folders()
    store.journal.ensure_spreads()
