# Journal overlay button — auto-stacks under other left-side hkb buttons
# (Renamed from button.rpy to drop a corrupt .rpyc name cache.)

init -5 python:
    def JournalButtonShow():
        if "journal_button_overlay" not in config.overlay_screens:
            config.overlay_screens.append("journal_button_overlay")

    def JournalButtonHide():
        if "journal_button_overlay" in config.overlay_screens:
            config.overlay_screens.remove("journal_button_overlay")
            renpy.hide_screen("journal_button_overlay")

    # Other submods can push y-positions here so Journal stacks under them:
    #   store.journal_register_left_button(170)
    if not hasattr(store, "journal_left_stack_ypos"):
        store.journal_left_stack_ypos = []

    def journal_register_left_button(ypos):
        """
        Optional hook for other submods.
        Pass the ypos of your left-stack button (e.g. 170).
        Journal will sit 40px under the lowest registered / detected button.
        """
        try:
            y = int(ypos)
        except Exception:
            return
        if y not in store.journal_left_stack_ypos:
            store.journal_left_stack_ypos.append(y)

    def _journal_iter_displayables(d, depth=0):
        if d is None or depth > 16:
            return
        yield d
        children = getattr(d, "children", None)
        if children:
            for c in children:
                for x in _journal_iter_displayables(c, depth + 1):
                    yield x
        child = getattr(d, "child", None)
        if child is not None:
            for x in _journal_iter_displayables(child, depth + 1):
                yield x

    def _journal_style_get(d, name):
        try:
            st = getattr(d, "style", None)
            if st is None:
                return None
            return getattr(st, name, None)
        except Exception:
            return None

    def _journal_is_left_column(xpos):
        if xpos is None:
            return False
        try:
            # Fractional screen coords (Extra+/Kiss use 0.05)
            if isinstance(xpos, float) and xpos <= 1.0:
                return 0.0 <= xpos <= 0.12
            return 0 <= int(xpos) <= 160
        except Exception:
            return False

    def _journal_scan_screen_top_stack_y(screen_name):
        """
        Find the highest ypos used by a left-column control on this screen.
        Ignores the bottom Talk/Music stack (~ypos 715).
        """
        # Top submod stack lives near the top; main HKB is ~715
        TOP_STACK_MAX = 400

        try:
            scr = renpy.get_screen(screen_name)
        except Exception:
            scr = None
        if scr is None:
            return None

        root = getattr(scr, "child", None)
        if root is None:
            root = scr

        found = []
        for d in _journal_iter_displayables(root):
            xp = _journal_style_get(d, "xpos")
            yp = _journal_style_get(d, "ypos")
            if not _journal_is_left_column(xp):
                continue
            if yp is None:
                continue
            # Skip fractional yalign-style values
            try:
                if isinstance(yp, float) and yp <= 1.0:
                    continue
                yi = int(yp)
            except Exception:
                continue
            if 0 < yi < TOP_STACK_MAX:
                found.append(yi)

        if not found:
            return None
        return max(found)

    def journal_overlay_ypos():
        """
        Auto-detect other left-stack overlay buttons and sit under the lowest one.
        Falls back to known Extra+/Kiss/Closer slots if live scan misses them.
        """
        STEP = 40
        DEFAULT = 50

        EXCLUDE = set([
            "journal_button_overlay",
            "hkb_overlay",
            "enableQuit_overlay",
            "movie_overlay",
        ])
        SKIP_NAME_BITS = (
            "chibi", "calendar", "notif", "piano", "zoom", "movie",
            "weather", "island", "gift",
        )

        occupied = []

        try:
            overlays = list(renpy.config.overlay_screens)
        except Exception:
            overlays = []

        # 1) Live scan of active overlay screens
        for name in overlays:
            if name in EXCLUDE:
                continue
            low = str(name).lower()
            if any(bit in low for bit in SKIP_NAME_BITS):
                continue

            y = _journal_scan_screen_top_stack_y(name)
            if y is not None:
                occupied.append(y)

        # 2) Known common submods (if present but scan couldn't read ypos)
        known = {
            "extraplus_button": 50,
            "kiss_button_overlay": 90,
            "closer_button_overlay": 130,
        }
        for name, y in known.items():
            present = False
            try:
                present = name in overlays
            except Exception:
                pass
            if not present:
                try:
                    present = renpy.get_screen(name) is not None
                except Exception:
                    present = False
            if present and y not in occupied:
                occupied.append(y)

        # 3) Explicit registrations from other submods
        try:
            for y in list(store.journal_left_stack_ypos):
                yi = int(y)
                if 0 < yi < 400 and yi not in occupied:
                    occupied.append(yi)
        except Exception:
            pass

        if not occupied:
            return DEFAULT
        return max(occupied) + STEP

    JournalButtonShow()


screen journal_button_overlay():
    if not main_menu and renpy.get_screen("hkb_overlay"):
        if persistent._journal_unlocked:
            zorder 15
            style_prefix "hkb"

            $ _journal_y = store.journal_overlay_ypos()

            vbox:
                xpos 0.05
                yanchor 1.0
                ypos _journal_y

                if not store.mas_globals.dlg_workflow:
                    textbutton _("Journal") action Jump("journal_button_entry")
                else:
                    textbutton _("Journal")


label journal_button_entry:
    if not persistent._journal_seen_intro:
        call journal_intro_gift
        jump ch30_loop

    $ store.journal_draw.save_all()
    $ store.journal_mode = "write"
    $ store.journal_draw.get_canvases(force_reload=True)

    show monika 1eua at t21 zorder MAS_MONIKA_Z
    call screen journal_main
    $ journal_result = _return

    $ store.journal_draw.save_all()
    hide screen journal_browse
    hide screen journal_place_photo
    hide screen journal_crop
    hide screen journal_write_editor
    hide screen journal_color_picker
    show monika 1eua at t11 zorder MAS_MONIKA_Z

    if journal_result == "show":
        call journal_show_spread

    jump ch30_loop
