"""Content blocks keep the shape the frontend relies on (SYS-PNL-04)."""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from gradian_testing.covers import covers
from panels import content
from panels.models import ContentBlock
from tests.helpers import seed


@covers("SYS-PNL-04", "SYS-DATA-06")
class SeedContentTests(SimpleTestCase):
    def test_every_block_of_the_demo_content_has_the_documented_shape(self) -> None:
        loaded = seed.content()
        blocks = {
            **{f"landing.{name}": data for name, data in loaded.landing.items()},
            **{f"widget.{name}": data for name, data in loaded.widgets.items()},
        }
        self.assertEqual(set(blocks), set(content.SHAPES))
        for key, data in blocks.items():
            with self.subTest(block=key):
                self.assertEqual(content.check_block(key, data), [])

    def test_the_generator_and_the_app_agree_on_the_block_names(self) -> None:
        self.assertEqual(seed.seed_generate.LANDING_SECTIONS, tuple(content.LANDING_SECTIONS))
        self.assertEqual(seed.seed_generate.WIDGETS, tuple(content.WIDGETS))

    def test_a_wrong_shape_is_reported_with_the_path_of_the_problem(self) -> None:
        problems = content.check_block("landing.statistics", [{"key": "a", "value": "1"}])
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0], "0.label: This field is required.")

    def test_an_unknown_block_is_reported(self) -> None:
        self.assertIn("unknown block", content.check_block("landing.nope", {})[0])


class BlockModelTests(TestCase):
    def test_saving_through_a_form_refuses_a_block_of_the_wrong_shape(self) -> None:
        block = ContentBlock(key="landing.hero", data={"title": "only a title"})
        with self.assertRaises(ValidationError) as caught:
            block.full_clean()
        self.assertIn("data", caught.exception.message_dict)

    def test_a_valid_block_passes(self) -> None:
        ContentBlock(key="landing.hero", data=dict(seed.content().landing["hero"])).full_clean()
