"""Query contracts: preserve source ratios, missing values and input validation."""

import unittest
from typing import Any
from unittest.mock import patch

import nyckeltal as data

RECORDS = [
    {
        "organisationsnr": "0000000001",
        "myndighet": "Testmyndigheten",
        "cofogtypNomenklatur": "01",
        "cofogtypNamn": "Allmän förvaltning",
        "år": 2017,
        "typ": "Kostnader för personal",
        "värde": 0.0,
        "värdeDelatMedAntalAnställda": None,
    },
    {
        "organisationsnr": "0000000001",
        "myndighet": "Testmyndigheten",
        "cofogtypNomenklatur": "01",
        "cofogtypNamn": "Allmän förvaltning",
        "år": 2019,
        "typ": "Kostnader för personal",
        "värde": 1234.56,
        "värdeDelatMedAntalAnställda": 12.345,
    },
]


class IndicatorTests(unittest.TestCase):
    def setUp(self):
        self.records = patch.object(data, "load_records", return_value=RECORDS)
        self.records.start()
        self.addCleanup(self.records.stop)

    def test_missing_year_is_not_zero(self):
        result = data.get_indicators(
            "Kostnader för personal", ["0000000001"], start_year=2017, end_year=2019
        )
        self.assertEqual(result["years"], [2017, 2018, 2019])
        self.assertEqual(result["series"][0]["values"], [0.0, None, 1234.56])

    def test_source_ratio_and_null_are_preserved(self):
        result = data.get_indicators(
            "Kostnader för personal",
            ["0000000001"],
            denominator="Antal anställda",
            start_year=2017,
            end_year=2019,
        )
        self.assertEqual(result["series"][0]["values"], [None, None, 12.345])
        self.assertEqual(result["value_field"], "värdeDelatMedAntalAnställda")

    def test_organisation_and_cofog_codes_are_text(self):
        result = data.find_agencies("TESTMYNDIGHET")
        self.assertEqual(result[0]["organisationsnr"], "0000000001")
        self.assertEqual(result[0]["cofogtypNomenklatur"], "01")

    def test_invalid_filters_fail_explicitly(self):
        for kwargs in [
            {"metric": "Finns inte"},
            {"denominator": "Finns inte"},
            {"start_year": 2025, "end_year": 2017},
            {"organisation_numbers": ["0000000002"]},
            {"organisation_numbers": []},
        ]:
            arguments: dict[str, Any] = {
                "metric": "Kostnader för personal",
                "organisation_numbers": ["0000000001"],
            }
            arguments.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                data.get_indicators(**arguments)


if __name__ == "__main__":
    unittest.main()
