class Constant:
    QUERY_KEYS = frozenset(
        ['limit', 'offset', 'query', 'fuzzy_query', 'sort', 'count_only'])

    PATCH_KEYS = frozenset(['create', 'update', 'remove'])

    SKILL_IDS = frozenset(['note_mirror', 'skill_mithra', 'skill_salt', 'gauge_exhaustion', 'skill_nell', 'gauge_easy|note_mirror', 'skill_hp_slow_drain', 'skill_saya_uncap', 'audio_gcemptyhit_pack_groovecoaster', 'frags_nami', 'eto_uncap', 'gauge_ilith_summer', 'visual_ink', 'ayu_uncap', 'visual_tomato_pack_tonesphere', 'skill_lost_to_85', 'frags_ongeki', 'skill_doroc_uncap', 'gauge_easy', 'skill_saya_konzetsu',
                           'gauge_hard|fail_frag_minus_100', 'visual_hide_hp', 'skill_milk', 'skill_tsumugi', 'gauge_safe_10', 'skill_kanae_uncap', 'combo_100-frag_1', 'skill_shama', 'skill_luna_ilot', 'gauge_seele', 'skill_aichan', 'visual_ghost_skynotes', 'skill_hprate_based_on_hp', 'challenge_fullcombo_0gauge', 'frags_ongeki_slash', 'gauge_regulus', 'skill_selene', 'gauge_hard|note_mirror', 'skill_frag_doubled_after_earning_X', 'skill_kou_winter...', ])
