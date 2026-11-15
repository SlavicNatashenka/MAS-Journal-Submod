init python in journal_draw:
    import os
    import math
    import pygame
    import store

    PAGE_W = 300
    PAGE_H = 380

    class PageCanvas(renpy.Displayable):
        """
        Drawable surface for one journal page side.

        Brush work is applied in render() from stored mouse points (like the
        Whiteboard submod) so strokes stay smooth even when motion events are sparse.
        """

        def __init__(self, side, brush_color=(43, 33, 24, 255), brush_size=4, **kwargs):
            renpy.Displayable.__init__(self, **kwargs)
            self.side = side
            self.brush_color = brush_color
            self.brush_size = max(1, min(24, int(brush_size)))
            self.enabled = True

            self._canvas = None
            self._dim = (PAGE_W, PAGE_H)

            # Mouse state — applied during render, not directly in event()
            self._pressed = False
            self._last_xy = None
            self._this_xy = None
            self._dirty = False
            self._needs_save = False

            self._load_from_disk()

        def _ensure_canvas(self):
            if self._canvas is None or self._canvas.get_size() != self._dim:
                old = self._canvas
                # Opaque-friendly alpha surface; brush stamps use full alpha
                self._canvas = pygame.Surface(self._dim, pygame.SRCALPHA, 32)
                self._canvas.fill((0, 0, 0, 0))
                if old is not None:
                    try:
                        self._canvas.blit(old, (0, 0))
                    except Exception:
                        pass

        def _load_from_disk(self):
            self._ensure_canvas()
            path = store.journal.draw_abs(self.side)
            if not os.path.isfile(path):
                return
            try:
                img = pygame.image.load(path)
                if hasattr(img, "convert_alpha"):
                    img = img.convert_alpha()
                self._canvas.fill((0, 0, 0, 0))
                self._canvas.blit(img, (0, 0))
            except Exception:
                pass

        def set_brush(self, color_rgb, size):
            if len(color_rgb) == 3:
                self.brush_color = (int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2]), 255)
            else:
                self.brush_color = color_rgb
            self.brush_size = max(1, min(24, int(size)))

        def wipe(self):
            self._ensure_canvas()
            self._canvas.fill((0, 0, 0, 0))
            # Don't re-save a blank PNG — delete the file so Show sees no drawing
            self._dirty = False
            self._needs_save = False
            store.journal.clear_drawing(self.side)
            renpy.redraw(self, 0)

        def save(self):
            if self._canvas is None:
                return
            if not self._dirty and not self._needs_save:
                return
            store.journal.ensure_folders()
            path = store.journal.draw_abs(self.side)
            # Cleared / empty canvas → remove file instead of keeping a blank PNG
            if store.journal.surface_is_blank(self._canvas):
                store.journal.clear_drawing(self.side)
                self._dirty = False
                self._needs_save = False
                return
            try:
                pygame.image.save(self._canvas, path)
                self._dirty = False
                self._needs_save = False
            except Exception:
                pass

        def reload(self):
            self.save()
            self._load_from_disk()
            self._dirty = False
            self._needs_save = False

        def _refresh_brush_from_store(self):
            try:
                rgb = hex_to_rgb(store.journal_draw_color)
                self.brush_color = (rgb[0], rgb[1], rgb[2], 255)
                self.brush_size = max(1, min(24, int(store.journal_draw_size)))
            except Exception:
                pass

        def _clamp(self, pos):
            x, y = pos
            w, h = self._dim
            return (max(0, min(w - 1, int(x))), max(0, min(h - 1, int(y))))

        def _stamp_circle(self, pos):
            """Stamp a filled circle. More reliable on SRCALPHA than draw.line width."""
            rad = max(1, self.brush_size // 2)
            pygame.draw.circle(self._canvas, self.brush_color, pos, rad)

        def _stroke(self, a, b):
            """Interpolate stamps between two points so fast drags don't gap."""
            a = self._clamp(a)
            b = self._clamp(b)
            x0, y0 = a
            x1, y1 = b
            dist = math.hypot(x1 - x0, y1 - y0)
            step = max(1.0, self.brush_size * 0.35)
            if dist < 0.5:
                self._stamp_circle(a)
                return
            n = int(dist / step) + 1
            for i in range(n + 1):
                t = float(i) / float(n)
                x = int(x0 + (x1 - x0) * t)
                y = int(y0 + (y1 - y0) * t)
                self._stamp_circle((x, y))

        def render(self, width, height, st, at):
            # Keep a stable size — don't thrash the surface on tiny layout wiggles
            w = PAGE_W if width < 2 else int(width)
            h = PAGE_H if height < 2 else int(height)
            if abs(w - PAGE_W) <= 2:
                w = PAGE_W
            if abs(h - PAGE_H) <= 2:
                h = PAGE_H
            self._dim = (w, h)
            self._ensure_canvas()
            self._refresh_brush_from_store()

            # Apply pending stroke segment (Whiteboard-style)
            if self._pressed and self._last_xy is not None and self._this_xy is not None:
                self._stroke(self._last_xy, self._this_xy)
                self._last_xy = self._this_xy
                self._dirty = True
            elif self._pressed and self._this_xy is not None and self._last_xy is None:
                self._stamp_circle(self._clamp(self._this_xy))
                self._last_xy = self._this_xy
                self._dirty = True

            r = renpy.Render(w, h)
            try:
                surf = r.canvas().get_surface()
                surf.fill((0, 0, 0, 0))
                surf.blit(self._canvas, (0, 0))
            except Exception:
                pass

            # Only keep redrawing WHILE drawing.
            # Continuous redraw(0) while idle breaks screen buttons (click never completes).
            if self._pressed:
                renpy.redraw(self, 0)
            return r

        def event(self, ev, x, y, st):
            if not self.enabled:
                # Still allow ending a stroke if we somehow kept pressed while disabled
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self._pressed:
                    self._pressed = False
                    self._last_xy = None
                    self._this_xy = None
                    self._needs_save = True
                    self.save()
                return

            inside = (0 <= x < self._dim[0]) and (0 <= y < self._dim[1])

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if not inside:
                    return
                self._pressed = True
                self._this_xy = (x, y)
                self._last_xy = (x, y)
                self._ensure_canvas()
                self._refresh_brush_from_store()
                self._stamp_circle(self._clamp(self._this_xy))
                self._dirty = True
                renpy.redraw(self, 0)
                raise renpy.IgnoreEvent

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self._pressed:
                    self._pressed = False
                    self._last_xy = None
                    self._this_xy = None
                    self._needs_save = True
                    self.save()
                    renpy.redraw(self, 0)
                    raise renpy.IgnoreEvent
                return

            elif ev.type == pygame.MOUSEMOTION:
                if not self._pressed:
                    return
                self._this_xy = (x, y)
                renpy.redraw(self, 0)
                raise renpy.IgnoreEvent

    left_canvas = None
    right_canvas = None
    color_picker = None

    # Expanded quick palette (hex)
    PALETTE = [
        "#2b2118", "#000000", "#4a4a4a", "#9a9a9a", "#ffffff",
        "#8B0000", "#e74c3c", "#ff7f50", "#f1c40f", "#f39c12",
        "#27ae60", "#2d5a3e", "#1abc9c", "#1a3a6b", "#3498db",
        "#9b59b6", "#6b3a4a", "#e91e63", "#fd79a8", "#a0522d",
    ]

    def hex_to_rgb(hex_color):
        h = str(hex_color).lstrip("#")
        if len(h) != 6:
            return (43, 33, 24)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            return (43, 33, 24)

    def rgb_to_hex(rgb):
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        return "#{0:02x}{1:02x}{2:02x}".format(
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        )

    def apply_rgb(rgb):
        store.journal_draw_color = rgb_to_hex(rgb)
        sync_brush(store.journal_draw_color, store.journal_draw_size)

    class ColorPicker(renpy.Displayable):
        """HSV color field + grayscale strip (Whiteboard-style)."""

        def __init__(self, **kwargs):
            renpy.Displayable.__init__(self, **kwargs)
            self.selected = (43, 33, 24)
            self._size = (220, 140)
            self._hue = 0.0
            self._sat = 1.0
            self._val = 1.0
            self._last_mx = None
            self._last_my = None
            self._surf = None
            self._dragging = False

        def set_from_hex(self, hex_color):
            r, g, b = hex_to_rgb(hex_color)
            self.selected = (r, g, b)
            try:
                import colorsys
                h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                self._hue = h * 360.0
                self._sat = s
                self._val = v
            except Exception:
                pass
            self._surf = None
            self._last_mx = None
            self._last_my = None

        def render(self, width, height, st, at):
            w = int(width) if width > 1 else self._size[0]
            h = int(height) if height > 1 else self._size[1]
            self._size = (w, h)
            if self._surf is None or self._surf.get_size() != self._size:
                self._make_gradient()

            r = renpy.Render(w, h)
            try:
                surf = r.canvas().get_surface()
                surf.blit(self._surf, (0, 0))
                if self._last_mx is not None and self._last_my is not None:
                    pygame.draw.line(
                        surf, (0, 0, 0),
                        (self._last_mx - 5, self._last_my),
                        (self._last_mx + 5, self._last_my), 1
                    )
                    pygame.draw.line(
                        surf, (255, 255, 255),
                        (self._last_mx, self._last_my - 5),
                        (self._last_mx, self._last_my + 5), 1
                    )
            except Exception:
                pass

            if self._dragging:
                renpy.redraw(self, 0)
            return r

        def event(self, ev, x, y, st):
            w, h = self._size
            inside = (0 <= x < w) and (0 <= y < h)

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and inside:
                self._dragging = True
                self._pick(x, y, w, h)
                renpy.redraw(self, 0)
                raise renpy.IgnoreEvent

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self._dragging:
                    self._dragging = False
                    renpy.restart_interaction()
                    raise renpy.IgnoreEvent

            elif ev.type == pygame.MOUSEMOTION and self._dragging:
                self._pick(x, y, w, h)
                renpy.redraw(self, 0)
                raise renpy.IgnoreEvent

        def _pick(self, x, y, w, h):
            import colorsys
            x = max(0, min(w - 1, int(x)))
            y = max(0, min(h - 1, int(y)))
            gradient_width = max(1, w - 14)
            if x < gradient_width:
                self._hue = 360.0 * float(x) / float(gradient_width)
                self._sat = 1.0 - (float(y) / float(max(1, h - 1)))
                self._sat = max(0.0, min(1.0, self._sat))
                rr, gg, bb = colorsys.hsv_to_rgb(self._hue / 360.0, self._sat, self._val)
                self.selected = (
                    int(min(max(rr * 255, 0), 255)),
                    int(min(max(gg * 255, 0), 255)),
                    int(min(max(bb * 255, 0), 255)),
                )
            else:
                gval = int(255 * (1.0 - float(y) / float(max(1, h - 1))))
                self.selected = (gval, gval, gval)
            self._last_mx = x
            self._last_my = y

        def _make_gradient(self):
            import colorsys
            w, h = self._size
            surf = pygame.Surface((w, h))
            gradient_width = max(1, w - 14)

            for x in range(gradient_width):
                for y in range(h):
                    hue = 360.0 * float(x) / float(gradient_width)
                    sat = 1.0 - (float(y) / float(max(1, h - 1)))
                    rr, gg, bb = colorsys.hsv_to_rgb(hue / 360.0, sat, self._val)
                    surf.set_at((x, y), (
                        int(min(max(rr * 255, 0), 255)),
                        int(min(max(gg * 255, 0), 255)),
                        int(min(max(bb * 255, 0), 255)),
                    ))

            for x in range(gradient_width, w):
                for y in range(h):
                    gval = int(255 * (1.0 - float(y) / float(max(1, h - 1))))
                    surf.set_at((x, y), (gval, gval, gval))

            self._surf = surf

        def set_value(self, val):
            """Brightness 0-1; rebuilds the hue field."""
            self._val = max(0.05, min(1.0, float(val)))
            self._surf = None
            import colorsys
            rr, gg, bb = colorsys.hsv_to_rgb(self._hue / 360.0, self._sat, self._val)
            self.selected = (
                int(min(max(rr * 255, 0), 255)),
                int(min(max(gg * 255, 0), 255)),
                int(min(max(bb * 255, 0), 255)),
            )
            renpy.redraw(self, 0)
            renpy.restart_interaction()

    def get_color_picker():
        global color_picker
        if color_picker is None:
            color_picker = ColorPicker()
        return color_picker

    def open_color_picker():
        picker = get_color_picker()
        picker.set_from_hex(store.journal_draw_color)
        renpy.show_screen("journal_color_picker")

    def confirm_color_picker():
        picker = get_color_picker()
        apply_rgb(picker.selected)
        renpy.hide_screen("journal_color_picker")
        renpy.restart_interaction()

    def nudge_brightness(delta):
        picker = get_color_picker()
        picker.set_value(picker._val + float(delta))

    def get_canvases(force_reload=False):
        global left_canvas, right_canvas
        if left_canvas is None or force_reload:
            if left_canvas is not None:
                left_canvas.save()
            if right_canvas is not None:
                right_canvas.save()
            left_canvas = PageCanvas("left")
            right_canvas = PageCanvas("right")
        return left_canvas, right_canvas

    def active_canvas():
        left, right = get_canvases()
        if store.journal_active_side == "right":
            return right
        return left

    def save_all():
        global left_canvas, right_canvas
        if left_canvas is not None:
            left_canvas.save()
        if right_canvas is not None:
            right_canvas.save()

    def sync_brush(color_hex, size):
        rgb = hex_to_rgb(color_hex)
        left, right = get_canvases()
        left.set_brush(rgb, size)
        right.set_brush(rgb, size)

    def set_enabled(side, enabled):
        left, right = get_canvases()
        # Only the active page accepts input
        left.enabled = bool(enabled) and (side == "left")
        right.enabled = bool(enabled) and (side == "right")
        # Cancel any half-finished stroke on the inactive side
        for c in (left, right):
            if not c.enabled and c._pressed:
                c._pressed = False
                c._last_xy = None
                c._this_xy = None
                c._needs_save = True
                c.save()

    def wipe_side(side):
        left, right = get_canvases()
        if side == "left":
            left.wipe()
        else:
            right.wipe()

    def end_all_strokes():
        """End any in-progress stroke (e.g. mouse released outside the page)."""
        global left_canvas, right_canvas
        for c in (left_canvas, right_canvas):
            if c is None:
                continue
            if c._pressed:
                c._pressed = False
                c._last_xy = None
                c._this_xy = None
                c._needs_save = True
                c.save()
                renpy.redraw(c, 0)

    class DrawingView(renpy.Displayable):
        """
        Show a page doodle via pygame (Ren'Py 6 can't im.Scale freshly written PNGs reliably).
        Prefers the live canvas surface when available.
        """

        def __init__(self, side, **kwargs):
            renpy.Displayable.__init__(self, **kwargs)
            self.side = side
            self._cached = None
            self._cache_path = None
            self._cache_mtime = None

        def _surface_from_live(self):
            global left_canvas, right_canvas
            c = left_canvas if self.side == "left" else right_canvas
            if c is not None and c._canvas is not None:
                if not store.journal.surface_is_blank(c._canvas):
                    return c._canvas
            return None

        def _surface_from_disk(self):
            path = store.journal.draw_abs(self.side)
            if not os.path.isfile(path):
                return None
            try:
                mtime = os.path.getmtime(path)
            except Exception:
                mtime = None
            if (
                self._cached is not None
                and self._cache_path == path
                and self._cache_mtime == mtime
            ):
                return self._cached
            try:
                img = pygame.image.load(path)
                if hasattr(img, "convert_alpha"):
                    img = img.convert_alpha()
                if store.journal.surface_is_blank(img):
                    self._cached = None
                    return None
                self._cached = img
                self._cache_path = path
                self._cache_mtime = mtime
                return img
            except Exception:
                return None

        def render(self, width, height, st, at):
            w = int(width) if width > 1 else PAGE_W
            h = int(height) if height > 1 else PAGE_H
            r = renpy.Render(w, h)

            src = self._surface_from_live()
            if src is None:
                src = self._surface_from_disk()
            if src is None:
                return r

            try:
                dest = r.canvas().get_surface()
                dest.fill((0, 0, 0, 0))
                sw, sh = src.get_size()
                if sw == w and sh == h:
                    dest.blit(src, (0, 0))
                else:
                    try:
                        scaled = pygame.transform.smoothscale(src, (w, h))
                    except Exception:
                        scaled = pygame.transform.scale(src, (w, h))
                    dest.blit(scaled, (0, 0))
            except Exception:
                pass
            return r

    def view_for_side(side):
        """Return a DrawingView if that side has ink, else None."""
        if side_has_view(side):
            return DrawingView(side)
        return None

    def side_has_view(side):
        """Bool only — safe for Ren'Py 6 screen `if` (Displayables break copy_on_change)."""
        global left_canvas, right_canvas
        c = left_canvas if side == "left" else right_canvas
        if c is not None and c._canvas is not None:
            if not store.journal.surface_is_blank(c._canvas):
                return True
        return store.journal.drawing_has_ink(side)
