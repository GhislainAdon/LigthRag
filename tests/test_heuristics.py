"""Tests for the plain-text structure heuristics in ingest.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ingest import heuristic_headers


def _apply(text):
    lines, changed = heuristic_headers(text.split('\n'))
    return '\n'.join(lines), changed


class TestHeuristicHeaders:
    def test_all_caps_line_becomes_h2(self):
        out, changed = _apply("CONTEXTE DE LA MISSION\nDu texte normal.")
        assert changed
        assert out.startswith('## CONTEXTE DE LA MISSION')

    def test_short_colon_line_becomes_h3(self):
        out, changed = _apply("Bases de données :\nOracle\nPostgreSQL")
        assert changed
        assert out.startswith('### Bases de données')

    def test_normal_sentences_untouched(self):
        text = ("Le prestataire interviendra sur les technologies "
                "et environnements suivants :\nOracle\nRedHat 7 / 8 / 9")
        out, changed = _apply(text)
        assert not changed
        assert out == text

    def test_lowercase_colon_line_untouched(self):
        out, changed = _apply("les Business Line IT du SI CASA :")
        assert not changed

    def test_short_acronym_lines_are_a_known_tradeoff(self):
        # 'API REST' is promoted (all-caps): harmless over-segmentation
        # accepted to keep the heuristic simple.
        out, changed = _apply("API REST")
        assert changed

    def test_mixed_case_title_without_colon_untouched(self):
        out, changed = _apply("Livrables attendus\nScripts Ansible")
        assert not changed
