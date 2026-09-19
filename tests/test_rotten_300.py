import os
import tempfile
import unittest

from bs4 import BeautifulSoup

from scripts import update_rotten_300


class Rotten300Tests(unittest.TestCase):
    def test_slugify_title_for_shared_filename(self):
        self.assertEqual(update_rotten_300.slugify_title("The Godfather"), "the-godfather")
        self.assertEqual(update_rotten_300.slugify_title("  In the Mood for Love  "), "in-the-mood-for-love")

    def test_dom_pattern_extracts_year_and_rank(self):
        html = '''
        <tr>
          <td>23.</td>
          <td>
            <div class="rkv-block">
              <span class="meta-data-wrapper">
                <a class="meta-title" href="https://www.rottentomatoes.com/m/the_godfather">The Godfather</a>
                <span class="meta-year">(1972)</span>
              </span>
            </div>
          </td>
        </tr>
        '''
        soup = BeautifulSoup(html, "html.parser")
        anchor = soup.select_one("a.meta-title")

        self.assertEqual(update_rotten_300._extract_year(anchor), 1972)
        self.assertEqual(update_rotten_300._extract_rank(anchor), 23)

    def test_prevent_redownload_when_image_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "shared-image.jpg")
            with open(target, "wb") as fh:
                fh.write(b"fake")

            result = update_rotten_300.ensure_local_image(
                "https://example.com/movie.jpg",
                target,
                skip_if_exists=True,
            )

            self.assertEqual(result, target)
            with open(target, "rb") as fh:
                self.assertEqual(fh.read(), b"fake")

    def test_download_image_skips_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "movie.jpg")
            with open(target, "wb") as fh:
                fh.write(b"existing")

            result = update_rotten_300.download_image("https://example.com/movie.jpg", target)
            self.assertEqual(result, target)
            with open(target, "rb") as fh:
                self.assertEqual(fh.read(), b"existing")


if __name__ == "__main__":
    unittest.main()
