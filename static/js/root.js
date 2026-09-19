const app = document.getElementById('app');

const countryDetails = {
  se: { label: 'Sweden', flag: '🇸🇪', gradient: 'linear-gradient(135deg, #0f766e 0%, #14b8a6 35%, #34d399 100%)' },
  dk: { label: 'Denmark', flag: '🇩🇰', gradient: 'linear-gradient(135deg, #1d4ed8 0%, #60a5fa 35%, #93c5fd 100%)' },
  no: { label: 'Norway', flag: '🇳🇴', gradient: 'linear-gradient(135deg, #7c3aed 0%, #a78bfa 40%, #c4b5fd 100%)' },
  fi: { label: 'Finland', flag: '🇫🇮', gradient: 'linear-gradient(135deg, #2563eb 0%, #38bdf8 40%, #7dd3fc 100%)' },
};

function renderCountries(countries) {
  const cards = countries.map(country => {
    const details = countryDetails[country] || {
      label: country.toUpperCase(),
      flag: '🌍',
      gradient: 'linear-gradient(135deg, #374151 0%, #64748b 38%, #94a3b8 100%)',
    };

    return `
      <div class="col-md-4 mb-4">
        <div class="card country-card h-100" data-country="${country}" style="--country-gradient: ${details.gradient};">
          <div class="card-body">
            <div>
              <div class="country-flag">${details.flag}</div>
              <div class="country-subtitle">Region</div>
            </div>
            <div>
              <h2 class="country-name">${details.label}</h2>
            </div>
            <div class="country-link">Open catalogue</div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  app.innerHTML = `
    <div class="landing-shell">
      <div class="hero-panel">
        <div class="hero-kicker">Global streaming</div>
        <h1>Pick a country</h1>
        <p>Explore the hottest titles across regions and compare what’s available where.</p>
      </div>
      <div class="country-grid row g-4">${cards}</div>
    </div>
  `;

  document.querySelectorAll('.country-card').forEach(card => {
    card.addEventListener('click', () => {
      window.location.href = './list.html?country=' + encodeURIComponent(card.dataset.country);
    });
  });
}

fetch('./data/metadata.json')
  .then(r => r.json())
  .then(meta => renderCountries(Object.keys(meta.countries || {})))
  .catch(() => {
    app.innerHTML = '<div class="alert alert-warning">No country metadata available right now.</div>';
  });
