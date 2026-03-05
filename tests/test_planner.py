from astrace.planner import ResearchPlanner, decide_mode


def test_decide_mode_auto_deep():
    mode, reason = decide_mode(
        "Please do comprehensive deep research and compare multi-source evidence",
        "auto",
    )
    assert mode == "deep"
    assert "auto selected deep" in reason


def test_decide_mode_forced():
    mode, reason = decide_mode("anything", "shallow")
    assert mode == "shallow"
    assert "forced" in reason


def test_planner_seeds_non_empty():
    planner = ResearchPlanner()
    seeds = planner.seed_queries("AstrBot NapCat", "deep")
    assert seeds
    assert "AstrBot NapCat" in seeds[0]
