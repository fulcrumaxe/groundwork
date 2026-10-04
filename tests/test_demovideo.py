"""Demo-video pipeline pure helpers: durations, concat, ffmpeg argv, framing."""
import unittest

from tools import demo_video as dvmod
from tools.demos import answerhist as pilot_i
from tools.demos import halflife as pilot_f


def _beats(total=42.0):
    tail = total - 26.0
    return [
        {"type": "title", "duration": 5, "title": "T"},
        {"type": "chrome", "duration": 6, "url_path": "/status"},
        {"type": "terminal", "duration": 15,
         "commands": [["echo", "hi"]]},
        {"type": "title", "duration": tail, "title": "Out"},
    ]


def _scenario(**over):
    scn = {"id": "x", "kind": "improvement", "batch": 1, "title": "X",
           "beats": _beats()}
    scn.update(over)
    return scn


class TotalDurationTest(unittest.TestCase):
    def test_sums_beats(self):
        self.assertEqual(dvmod.total_duration(_beats(42.0)), 42.0)

    def test_hostile_counts_zero(self):
        self.assertEqual(dvmod.total_duration(None), 0.0)
        self.assertEqual(dvmod.total_duration([None, {}, {"duration": "x"}]),
                         0.0)


class ValidateScenarioTest(unittest.TestCase):
    def test_valid_passes(self):
        self.assertEqual(dvmod.validate_scenario(_scenario()), [])

    def test_pilots_filmable(self):
        self.assertEqual(dvmod.validate_scenario(pilot_i.SCENARIO), [])
        self.assertEqual(dvmod.validate_scenario(pilot_f.SCENARIO), [])

    def test_all_scenarios_filmable(self):
        for name in dvmod.list_scenarios():
            with self.subTest(scenario=name):
                scn, _seed = dvmod.load_scenario(name)
                self.assertEqual(dvmod.validate_scenario(scn), [])

    def test_scenarios_import_without_repo_root(self):
        # The film process runs as tools/demo_video.py, so only tools/
        # is on sys.path: scenario modules must be stdlib-only at
        # module level (groundwork imports inside beat command strings
        # are fine -- those run as subprocesses from the repo root).
        import ast
        from pathlib import Path
        demos = Path(dvmod.__file__).resolve().parent / "demos"
        for mod in sorted(demos.glob("*.py")):
            if mod.name.startswith("_"):
                continue
            with self.subTest(scenario=mod.stem):
                tree = ast.parse(mod.read_text())
                roots = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        roots.update(a.name.split(".")[0]
                                     for a in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        if (node.module or "").split(".")[0]:
                            roots.add(node.module.split(".")[0])
                self.assertNotIn("groundwork", roots)

    def test_missing_keys(self):
        errs = dvmod.validate_scenario({"id": "x"})
        self.assertTrue(any("kind" in e for e in errs))
        self.assertTrue(any("beats" in e for e in errs))

    def test_bad_kind(self):
        errs = dvmod.validate_scenario(_scenario(kind="task"))
        self.assertTrue(any("kind" in e for e in errs))

    def test_bad_batch(self):
        for bad in (None, 0, -3, "1", 1.5, True):
            with self.subTest(batch=bad):
                errs = dvmod.validate_scenario(_scenario(batch=bad))
                self.assertTrue(any("batch" in e for e in errs))

    def test_output_paths_batch_kind_layout(self):
        from pathlib import Path
        mp4, gif, jsn, frames = dvmod.output_paths(
            Path("demos"), _scenario(id="nav-counts", item="I-11"))
        self.assertEqual(
            str(mp4),
            "demos/batch-1/improvement/nav-counts-I-11/nav-counts.mp4")
        self.assertEqual(
            str(gif),
            "demos/batch-1/improvement/nav-counts-I-11/nav-counts.gif")
        self.assertEqual(
            str(jsn),
            "demos/batch-1/improvement/nav-counts-I-11/nav-counts.json")
        self.assertEqual(
            str(frames),
            "demos/batch-1/improvement/nav-counts-I-11/"
            "nav-counts-frames")
        mp4, _gif, _jsn, _frames = dvmod.output_paths(
            Path("demos"),
            _scenario(id="halflife", kind="feature", batch=29,
                      item="F-182"))
        self.assertEqual(
            str(mp4),
            "demos/batch-29/feature/halflife-F-182/halflife.mp4")
        mp4, _gif, _jsn, _frames = dvmod.output_paths(
            Path("demos"),
            _scenario(id="anki-export", kind="feature"))
        self.assertEqual(
            str(mp4),
            "demos/batch-1/feature/anki-export/anki-export.mp4")

    def test_bad_item(self):
        for bad in ("", "197", "X-1", "I-", 197):
            with self.subTest(item=bad):
                errs = dvmod.validate_scenario(_scenario(item=bad))
                self.assertTrue(any("item" in e for e in errs))
        self.assertEqual(
            dvmod.validate_scenario(_scenario(item="I-197")), [])

    def test_bad_beat_type(self):
        errs = dvmod.validate_scenario(
            _scenario(beats=[{"type": "audio", "duration": 40}]))
        self.assertTrue(any("bad type" in e for e in errs))

    def test_beat_duration_bounds(self):
        errs = dvmod.validate_scenario(
            _scenario(beats=[{"type": "title", "duration": 1, "title": "T"}]))
        self.assertTrue(any("outside 2-20" in e for e in errs))

    def test_total_window(self):
        short = _scenario(beats=[{"type": "title", "duration": 5,
                                   "title": "T"}])
        self.assertTrue(any("outside 30-60" in e
                            for e in dvmod.validate_scenario(short)))
        long = _scenario(beats=[{"type": "title", "duration": 20,
                                  "title": "T"}] * 4)
        self.assertTrue(any("outside 30-60" in e
                            for e in dvmod.validate_scenario(long)))

    def test_per_type_requirements(self):
        no_title = _scenario(beats=[{"type": "title", "duration": 40}])
        self.assertTrue(any("needs title" in e
                            for e in dvmod.validate_scenario(no_title)))
        no_path = _scenario(beats=[{"type": "chrome", "duration": 40}])
        self.assertTrue(any("needs url_path" in e
                            for e in dvmod.validate_scenario(no_path)))
        no_cmds = _scenario(beats=[{"type": "terminal", "duration": 40}])
        self.assertTrue(any("needs commands" in e
                            for e in dvmod.validate_scenario(no_cmds)))

    def test_hostile_never_raises(self):
        self.assertTrue(dvmod.validate_scenario(None))
        self.assertTrue(dvmod.validate_scenario("x"))


class ConcatListTest(unittest.TestCase):
    def test_durations_and_bare_tail(self):
        text = dvmod.build_concat_list([("/a/b0.jpeg", 5), ("/a/b1.jpeg", 6)])
        self.assertIn("file '/a/b0.jpeg'\nduration 5.000", text)
        self.assertIn("file '/a/b1.jpeg'\nduration 6.000", text)
        self.assertTrue(text.rstrip().endswith("file '/a/b1.jpeg'"))

    def test_empty(self):
        self.assertEqual(dvmod.build_concat_list([]), "")


class FfmpegCmdTest(unittest.TestCase):
    def test_mp4_trims_to_total(self):
        cmd = dvmod.ffmpeg_cmd("list.txt", "o.mp4", 43.0)
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("-t", cmd)
        self.assertEqual(cmd[cmd.index("-t") + 1], "43.000")
        self.assertIn("libx264", cmd)
        self.assertEqual(cmd[cmd.index("-crf") + 1], "18")
        vf = cmd[cmd.index("-vf") + 1]
        self.assertIn("scale=1280:720", vf)
        self.assertIn("fps=30", vf)

    def test_gif_loops_and_trims(self):
        cmd = dvmod.gif_cmd("list.txt", "o.gif", 40.0)
        self.assertIn("-t", cmd)
        self.assertEqual(cmd[cmd.index("-t") + 1], "40.000")
        self.assertIn("paletteuse", cmd[cmd.index("-vf") + 1])
        self.assertIn("0", cmd[cmd.index("-loop") + 1:cmd.index("-loop") + 2])


class DurationGateTest(unittest.TestCase):
    def test_window_edges(self):
        self.assertTrue(dvmod.check_duration_ok(30.0))
        self.assertTrue(dvmod.check_duration_ok(60.0))
        self.assertFalse(dvmod.check_duration_ok(29.9))
        self.assertFalse(dvmod.check_duration_ok(60.1))
        self.assertFalse(dvmod.check_duration_ok(None))


class HtmlCardsTest(unittest.TestCase):
    def test_title_escapes(self):
        out = dvmod.title_html("K", "<b>T</b>", "S&S")
        self.assertIn("&lt;b&gt;T&lt;/b&gt;", out)
        self.assertIn("S&amp;S", out)

    def test_terminal_escapes_and_caps(self):
        out = dvmod.terminal_html("<cap>", [(["echo", "<x>"], "o&o")])
        self.assertIn("&lt;cap&gt;", out)
        self.assertIn("&lt;x&gt;", out)
        self.assertIn("o&amp;o", out)


class FrameJsTest(unittest.TestCase):
    def test_caption_path(self):
        js = dvmod.frame_js("Hello")
        self.assertIn("demo-cap", js)
        self.assertIn("Hello", js)
        self.assertIn("caption-ok", js)

    def test_focus_path(self):
        js = dvmod.frame_js("Hi", "#status-b29-answerhist")
        self.assertIn("#status-b29-answerhist", js)
        self.assertIn("framed", js)
        self.assertIn("focus-missing", js)
        self.assertNotIn("position:fixed", js)

    def test_caption_escaped_for_js(self):
        js = dvmod.frame_js('a"b\\c')
        self.assertIn('"a\\"b\\\\c"', js)


class RenderBeatTest(unittest.TestCase):
    def test_substitutes_seed_tokens(self):
        beat = {"type": "chrome", "url_path": "/due",
                "js": ["() => '/cards/{seed_card_id}/review'"]}
        out = dvmod.render_beat(beat, {"card_id": "C1"})
        self.assertIn("/cards/C1/review", out["js"][0])
        self.assertNotIn("{seed_", str(out))

    def test_no_tokens_passthrough(self):
        beat = {"type": "title", "duration": 5, "title": "T"}
        self.assertEqual(dvmod.render_beat(beat, {}), beat)

    def test_hostile_never_raises(self):
        self.assertEqual(dvmod.render_beat(None, None), None)


if __name__ == "__main__":
    unittest.main()
