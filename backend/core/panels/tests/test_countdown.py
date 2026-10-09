from datetime import date

from django.test import SimpleTestCase

from gradian_testing.covers import covers
from panels.countdown import countdown

EXAM = date(2027, 6, 25)


@covers("SYS-PNL-03")
class CountdownTests(SimpleTestCase):
    def test_before_the_exam_it_counts_the_days_in_persian(self) -> None:
        result = countdown(EXAM, date(2027, 2, 25))
        self.assertEqual(result["state"], "upcoming")
        self.assertEqual(result["days_remaining"], 120)
        self.assertEqual(result["label"], "۱۲۰ روز تا کنکور")
        self.assertEqual(result["date"], "2027-06-25")

    def test_the_day_before_is_one_day_away(self) -> None:
        result = countdown(EXAM, date(2027, 6, 24))
        self.assertEqual((result["state"], result["days_remaining"]), ("upcoming", 1))
        self.assertEqual(result["label"], "۱ روز تا کنکور")

    def test_on_the_day_itself(self) -> None:
        result = countdown(EXAM, EXAM)
        self.assertEqual((result["state"], result["days_remaining"]), ("today", 0))
        self.assertEqual(result["label"], "امروز روز کنکور است")

    def test_after_the_exam_nothing_is_negative(self) -> None:
        result = countdown(EXAM, date(2027, 7, 30))
        self.assertEqual((result["state"], result["days_remaining"]), ("past", 0))
        self.assertEqual(result["label"], "کنکور برگزار شده است")
