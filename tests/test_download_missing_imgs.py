import unittest

from scripts import download_missing_imgs


class DownloadMissingImgsTests(unittest.TestCase):
    def test_find_tmdb_poster_url_for_casablanca_1943_uses_expected_poster(self):
        poster_url = download_missing_imgs.find_tmdb_poster_url("Casablanca", 1943)

        print(poster_url)
        self.assertIsNotNone(poster_url)
        self.assertTrue("lGCEKlJo2CnWydQj7aamY7s1S7Q.jpg" in poster_url)


if __name__ == "__main__":
    unittest.main()
