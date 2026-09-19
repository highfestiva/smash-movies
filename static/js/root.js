const app = document.getElementById('app');

function renderCountries(countries) {
  const cards = countries.map(country => `
    <div class="col-md-4 mb-3">
      <div class="card country-card h-100 shadow-sm" data-country="${country}">
        <div class="card-body d-flex align-items-center justify-content-center">
          <h5 class="mb-0 text-uppercase">${country}</h5>
        </div>
      </div>
    </div>
  `).join('');

  app.innerHTML = `
    <div class="mb-4">
      <h1>Pick a country</h1>
    </div>
    <div class="row">${cards}</div>
  `;

  document.querySelectorAll('.country-card').forEach(card => {
    card.addEventListener('click', () => {
      window.location.href = '/country.html?country=' + encodeURIComponent(card.dataset.country);
    });
  });
}

fetch('/data/metadata.json')
  .then(r => r.json())
  .then(meta => renderCountries(meta.countries || []))
  .catch(() => {
    app.innerHTML = '<div class="alert alert-warning">No country metadata available right now.</div>';
  });
