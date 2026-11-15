# Journal screens

init python:
    import store

    class JournalSetMode(Action):
        def __init__(self, mode):
            self.mode = mode

        def __call__(self):
            store.journal_draw.save_all()
            store.journal_mode = self.mode
            if self.mode == "draw":
                store.journal_draw.sync_brush(store.journal_draw_color, store.journal_draw_size)
                store.journal_draw.set_enabled(store.journal_active_side, True)
            else:
                store.journal_draw.set_enabled("left", False)
                store.journal_draw.set_enabled("right", False)
            renpy.restart_interaction()

    class JournalSetSide(Action):
        def __init__(self, side):
            self.side = side

        def __call__(self):
            store.journal_active_side = self.side
            if store.journal_mode == "draw":
                store.journal_draw.set_enabled(self.side, True)
            renpy.restart_interaction()

    class JournalCoverColor(Action):
        def __init__(self, color):
            self.color = color

        def __call__(self):
            store.journal.set_cover_color(self.color)
            renpy.restart_interaction()

    class JournalNav(Action):
        def __init__(self, delta):
            self.delta = delta

        def __call__(self):
            store.journal_draw.save_all()
            if store.journal.goto_spread(self.delta):
                store.journal_draw.get_canvases(force_reload=True)
                if store.journal_mode == "draw":
                    store.journal_draw.sync_brush(store.journal_draw_color, store.journal_draw_size)
                    store.journal_draw.set_enabled(store.journal_active_side, True)
                renpy.restart_interaction()

    class JournalAddPage(Action):
        def __call__(self):
            store.journal_draw.save_all()
            store.journal.add_spread()
            store.journal_draw.get_canvases(force_reload=True)
            if store.journal_mode == "draw":
                store.journal_draw.sync_brush(store.journal_draw_color, store.journal_draw_size)
                store.journal_draw.set_enabled(store.journal_active_side, True)
            renpy.restart_interaction()

    class JournalBrushColor(Action):
        def __init__(self, color):
            self.color = color

        def __call__(self):
            store.journal_draw_color = self.color
            store.journal_draw.sync_brush(self.color, store.journal_draw_size)
            renpy.restart_interaction()

    class JournalPickPhoto(Action):
        def __init__(self, filename):
            self.filename = filename

        def __call__(self):
            # Start placement on active side
            store.journal_placing = {
                "file": self.filename,
                "side": store.journal_active_side,
                "x": 0.12,
                "y": 0.12,
                "scale": 0.42,
                "crop": None,
            }
            renpy.hide_screen("journal_browse")
            renpy.show_screen("journal_place_photo")
            renpy.restart_interaction()

    class JournalConfirmPlace(Action):
        def __call__(self):
            p = store.journal_placing
            if not p:
                return
            store.journal.add_photo(
                p["file"],
                side=p.get("side", "left"),
                x=p.get("x", 0.12),
                y=p.get("y", 0.12),
                scale=p.get("scale", 0.42),
                crop=p.get("crop"),
            )
            store.journal_placing = None
            renpy.hide_screen("journal_place_photo")
            renpy.restart_interaction()

    class JournalCancelPlace(Action):
        def __call__(self):
            store.journal_placing = None
            renpy.hide_screen("journal_place_photo")
            renpy.restart_interaction()

    class JournalRemovePhoto(Action):
        def __init__(self, index):
            self.index = index

        def __call__(self):
            store.journal.remove_photo(self.index)
            renpy.restart_interaction()

    class JournalOpenCrop(Action):
        def __call__(self):
            p = store.journal_placing
            if not p:
                return
            store.journal_crop_file = p["file"]
            renpy.show_screen("journal_crop", filename=p["file"])

    class JournalApplyCrop(Action):
        def __init__(self, crop):
            self.crop = crop

        def __call__(self):
            if store.journal_placing is not None:
                store.journal_placing["crop"] = self.crop
            renpy.hide_screen("journal_crop")
            renpy.restart_interaction()

    class JournalSaveText(Action):
        def __init__(self, side, getter):
            self.side = side
            self.getter = getter

        def __call__(self):
            store.journal.set_text(self.side, self.getter())
            renpy.hide_screen("journal_write_editor")
            renpy.restart_interaction()


# ---------------------------------------------------------------------------
# Main journal window
# ---------------------------------------------------------------------------
screen journal_main():
    modal True
    zorder 50

    python:
        store.journal.ensure_folders()
        store.journal.ensure_spreads()
        j = store.journal
        cover = j.cover_color()
        sp = j.current_spread()
        page_label = "Spread {0} / {1}".format(
            store.persistent._journal_spread_index + 1,
            j.spread_count(),
        )
        left_text = sp.get("left_text", "") or ""
        right_text = sp.get("right_text", "") or ""
        left_text_show = j.escape_text(left_text)
        right_text_show = j.escape_text(right_text)
        mode = store.journal_mode
        active = store.journal_active_side
        PAGE_W = 300
        PAGE_H = 380
        # Booleans only in screen scope — Displayables in `if` crash Ren'Py 6 copy_on_change
        show_left_draw = (mode != "draw") and store.journal_draw.side_has_view("left")
        show_right_draw = (mode != "draw") and store.journal_draw.side_has_view("right")
        left_c, right_c = store.journal_draw.get_canvases()
        if mode == "draw":
            store.journal_draw.sync_brush(store.journal_draw_color, store.journal_draw_size)
            store.journal_draw.set_enabled(active, True)
        else:
            left_c.enabled = False
            right_c.enabled = False

    add Solid("#000000"):
        alpha 0.28

    # Floating journal — not fullscreen; Monika stays visible
    frame:
        xalign 0.62
        yalign 0.42
        background None
        padding (0, 0)

        vbox:
            spacing 8

            # Mode + cover color row
            hbox:
                spacing 8
                xalign 0.5

                textbutton _("Write"):
                    style "hkb_button"
                    selected (mode == "write")
                    action JournalSetMode("write")

                textbutton _("Draw"):
                    style "hkb_button"
                    selected (mode == "draw")
                    action JournalSetMode("draw")

                textbutton _("Photo"):
                    style "hkb_button"
                    selected (mode == "photo")
                    action JournalSetMode("photo")

                null width 12

                text _("Cover"):
                    style "mas_extra_menu_label_text"
                    size 14
                    yalign 0.5

                for col, _name in store.journal.COVER_COLORS:
                    button:
                        xsize 18
                        ysize 18
                        background Solid(col)
                        action JournalCoverColor(col)
                        selected (cover == col)

            # Book chrome
            fixed:
                xsize 680
                ysize 440

                # Outer cover / border
                frame:
                    background Solid(cover)
                    xfill True
                    yfill True
                    padding (14, 14)

                    # Inner pages area
                    frame:
                        background Solid("#c4b8a4")
                        xfill True
                        yfill True
                        padding (6, 6)

                        hbox:
                            spacing 8
                            xalign 0.5
                            yalign 0.5

                            # LEFT PAGE
                            fixed:
                                xsize PAGE_W
                                ysize PAGE_H

                                frame:
                                    background Solid(store.journal.PAGE_CREAM)
                                    xfill True
                                    yfill True
                                    padding (10, 10)

                                    # Lined paper (no screen `for` — avoids Ren'Py 6 SLCache crash)
                                    add store.journal.lined_paper(PAGE_W - 20, PAGE_H - 20)

                                # Saved drawing (pygame view — Ren'Py can't load fresh PNGs reliably)
                                if show_left_draw:
                                    fixed:
                                        xpos 0
                                        ypos 0
                                        xsize PAGE_W
                                        ysize PAGE_H
                                        add store.journal_draw.DrawingView("left")

                                # Photos on left
                                for idx, ph in store.journal.photos_on_side("left"):
                                    python:
                                        img, iw, ih = store.journal.photo_sized(
                                            ph["file"], ph.get("crop"), ph.get("scale", 0.4),
                                            PAGE_W - 20, PAGE_H - 20,
                                        )
                                        px = int(ph.get("x", 0.1) * (PAGE_W - 10))
                                        py = int(ph.get("y", 0.1) * (PAGE_H - 10))
                                    fixed:
                                        xpos px
                                        ypos py
                                        xsize max(iw, 40)
                                        ysize max(ih, 40)
                                        add img
                                        if mode == "photo":
                                            textbutton _("x"):
                                                style "hkb_button"
                                                xalign 1.0
                                                yalign 0.0
                                                action JournalRemovePhoto(idx)

                                # Text (escaped so [brackets] / {tags} in player writing don't crash Ren'Py)
                                if left_text and mode != "write":
                                    text left_text_show:
                                        style "journal_page_text"
                                        xpos 14
                                        ypos 14
                                        xmaximum PAGE_W - 28

                                if mode == "write" and left_text:
                                    text left_text_show:
                                        style "journal_page_text"
                                        xpos 14
                                        ypos 14
                                        xmaximum PAGE_W - 28

                                # Live canvases in draw mode (only active side accepts input)
                                if mode == "draw":
                                    fixed:
                                        xpos 0
                                        ypos 0
                                        xsize PAGE_W
                                        ysize PAGE_H
                                        add left_c

                                # Click targets / side select
                                if mode == "write":
                                    button:
                                        background Solid("#00000000")
                                        hover_background Solid("#4a90d220")
                                        xfill True
                                        yfill True
                                        action [
                                            Function(store.journal_ui.begin_edit, "left"),
                                            Show("journal_write_editor", side="left"),
                                        ]

                            # Spine gutter
                            add Solid("#8a7a68", xsize=6, ysize=PAGE_H)

                            # RIGHT PAGE
                            fixed:
                                xsize PAGE_W
                                ysize PAGE_H

                                frame:
                                    background Solid(store.journal.PAGE_CREAM)
                                    xfill True
                                    yfill True
                                    padding (10, 10)

                                    add store.journal.lined_paper(PAGE_W - 20, PAGE_H - 20)

                                if show_right_draw:
                                    fixed:
                                        xpos 0
                                        ypos 0
                                        xsize PAGE_W
                                        ysize PAGE_H
                                        add store.journal_draw.DrawingView("right")

                                for idx, ph in store.journal.photos_on_side("right"):
                                    python:
                                        img, iw, ih = store.journal.photo_sized(
                                            ph["file"], ph.get("crop"), ph.get("scale", 0.4),
                                            PAGE_W - 20, PAGE_H - 20,
                                        )
                                        px = int(ph.get("x", 0.1) * (PAGE_W - 10))
                                        py = int(ph.get("y", 0.1) * (PAGE_H - 10))
                                    fixed:
                                        xpos px
                                        ypos py
                                        xsize max(iw, 40)
                                        ysize max(ih, 40)
                                        add img
                                        if mode == "photo":
                                            textbutton _("x"):
                                                style "hkb_button"
                                                xalign 1.0
                                                yalign 0.0
                                                action JournalRemovePhoto(idx)

                                if right_text and mode != "write":
                                    text right_text_show:
                                        style "journal_page_text"
                                        xpos 14
                                        ypos 14
                                        xmaximum PAGE_W - 28

                                if mode == "write" and right_text:
                                    text right_text_show:
                                        style "journal_page_text"
                                        xpos 14
                                        ypos 14
                                        xmaximum PAGE_W - 28

                                if mode == "draw":
                                    fixed:
                                        xpos 0
                                        ypos 0
                                        xsize PAGE_W
                                        ysize PAGE_H
                                        add right_c

                                if mode == "write":
                                    button:
                                        background Solid("#00000000")
                                        hover_background Solid("#4a90d220")
                                        xfill True
                                        yfill True
                                        action [
                                            Function(store.journal_ui.begin_edit, "right"),
                                            Show("journal_write_editor", side="right"),
                                        ]
            # Tool row (mode-specific)
            if mode == "draw":
                hbox:
                    spacing 6
                    xalign 0.5

                    text _("Ink"):
                        style "mas_extra_menu_label_text"
                        size 14
                        yalign 0.5

                    # Current color preview
                    button:
                        xsize 22
                        ysize 22
                        background Solid(store.journal_draw_color)
                        action Function(store.journal_draw.open_color_picker)

                    textbutton _("Wheel"):
                        style "hkb_button"
                        action Function(store.journal_draw.open_color_picker)

                    textbutton _("Left"):
                        style "hkb_button"
                        selected (active == "left")
                        action JournalSetSide("left")

                    textbutton _("Right"):
                        style "hkb_button"
                        selected (active == "right")
                        action JournalSetSide("right")

                    textbutton _("Clear side"):
                        style "hkb_button"
                        action Function(store.journal_draw.wipe_side, active)

                    bar:
                        value FieldValue(store, "journal_draw_size", range=23, offset=1, style="slider")
                        xsize 100
                        yalign 0.5

                # Expanded palette row
                hbox:
                    spacing 4
                    xalign 0.5
                    for col in store.journal_draw.PALETTE:
                        button:
                            xsize 18
                            ysize 18
                            background Solid(col)
                            action JournalBrushColor(col)

                text _("Tap a swatch, or Wheel for any color. Drawing on [active] page."):
                    style "mas_extra_menu_label_text"
                    size 12
                    xalign 0.5

            if mode == "photo":
                hbox:
                    spacing 8
                    xalign 0.5

                    textbutton _("Browse"):
                        style "hkb_button"
                        action Show("journal_browse")

                    textbutton _("Left"):
                        style "hkb_button"
                        selected (active == "left")
                        action JournalSetSide("left")

                    textbutton _("Right"):
                        style "hkb_button"
                        selected (active == "right")
                        action JournalSetSide("right")

                    text _("Drop PNGs/JPGs in Photos folder"):
                        style "mas_extra_menu_label_text"
                        size 12
                        yalign 0.5

            if mode == "write":
                text _("Tap a page to write on it"):
                    style "mas_extra_menu_label_text"
                    size 14
                    xalign 0.5

            # Navigation + close/show
            hbox:
                spacing 14
                xalign 0.5

                textbutton _("< Prev"):
                    style "hkb_button"
                    sensitive (store.persistent._journal_spread_index > 0)
                    action JournalNav(-1)

                text "[page_label]":
                    style "mas_extra_menu_label_text"
                    size 16
                    yalign 0.5

                textbutton _("Next >"):
                    style "hkb_button"
                    sensitive (store.persistent._journal_spread_index < store.journal.spread_count() - 1)
                    action JournalNav(1)

                textbutton _("+ Page"):
                    style "hkb_button"
                    action JournalAddPage()

                null width 20

                textbutton _("Show"):
                    style "hkb_button"
                    action Return("show")

                textbutton _("Close"):
                    style "hkb_button"
                    action Return("close")

    key "K_ESCAPE" action Return("close")


# ---------------------------------------------------------------------------
# Write editor
# ---------------------------------------------------------------------------
screen journal_write_editor(side="left"):
    modal True
    zorder 70

    python:
        side_label = _("Left page") if side == "left" else _("Right page")

    add Solid("#000000"):
        alpha 0.45

    frame:
        style "mas_extra_menu_frame"
        xalign 0.5
        yalign 0.5
        xsize 560
        ysize 420
        padding (18, 16)

        vbox:
            spacing 10
            xfill True
            yfill True

            label side_label:
                text_style "mas_extra_menu_label_text"
                xalign 0.5

            text _("Tip: press Enter for a new line."):
                style "mas_extra_menu_label_text"
                size 13
                xalign 0.5

            frame:
                background Solid("#FFF8EE")
                xfill True
                ysize 280
                padding (10, 10)

                viewport:
                    mousewheel True
                    scrollbars "vertical"
                    input:
                        id "journal_input"
                        style "journal_input"
                        value FieldInputValue(store.journal_ui, "edit_text")
                        font store.journal.page_font
                        color "#2b2118"
                        size 18
                        outlines []
                        xfill True
                        length store.journal.MAX_TEXT

            hbox:
                xalign 0.5
                spacing 20

                textbutton _("Save"):
                    style "hkb_button"
                    action [
                        Function(store.journal_ui.save_edit, side),
                        Hide("journal_write_editor"),
                    ]

                textbutton _("Clear text"):
                    style "hkb_button"
                    action [
                        SetField(store.journal_ui, "edit_text", ""),
                        Function(store.journal.set_text, side, ""),
                        Hide("journal_write_editor"),
                    ]

                textbutton _("Cancel"):
                    style "hkb_button"
                    action Hide("journal_write_editor")

    key "K_RETURN" action Function(store.journal_ui.insert_newline, "journal_write_editor", "journal_input")
    key "K_KP_ENTER" action Function(store.journal_ui.insert_newline, "journal_write_editor", "journal_input")
    key "K_ESCAPE" action Hide("journal_write_editor")


init python in journal_ui:
    import store

    edit_text = u""
    crop_l = 0.0
    crop_t = 0.0
    crop_r = 0.0
    crop_b = 0.0

    def begin_edit(side):
        store.journal_ui.edit_text = store.journal.get_text(side)

    def save_edit(side):
        store.journal.set_text(side, store.journal_ui.edit_text)

    def reset_crop():
        store.journal_ui.crop_l = 0.0
        store.journal_ui.crop_t = 0.0
        store.journal_ui.crop_r = 0.0
        store.journal_ui.crop_b = 0.0

    def insert_newline(screen_name, widget_id, var_name=None):
        try:
            val = store.journal_ui.edit_text or ""
            if len(val) >= store.journal.MAX_TEXT:
                return
            try:
                widget = renpy.get_widget(screen_name, widget_id, "screens")
            except Exception:
                widget = None
            if widget is not None and hasattr(widget, "caret_pos"):
                pos = widget.caret_pos
                val = val[:pos] + "\n" + val[pos:]
                store.journal_ui.edit_text = val
                widget.content = val
                widget.caret_pos = pos + 1
                if hasattr(widget, "update_text"):
                    widget.update_text(widget.content, widget.editable)
            else:
                store.journal_ui.edit_text = val + "\n"
            renpy.restart_interaction()
        except Exception:
            pass

    def nudge_placing(dx, dy):
        p = store.journal_placing
        if not p:
            return
        p["x"] = max(0.0, min(0.85, float(p.get("x", 0.1)) + dx))
        p["y"] = max(0.0, min(0.85, float(p.get("y", 0.1)) + dy))
        renpy.restart_interaction()

    def scale_placing(delta):
        p = store.journal_placing
        if not p:
            return
        p["scale"] = max(0.15, min(0.95, float(p.get("scale", 0.4)) + delta))
        renpy.restart_interaction()

    def flip_placing_side():
        p = store.journal_placing
        if not p:
            return
        p["side"] = "right" if p.get("side") == "left" else "left"
        renpy.restart_interaction()


# ---------------------------------------------------------------------------
# Photo browse
# ---------------------------------------------------------------------------
screen journal_browse():
    modal True
    zorder 75

    python:
        photos = store.journal.list_photos()
        hint = store.journal.photos_folder_hint()

    add Solid("#000000"):
        alpha 0.5

    frame:
        style "mas_extra_menu_frame"
        xalign 0.5
        yalign 0.5
        xsize 700
        ysize 520
        padding (16, 14)

        vbox:
            spacing 10
            xfill True
            yfill True

            label _("Your Photos"):
                text_style "mas_extra_menu_label_text"
                xalign 0.5

            text _("Pick an image to place on the [journal_active_side] page."):
                style "mas_extra_menu_label_text"
                size 14
                xalign 0.5

            if not photos:
                text _("No images yet.\nDrop .png or .jpg files into:\n[hint]"):
                    style "mas_extra_menu_label_text"
                    size 15
                    xalign 0.5
                    text_align 0.5
            else:
                viewport:
                    mousewheel True
                    scrollbars "vertical"
                    ysize 380
                    xfill True

                    vpgrid:
                        cols 3
                        spacing 10
                        xalign 0.5

                        for name in photos:
                            $ thumb = store.journal.fitted(store.journal.photo_path(name), 180, 120)
                            button:
                                xsize 200
                                ysize 150
                                style "scrollable_menu_button"
                                action JournalPickPhoto(name)
                                vbox:
                                    spacing 4
                                    xalign 0.5
                                    frame:
                                        background Solid("#ffffff")
                                        xsize 186
                                        ysize 120
                                        add thumb:
                                            xalign 0.5
                                            yalign 0.5
                                    text name:
                                        size 12
                                        xalign 0.5

            textbutton _("Close"):
                style "hkb_button"
                xalign 0.5
                action Hide("journal_browse")

    key "K_ESCAPE" action Hide("journal_browse")


# ---------------------------------------------------------------------------
# Place / size photo on page
# ---------------------------------------------------------------------------
screen journal_place_photo():
    modal True
    zorder 80

    python:
        p = store.journal_placing
        if p is None:
            p = {"file": "", "side": "left", "x": 0.12, "y": 0.12, "scale": 0.42, "crop": None}
        preview, pw, ph = store.journal.photo_sized(
            p.get("file"), p.get("crop"), p.get("scale", 0.42), 280, 340
        )
        side_txt = _("Left") if p.get("side") == "left" else _("Right")

    add Solid("#000000"):
        alpha 0.4

    frame:
        style "mas_extra_menu_frame"
        xalign 0.5
        yalign 0.5
        xsize 520
        padding (16, 14)

        vbox:
            spacing 10
            xfill True

            label _("Place photo"):
                text_style "mas_extra_menu_label_text"
                xalign 0.5

            text _("Page: [side_txt]  ·  arrows move  ·  +/- size"):
                style "mas_extra_menu_label_text"
                size 13
                xalign 0.5

            frame:
                background Solid("#FFF8EE")
                xalign 0.5
                xsize 300
                ysize 360
                padding (8, 8)

                fixed:
                    xfill True
                    yfill True
                    python:
                        px = int(float(p.get("x", 0.12)) * 270)
                        py = int(float(p.get("y", 0.12)) * 330)
                    fixed:
                        xpos px
                        ypos py
                        add preview

            hbox:
                xalign 0.5
                spacing 8

                textbutton _("Move L"):
                    style "hkb_button"
                    action Function(store.journal_ui.nudge_placing, -0.04, 0)
                textbutton _("Move R"):
                    style "hkb_button"
                    action Function(store.journal_ui.nudge_placing, 0.04, 0)
                textbutton _("Move U"):
                    style "hkb_button"
                    action Function(store.journal_ui.nudge_placing, 0, -0.04)
                textbutton _("Move D"):
                    style "hkb_button"
                    action Function(store.journal_ui.nudge_placing, 0, 0.04)

            hbox:
                xalign 0.5
                spacing 8

                textbutton _("Smaller"):
                    style "hkb_button"
                    action Function(store.journal_ui.scale_placing, -0.06)
                textbutton _("Bigger"):
                    style "hkb_button"
                    action Function(store.journal_ui.scale_placing, 0.06)
                textbutton _("Flip page"):
                    style "hkb_button"
                    action Function(store.journal_ui.flip_placing_side)
                textbutton _("Crop"):
                    style "hkb_button"
                    action JournalOpenCrop()

            hbox:
                xalign 0.5
                spacing 20

                textbutton _("Place"):
                    style "hkb_button"
                    action JournalConfirmPlace()

                textbutton _("Cancel"):
                    style "hkb_button"
                    action JournalCancelPlace()

    key "K_LEFT" action Function(store.journal_ui.nudge_placing, -0.03, 0)
    key "K_RIGHT" action Function(store.journal_ui.nudge_placing, 0.03, 0)
    key "K_UP" action Function(store.journal_ui.nudge_placing, 0, -0.03)
    key "K_DOWN" action Function(store.journal_ui.nudge_placing, 0, 0.03)
    key "K_MINUS" action Function(store.journal_ui.scale_placing, -0.05)
    key "K_EQUALS" action Function(store.journal_ui.scale_placing, 0.05)
    key "K_ESCAPE" action JournalCancelPlace()


# ---------------------------------------------------------------------------
# Simple crop (center crop presets + optional custom margins)
# ---------------------------------------------------------------------------
screen journal_crop(filename):
    modal True
    zorder 90

    on "show" action Function(store.journal_ui.reset_crop)

    python:
        path = store.journal.photo_path(filename)
        try:
            iw, ih = renpy.image_size(path)
        except Exception:
            iw, ih = 400, 400
        cl = int(iw * store.journal_ui.crop_l)
        ct = int(ih * store.journal_ui.crop_t)
        cr = int(iw * store.journal_ui.crop_r)
        cb = int(ih * store.journal_ui.crop_b)
        cw = max(8, iw - cl - cr)
        ch = max(8, ih - ct - cb)
        crop_tuple = (cl, ct, cw, ch)
        preview = store.journal._scale_any(None, path, crop_tuple, 420, 280)

    add Solid("#000000"):
        alpha 0.55

    frame:
        style "mas_extra_menu_frame"
        xalign 0.5
        yalign 0.5
        xsize 560
        padding (16, 14)

        vbox:
            spacing 10
            xfill True

            label _("Crop"):
                text_style "mas_extra_menu_label_text"
                xalign 0.5

            frame:
                background Solid("#111111")
                xalign 0.5
                xsize 440
                ysize 300
                add preview:
                    xalign 0.5
                    yalign 0.5

            text _("Trim edges (sliders)"):
                style "mas_extra_menu_label_text"
                size 13
                xalign 0.5

            hbox:
                spacing 8
                xalign 0.5
                text _("L") size 12 yalign 0.5
                bar value FieldValue(store.journal_ui, "crop_l", range=0.45) xsize 90 style "slider"
                text _("R") size 12 yalign 0.5
                bar value FieldValue(store.journal_ui, "crop_r", range=0.45) xsize 90 style "slider"
                text _("T") size 12 yalign 0.5
                bar value FieldValue(store.journal_ui, "crop_t", range=0.45) xsize 90 style "slider"
                text _("B") size 12 yalign 0.5
                bar value FieldValue(store.journal_ui, "crop_b", range=0.45) xsize 90 style "slider"

            hbox:
                xalign 0.5
                spacing 16

                textbutton _("Apply crop"):
                    style "hkb_button"
                    action JournalApplyCrop(crop_tuple)

                textbutton _("No crop"):
                    style "hkb_button"
                    action JournalApplyCrop(None)

                textbutton _("Cancel"):
                    style "hkb_button"
                    action Hide("journal_crop")

    key "K_ESCAPE" action Hide("journal_crop")


# ---------------------------------------------------------------------------
# Color wheel / HSV picker
# ---------------------------------------------------------------------------
screen journal_color_picker():
    modal True
    zorder 95

    python:
        picker = store.journal_draw.get_color_picker()
        preview_hex = store.journal_draw.rgb_to_hex(picker.selected)

    add Solid("#000000"):
        alpha 0.45

    frame:
        style "mas_extra_menu_frame"
        xalign 0.5
        yalign 0.55
        xsize 320
        padding (16, 14)

        vbox:
            spacing 10
            xfill True

            label _("Color wheel"):
                text_style "mas_extra_menu_label_text"
                xalign 0.5

            text _("Drag on the field. Gray strip = shades."):
                style "mas_extra_menu_label_text"
                size 12
                xalign 0.5

            fixed:
                xalign 0.5
                xsize 260
                ysize 150
                add picker

            hbox:
                xalign 0.5
                spacing 10
                yalign 0.5

                text _("Brightness"):
                    style "mas_extra_menu_label_text"
                    size 13
                    yalign 0.5

                textbutton _("-"):
                    style "hkb_button"
                    action Function(store.journal_draw.nudge_brightness, -0.1)

                textbutton _("+"):
                    style "hkb_button"
                    action Function(store.journal_draw.nudge_brightness, 0.1)

                frame:
                    xsize 36
                    ysize 24
                    background Solid(preview_hex)

            hbox:
                xalign 0.5
                spacing 20

                textbutton _("Use color"):
                    style "hkb_button"
                    action Function(store.journal_draw.confirm_color_picker)

                textbutton _("Cancel"):
                    style "hkb_button"
                    action Hide("journal_color_picker")

    key "K_ESCAPE" action Hide("journal_color_picker")
