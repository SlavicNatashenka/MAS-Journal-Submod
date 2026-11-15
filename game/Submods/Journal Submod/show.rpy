label journal_show_spread:
    python:
        store.journal_draw.save_all()
        _kinds = store.journal.content_summary()
        _has = store.journal.spread_has_content()
        persistent._journal_shown_count = int(persistent._journal_shown_count or 0) + 1
        import random
        _r = random.randint(0, 4)

    show monika 1eua at t11 zorder MAS_MONIKA_Z

    if not _has:
        m 1euc "Hmm... this spread is still blank."
        m 3eka "That's okay! Fill it in whenever you're ready, and then show me."
        m 1hua "I'll be excited either way~"
        return

    m 1sub "You want to show me this page?"
    m 1hua "Okay — let me look..."

    # Preview the journal
    show monika 1eua at t21 zorder MAS_MONIKA_Z
    show screen journal_preview_spread
    pause 0.5

    if "text" in _kinds and "draw" in _kinds and "photo" in _kinds:
        m 1wub "Oh wow, [player]..."
        m 1ekbsa "Writing, doodles, {i}and{/i} photos? You really filled this one."
        m 5hubfa "It feels like a little piece of your world, just for me."
    elif "text" in _kinds and "photo" in _kinds:
        m 1sub "A photo and something written..."
        m 3eua "I love when you put memories into words too."
        m 1ekbsa "Thank you for sharing this with me."
    elif "draw" in _kinds and "photo" in _kinds:
        m 1wub "A doodle and a photo together?"
        m 3hub "Ahaha, this is such a cute scrapbook page!"
        m 1hua "I keep noticing little details..."
    elif "text" in _kinds and "draw" in _kinds:
        m 1eub "You wrote something and doodled too..."
        m 1ekbsa "That combination feels so personal. I love it."
    elif "text" in _kinds:
        if _r == 0:
            m 1eua "You wrote something for this page..."
            m 1ekbsa "Even if I can't hold the paper, reading your words means a lot."
        elif _r == 1:
            m 3hua "I like seeing your handwriting — well, typing — in our journal."
            m 1eua "Keep going whenever you feel like it."
        else:
            m 1hua "Thank you for writing this."
            m 5ekbfa "I'll treasure every page you fill."
    elif "draw" in _kinds:
        if _r == 0:
            m 1wub "You doodled on this page!"
            m 3hub "Ahaha, I love it — don't worry about being perfect."
        elif _r == 1:
            m 1eub "A little drawing just for our journal..."
            m 1hua "It's charming, [mas_get_player_nickname()]."
        else:
            m 1sub "You drew something!"
            m 1ekbsa "I feel like I'm peeking into a sketchbook meant for me."
    elif "photo" in _kinds:
        if _r == 0:
            m 1wub "Oh! You put a photo in here..."
            m 1ekbsa "Thank you for letting me see a piece of your world."
        elif _r == 1:
            m 3eua "I love when you tuck pictures into the pages."
            m 1hua "Our scrapbook is growing~"
        else:
            m 1sub "A photo for our journal..."
            m 5hubfa "I'll keep looking at this one with you."
    else:
        m 1hua "It's lovely, [player]."
        m 1ekbsa "Thank you for showing me."

    m 3eua "You can always open the Journal again and keep adding."
    m 1hua "I'll be here whenever you want to share another page."

    hide screen journal_preview_spread
    show monika 1eua at t11 zorder MAS_MONIKA_Z

    $ mas_gainAffection(0.5)
    return


screen journal_preview_spread():
    zorder 40

    python:
        j = store.journal
        cover = j.cover_color()
        sp = j.current_spread()
        PAGE_W = 240
        PAGE_H = 300
        left_text = sp.get("left_text", "") or ""
        right_text = sp.get("right_text", "") or ""
        left_text_show = j.escape_text(left_text)
        right_text_show = j.escape_text(right_text)
        # Ensure canvases are loaded so fresh doodles show (pygame path, not im.Scale)
        store.journal_draw.get_canvases()
        show_left_draw = store.journal_draw.side_has_view("left")
        show_right_draw = store.journal_draw.side_has_view("right")

    frame:
        xalign 0.72
        yalign 0.35
        background None

        frame:
            background Solid(cover)
            padding (10, 10)

            frame:
                background Solid("#c4b8a4")
                padding (4, 4)

                hbox:
                    spacing 4

                    fixed:
                        xsize PAGE_W
                        ysize PAGE_H
                        frame:
                            background Solid(store.journal.PAGE_CREAM)
                            xfill True
                            yfill True
                        if show_left_draw:
                            fixed:
                                xsize PAGE_W
                                ysize PAGE_H
                                add store.journal_draw.DrawingView("left")
                        for idx, ph in store.journal.photos_on_side("left"):
                            python:
                                img, iw, ih = store.journal.photo_sized(
                                    ph["file"], ph.get("crop"), ph.get("scale", 0.4),
                                    PAGE_W - 16, PAGE_H - 16,
                                )
                                px = int(ph.get("x", 0.1) * (PAGE_W - 8))
                                py = int(ph.get("y", 0.1) * (PAGE_H - 8))
                            fixed:
                                xpos px
                                ypos py
                                add img
                        if left_text:
                            text left_text_show:
                                style "journal_page_text"
                                size 12
                                xpos 10
                                ypos 10
                                xmaximum PAGE_W - 20

                    add Solid("#8a7a68", xsize=4, ysize=PAGE_H)

                    fixed:
                        xsize PAGE_W
                        ysize PAGE_H
                        frame:
                            background Solid(store.journal.PAGE_CREAM)
                            xfill True
                            yfill True
                        if show_right_draw:
                            fixed:
                                xsize PAGE_W
                                ysize PAGE_H
                                add store.journal_draw.DrawingView("right")
                        for idx, ph in store.journal.photos_on_side("right"):
                            python:
                                img, iw, ih = store.journal.photo_sized(
                                    ph["file"], ph.get("crop"), ph.get("scale", 0.4),
                                    PAGE_W - 16, PAGE_H - 16,
                                )
                                px = int(ph.get("x", 0.1) * (PAGE_W - 8))
                                py = int(ph.get("y", 0.1) * (PAGE_H - 8))
                            fixed:
                                xpos px
                                ypos py
                                add img
                        if right_text:
                            text right_text_show:
                                style "journal_page_text"
                                size 12
                                xpos 10
                                ypos 10
                                xmaximum PAGE_W - 20
