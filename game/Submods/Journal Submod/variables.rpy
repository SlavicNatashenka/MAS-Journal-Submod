default persistent._journal_seen_intro = False
default persistent._journal_unlocked = False
default persistent._journal_cover_color = "#1a2b45"
default persistent._journal_spreads = None
default persistent._journal_spread_index = 0
default persistent._journal_shown_count = 0

# Runtime (not saved)
default journal_mode = "write"
default journal_active_side = "left"
default journal_draw_color = "#2b2118"
default journal_draw_size = 4
default journal_placing = None
default journal_crop_file = None
default journal_picker_brightness = 1.0


# Journal text
style journal_page_text is default:
    font journal.page_font
    size 16
    color "#2b2118"
    outlines []

style journal_input is default:
    font journal.page_font
    size 18
    color "#2b2118"
    outlines []
