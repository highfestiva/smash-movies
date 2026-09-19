from bs4 import BeautifulSoup
import unittest

import web_serve
from scripts import update_se_netflix


class NetflixAvailabilityParserTests(unittest.TestCase):
    def test_extract_first_results_link_from_html(self):
        html = '''
        <html>
          <body>
            <div class="results">
              <ul class="titles">
              <li>2020 <a href="/film/arrival">Arrival</a></li>
              <li>2023 <a href="/film/other">Other</a></li>
            </div>
          </body>
        </html>
        '''
        self.assertEqual(
            update_se_netflix.extract_results_link(html, 2020),
            "/film/arrival",
        )

    def test_detect_unavailable_movie_page(self):
        page = "<html><body>är inte tillgänglig på Netflix i Sverige</body></html>"
        self.assertFalse(update_se_netflix.is_available_in_sweden(page))

    def test_detect_available_movie_page(self):
        page = "<html><body>Streama nu på Netflix</body></html>"
        self.assertTrue(update_se_netflix.is_available_in_sweden(page))

    def test_clean_title(self):
        title_html = "<h1> <strong>Film.</strong>Joråsåattde...</h1>"
        title_h1 = BeautifulSoup(title_html, "html.parser")
        extracted = update_se_netflix.extract_movie_title(title_h1)
        assert extracted == "Joråsåattde..."

    def test_improve_movie_data(self):
        movie = {"title": "Old title", "synopsis": "Old synopsis"}
        page_html = '''
        <html>
          <body>
            <div class="main">
              <h1><strong>Movie.</strong> A Real Movie Title</h1>
            </div>
            <p class="synopsis">A short, updated synopsis.</p>
          </body>
        </html>
        '''

        updated = update_se_netflix.improve_movie_data(page_html, movie)

        self.assertEqual(updated["title"], "A Real Movie Title")
        self.assertEqual(updated["synopsis"], "A short, updated synopsis.")


class WebServeTests(unittest.TestCase):
    def test_index_lists_countries_only(self):
        client = web_serve.app.test_client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
        country_names = [link.get_text(strip=True) for link in soup.select("a.btn-outline-primary")]

        self.assertNotIn("rotten_300", country_names)
        self.assertIn("se", country_names)
        self.assertNotIn("netflix", country_names)


if __name__ == "__main__":
    unittest.main()
