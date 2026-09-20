const app = document.getElementById('app');

const countryDetails = {
  se: { label: 'Sverige', flag: '🇸🇪', gradient: 'linear-gradient(135deg, #006aa7 0%, #fecc00 50%, #006aa7 100%)' },
  dk: { label: 'Danmark', flag: '🇩🇰', gradient: 'linear-gradient(135deg, #c8102e 0%, #ffffff 50%, #c8102e 100%)' },
  no: { label: 'Norge', flag: '🇳🇴', gradient: 'linear-gradient(135deg, #ba0c2f 0%, #ffffff 50%, #00205b 100%)' },
  fi: { label: 'Suomi', flag: '🇫🇮', gradient: 'linear-gradient(135deg, #ffffff 0%, #003580 50%, #ffffff 100%)' },
  is: { label: 'Ísland', flag: '🇮🇸', gradient: 'linear-gradient(135deg, #02529c 0%, #ffffff 50%, #dc1e35 100%)' },
  us: { label: 'United States', flag: '🇺🇸', gradient: 'linear-gradient(135deg, #b22234 0%, #ffffff 50%, #3c3b6e 100%)' },
  ca: { label: 'Canada', flag: '🇨🇦', gradient: 'linear-gradient(135deg, #ff0000 0%, #ffffff 50%, #ff0000 100%)' },
  gb: { label: 'United Kingdom', flag: '🇬🇧', gradient: 'linear-gradient(135deg, #012169 0%, #ffffff 50%, #c8102e 100%)' },
  au: { label: 'Australia', flag: '🇦🇺', gradient: 'linear-gradient(135deg, #00008b 0%, #ffffff 50%, #ff0000 100%)' },
  de: { label: 'Deutschland', flag: '🇩🇪', gradient: 'linear-gradient(135deg, #000000 0%, #dd0000 50%, #ffce00 100%)' },
  fr: { label: 'France', flag: '🇫🇷', gradient: 'linear-gradient(135deg, #0055a4 0%, #ffffff 50%, #ef4135 100%)' },
  nl: { label: 'Nederland', flag: '🇳🇱', gradient: 'linear-gradient(135deg, #ae1c28 0%, #ffffff 50%, #21468b 100%)' },
  ie: { label: 'Éire', flag: '🇮🇪', gradient: 'linear-gradient(135deg, #169b62 0%, #ffffff 50%, #ff883e 100%)' },
  nz: { label: 'New Zealand', flag: '🇳🇿', gradient: 'linear-gradient(135deg, #00247d 0%, #ffffff 50%, #cc142b 100%)' },
  ch: { label: 'Schweiz', flag: '🇨🇭', gradient: 'linear-gradient(135deg, #ff0000 0%, #ffffff 50%, #ff0000 100%)' },
  at: { label: 'Österreich', flag: '🇦🇹', gradient: 'linear-gradient(135deg, #ed2939 0%, #ffffff 50%, #ed2939 100%)' },
  be: { label: 'België', flag: '🇧🇪', gradient: 'linear-gradient(135deg, #000000 0%, #fdda24 50%, #ef3340 100%)' },
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
