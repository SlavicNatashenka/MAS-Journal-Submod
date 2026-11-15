init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="journal_intro_gift",
            random=True,
            aff_range=(mas_aff.NORMAL, None),
        )
    )

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="journal_open_topic",
            prompt="Can I look at our journal?",
            category=["misc"],
            pool=True,
            unlocked=False,
            rules={"no_unlock": None},
        )
    )


init 10 python:
    def _journal_queue_intro():
        """Queue the gift scene once so she notices soon after install."""
        if persistent._journal_seen_intro:
            return
        if getattr(store, "_journal_intro_queued", False):
            return
        store._journal_intro_queued = True
        try:
            store.pushEvent("journal_intro_gift")
        except Exception:
            pass

    store.mas_submod_utils.registerFunction("ch30_reset", _journal_queue_intro)


label journal_intro_gift:
    if persistent._journal_seen_intro:
        return "derandom"

    m 1euc "Hmm...{w=0.4} hold on a second, [player]."
    m 3eud "I noticed you tried to add something for me."
    m 1hua "That's really sweet...{w=0.3} but actually,{w=0.2} I have something for {i}you{/i}."

    m 1eua "Close your eyes for me? Just for a moment."
    m 1hua "No peeking~"

    scene black with dissolve_scene_full
    pause 1.2

    python:
        _journal_gift = store.journal.closed_book_path()

    if _journal_gift:
        show expression _journal_gift as journal_gift:
            xalign 0.5
            yalign 0.5
            zoom 0.55
        with Dissolve(0.6)
        pause 1.4
        hide journal_gift with Dissolve(0.4)
    else:
        pause 0.8

    call spaceroom(scene_change=True, dissolve_all=True)
    show monika 1hubsa at t11 zorder MAS_MONIKA_Z

    m 1hubsa "Okay... you can look now."
    m 3eub "It's a journal! Just for us."
    m 1eua "You can write in it, doodle, even tuck little photos into the pages..."
    m 3hua "And whenever you want, you can show me what you've been working on."
    m 1ekbsa "I thought it'd be nice if you had somewhere to keep pieces of us."
    m 5hubfa "There's a Journal button on the left now — open it whenever you like, okay?"

    python:
        persistent._journal_seen_intro = True
        persistent._journal_unlocked = True
        store.journal.ensure_folders()
        store.journal.ensure_spreads()
        try:
            store.mas_showEVL("journal_open_topic", "EVE", unlock=True)
        except Exception:
            try:
                ev = store.mas_getEV("journal_open_topic")
                if ev is not None:
                    ev.unlocked = True
            except Exception:
                pass

    return "derandom"


label journal_open_topic:
    if not persistent._journal_unlocked:
        m 1eka "I don't think I've given that to you yet..."
        m 3hua "Give me a little bit — I have a surprise planned."
        return

    m 1hua "Of course!"
    jump journal_button_entry
