init -990 python in mas_submod_utils:
    # journal_header_register
    Submod(
        author="Natshenka",
        name="Journal",
        version="1.0.3",
        description="Monika gives you a journal — write, draw, and scrapbook pages to share with her. ^^",
    )


init 5 python in mas_bookmarks_derand:
    # journal_header_derand
    label_prefix_map["journal_"] = label_prefix_map["monika_"]
