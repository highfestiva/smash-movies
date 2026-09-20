import unittest
from unittest import mock

from scripts import update_services


class UpdateServicesTests(unittest.TestCase):
    def test_build_streams_on_uses_known_services(self):
        metadata_services = {
            "Netflix": "netflix",
            "Amazon Prime": "prime",
            "Apple TV": "apple",
            "HBO": "hbo",
        }
        sources = [
            {"name": "Prime Video", "region": "SE"},
            {"name": "Netflix", "region": "SE"},
            {"name": "HBO Max", "region": "SE"},
            {"name": "Unknown Service", "region": "SE"},
        ]

        self.assertEqual(
            update_services.build_streams_on(sources, metadata_services),
            ["netflix", "prime", "hbo"],
        )

    def test_find_streaming_sources_uses_watchmode_title_and_sources_endpoints(self):
        search_response = mock.Mock()
        search_response.json.return_value = {
            "title_results": [{"resultType": "title", "year": 2023, "id": 123}]
        }
        source_response = mock.Mock()
        source_response.json.return_value = [{
            "source_id": 26,
            "name": "Prime Video",
            "region": "SE",
        }]

        with mock.patch.object(update_services.requests, "get", side_effect=[search_response, source_response]) as get_mock:
            sources = update_services.find_streaming_sources("Godzilla Minus One", 2023, region="SE")

        self.assertEqual(sources, [{"source_id": 26, "name": "Prime Video", "region": "SE"}])
        self.assertEqual(get_mock.call_count, 2)
        self.assertIn("/search/", get_mock.call_args_list[0].args[0])
        self.assertIn("/title/123/sources/", get_mock.call_args_list[1].args[0])

    def test_filter_sources_for_country_keeps_only_matching_country_sources(self):
        sources = [
            {"name": "Netflix", "region": "SE"},
            {"name": "HBO Max", "region": "DK"},
            {"name": "Prime Video", "region": "SE"},
            {"name": "Disney+", "region": "US"},
        ]

        country_sources = update_services.filter_sources_for_country(sources, "SE")

        self.assertEqual(country_sources, [
            {"name": "Netflix", "region": "SE"},
            {"name": "Prime Video", "region": "SE"},
        ])



if __name__ == "__main__":
    unittest.main()
