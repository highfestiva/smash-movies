const app = document.getElementById('app');
const country = new URLSearchParams(window.location.search).get('country') || 'se';
const defaultServiceNames = ['netflix', 'hbo', 'prime'];
let serviceNames = [...defaultServiceNames];
const serviceLabels = { netflix: 'Netflix', hbo: 'HBO', prime: 'Prime' };
const serviceStyles = {
  netflix: { className: 'service-netflix', color: '#dc3545' },
  hbo: { className: 'service-hbo', color: '#0d6efd' },
  prime: { className: 'service-prime', color: '#ffc107' },
};
const selectedServices = new Set();
let allMovies = [];

function readSelectedServicesFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const serviceValues = params.getAll('service');

  if (!serviceValues.length) {
    return [];
  }

  return serviceValues
    .flatMap(value => value.split(','))
    .map(value => value.trim().toLowerCase())
    .filter(value => serviceStyles[value] || defaultServiceNames.includes(value));
}

function syncSelectedServicesWithUrl() {
  const params = new URLSearchParams(window.location.search);
  params.delete('service');

  if (selectedServices.size > 0) {
    const ordered = serviceNames.filter(service => selectedServices.has(service));
    ordered.forEach(service => params.append('service', service));
  }

  const query = params.toString();
  const nextUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
  window.history.replaceState({}, '', nextUrl);
}

function getPreferredMovieDetails(movie) {
  const serviceEntries = serviceNames
    .filter(service => movie.services && movie.services[service])
    .map(service => movie.services[service]);

  for (const serviceMovie of serviceEntries) {
    if (serviceMovie.title || serviceMovie.synopsis) {
      return {
        title: serviceMovie.title || movie.title,
        synopsis: serviceMovie.synopsis || movie.synopsis,
      };
    }
  }

  return {
    title: movie.title,
    synopsis: movie.synopsis,
  };
}

function renderServiceFilters() {
  const controls = serviceNames.map(service => `
    <button
      type="button"
      class="service-filter-btn ${serviceStyles[service].className} ${selectedServices.has(service) ? 'active' : ''}"
      data-service="${service}"
      aria-pressed="${selectedServices.has(service) ? 'true' : 'false'}"
    >
      ${serviceLabels[service]}
    </button>
  `).join('');

  const host = document.getElementById('service-filter-host');
  if (host) {
    host.innerHTML = `
      <div class="service-filter-bar list-service-host">
        <span class="navbar-kicker">Services</span>
        ${controls}
      </div>
    `;
  }
}

function getFilteredMovies(movies) {
  if (selectedServices.size === 0) {
    return movies;
  }

  return movies.filter(movie => {
    const movieServices = Object.keys(movie.services || {});
    return movieServices.some(name => selectedServices.has(name));
  });
}

function renderMovies(items) {
  const cards = items.map(movie => {
    const preferred = getPreferredMovieDetails(movie);
    const title = preferred.title || movie.title;
    const synopsis = preferred.synopsis || movie.synopsis || 'No synopsis available.';
    const badges = [];
    if (movie.services && movie.services.netflix) badges.push('<span class="badge bg-danger">Netflix</span>');
    if (movie.services && movie.services.hbo) badges.push('<span class="badge bg-primary">HBO</span>');
    if (movie.services && movie.services.prime) badges.push('<span class="badge bg-warning text-dark">Prime</span>');

    return `
      <div class="col-md-4 mb-4">
        <div class="card movie-card h-100 shadow-sm">
          ${movie.image ? `
            <div class="poster-shell" style="--poster-bg: url('${movie.image}');">
              <img class="poster-image" src="${movie.image}" alt="${title}">
            </div>
          ` : '<div class="poster-shell"></div>'}
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">${movie.rank}. ${title} (${movie.year || ''})</h5>
            <p class="card-text text-muted flex-grow-1">${synopsis}</p>
            <div class="mt-auto d-flex gap-2 flex-wrap">
              ${badges.join('')}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  const countryHeader = document.getElementById('country-header');
  if (countryHeader) {
    countryHeader.textContent = '';
  }

  const visibleMovies = items.length ? items : [];
  renderServiceFilters();
  const movieGrid = visibleMovies.length ? `<div class="movie-grid row g-4">${cards}</div>` : '<div class="alert alert-light border">No movies match the selected services.</div>';

  app.innerHTML = `
    <div class="list-shell">
      <div class="hero-panel list-hero">
        <div class="list-top-row">
          <div class="list-title-group">
            <div class="list-kicker">Streaming catalogue</div>
            <h1>${country.toUpperCase()}</h1>
          </div>
          <div class="list-count">${visibleMovies.length} movies</div>
          <div class="list-meta">${selectedServices.size === 0 ? 'All movies' : `${selectedServices.size} service${selectedServices.size === 1 ? '' : 's'} selected`}</div>
        </div>
      </div>
      ${movieGrid}
    </div>
  `;

  document.querySelectorAll('.service-filter-btn').forEach(button => {
    button.addEventListener('click', () => {
      const service = button.dataset.service;
      if (selectedServices.has(service)) {
        selectedServices.delete(service);
      } else {
        selectedServices.add(service);
      }

      syncSelectedServicesWithUrl();
      button.classList.toggle('active', selectedServices.has(service));
      button.setAttribute('aria-pressed', String(selectedServices.has(service)));

      const filteredMovies = getFilteredMovies(allMovies);
      renderMovies(filteredMovies);
    });
  });
}

const initialServices = readSelectedServicesFromUrl();
if (initialServices.length) {
  initialServices.forEach(service => selectedServices.add(service));
}

fetch('./data/metadata.json')
  .then(r => r.json())
  .then(meta => {
    if (Array.isArray(meta.services) && meta.services.length) {
      serviceNames = meta.services.filter(service => serviceStyles[service] || defaultServiceNames.includes(service));
    }
    return fetch('./data/rotten_300.json');
  })
  .then(r => r.json())
  .then(rottenMovies => {
    allMovies = rottenMovies.map(movie => ({ ...movie, services: {} }));

    const promises = serviceNames.map(service =>
      fetch(`./data/${country}/${service}.json`)
        .then(res => (res.ok ? res.json() : []))
        .then(serviceMovies => {
          serviceMovies.forEach(serviceMovie => {
            const match = allMovies.find(m => m.rank === serviceMovie.rank);
            if (match) match.services[service] = serviceMovie;
          });
        })
        .catch(() => {})
    );

    Promise.all(promises).then(() => {
      const filteredMovies = getFilteredMovies(allMovies);
      renderMovies(filteredMovies);
    });
  })
  .catch(() => {
    app.innerHTML = '<div class="alert alert-danger">Could not load country data.</div>';
  });
