import sys
import unittest
from unittest import mock

from bs4 import BeautifulSoup

from scripts import update_countries


class CountriesUpdaterTests(unittest.TestCase):
    def test_get_country_language(self):
        self.assertEqual(update_countries.get_country_language("se"), "sv-SE")
        self.assertEqual(update_countries.get_country_language("dk"), "da-DK")

    def test_extract_movie_title(self):
        html = """
        <html>
          <body>
            <div class="title">
              <a href="/film/arrival">Arrival</a>
            </div>
          </body>
        </html>
        """
        self.assertEqual(update_countries.extract_movie_title(html), "Arrival")

    def test_is_service_available_detects_service_names(self):
        html = """
        <html>
          <body>
            <div class="poster">
              <a title="Available on Netflix">Netflix</a>
            </div>
          </body>
        </html>
        """
        self.assertTrue(update_countries.is_service_available(html, ["netflix"]))
        self.assertFalse(update_countries.is_service_available(html, ["hbo"]))

    def test_scrape_movies_writes_single_country_movies_file(self):
        rotten_movies = [{
            "rank": 1,
            "title": "Example Movie",
            "year": 2024,
            "image": "image.jpg",
        }]

        with mock.patch.object(update_countries, "load_metadata", return_value={"countries": ["se"], "services": {"Netflix": "netflix", "HBO": "hbo"}}), \
             mock.patch("builtins.open", mock.mock_open(read_data="")), \
             mock.patch.object(update_countries, "fetch_search_page", return_value="<html>search</html>"), \
             mock.patch.object(update_countries, "fetch_movie_page", return_value="<html><div class='title'><a>Example Movie</a></div><div class='overview'>A nice synopsis.</div><a title='Available on Netflix'>Netflix</a></html>"), \
             mock.patch.object(update_countries, "write_country_movies_file") as write_mock, \
             mock.patch("json.load", return_value=rotten_movies):
            result = update_countries.scrape_movies(start_index=0, end_index=0)

        self.assertEqual(result["se"][0]["title"], "Example Movie")
        self.assertEqual(result["se"][0]["streams_on"], ["netflix"])
        self.assertNotIn("image", result["se"][0])
        self.assertNotIn("year", result["se"][0])
        write_mock.assert_called_once_with("se", result["se"])

    def test_iter_service_aliases_maps_long_names_to_short_tags(self):
        aliases = list(update_countries.iter_service_aliases({"Netflix": "netflix", "HBO": "hbo"}))
        self.assertEqual(aliases, [("netflix", "netflix"), ("hbo", "hbo")])

    def test_parse_args_reads_indexes(self):
        with mock.patch.object(sys, "argv", ["update_countries.py", "--start-index", "4", "--end-index", "7"]):
            args = update_countries.parse_args()

        self.assertEqual(args.start_index, 4)
        self.assertEqual(args.end_index, 7)

    def test_fetch_search_page_for_real_title_is_not_blocked(self):
        search_page = update_countries.fetch_search_page("The Battle of Algiers", "sv-SE")

        self.assertIsNotNone(search_page)

        plain_text = BeautifulSoup(search_page, "html.parser").get_text(" ", strip=True).lower()
        self.assertIn("the battle of algiers", plain_text)
        self.assertNotIn("verify you are human", plain_text)
        self.assertNotIn("checking your browser before accessing", plain_text)
        self.assertNotIn("please complete the security check", plain_text)
        self.assertNotIn("why have i been blocked", plain_text)

        movie_page = update_countries.fetch_movie_page(search_page)
        self.assertIsNotNone(movie_page)
        self.assertEqual(update_countries.extract_movie_title(movie_page), "Slaget om Alger")

    def test_fetch_movie_page_contains_uppsala_synopsis_for_fanny_and_alexander(self):
        search_page = update_countries.fetch_search_page("Fanny and Alexander", "sv-SE")
        self.assertIsNotNone(search_page)

        movie_page = update_countries.fetch_movie_page(search_page)
        self.assertIsNotNone(movie_page)

        synopsis = update_countries.extract_movie_synopsis(movie_page)
        self.assertIsNotNone(synopsis)
        self.assertIn("utspelar sig i Uppsala", synopsis)

    def test_godzilla_minus_one_is_streaming_on_netflix(self):
        search_page = update_countries.fetch_search_page("Godzilla Minus One", "sv-SE")
        self.assertIsNotNone(search_page)

        movie_page = update_countries.fetch_movie_page(search_page)
        self.assertIsNotNone(movie_page)

        self.assertTrue(update_countries.is_service_available(movie_page, ["netflix"]))


if __name__ == "__main__":
    unittest.main()
