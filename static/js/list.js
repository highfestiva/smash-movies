const app = document.getElementById('app');
const country = new URLSearchParams(window.location.search).get('country') || 'se';
let serviceNames = [];
let serviceLabels = {};
const selectedServices = new Set();
let allMovies = [];

function normalizeServiceMetadata(meta) {
  const rawServices = meta && meta.services;
  if (!rawServices) {
    serviceNames = [];
    serviceLabels = {};
    return;
  }

  const entries = Array.isArray(rawServices)
    ? rawServices.map(service => [String(service), String(service)])
    : Object.entries(rawServices).map(([label, code]) => [String(label).trim(), String(code).trim()]);

  const normalized = entries
    .map(([label, code]) => [String(code).trim().toLowerCase(), String(label).trim()])
    .filter(([code, label]) => code && label);

  if (!normalized.length) {
    serviceNames = [];
    serviceLabels = {};
    return;
  }

  serviceNames = [...new Set(normalized.map(([code]) => code))];
  serviceLabels = Object.fromEntries(normalized.map(([code, label]) => [code, label]));
}

function readSelectedServicesFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const serviceValues = params.getAll('service');

  if (!serviceValues.length) {
    return [];
  }

  return serviceValues
    .flatMap(value => value.split(','))
    .map(value => value.trim().toLowerCase())
    .filter(value => serviceNames.includes(value));
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

function mergeMovieRecord(baseMovie, localMovie) {
  const merged = {
    ...(baseMovie || {}),
    ...(localMovie || {}),
  };

  merged.title = localMovie?.title || baseMovie?.title || merged.title;
  merged.synopsis = localMovie?.synopsis || baseMovie?.synopsis || merged.synopsis;
  merged.image = localMovie?.image || baseMovie?.image || merged.image;
  merged.year = localMovie?.year || baseMovie?.year || merged.year;
  merged.rank = localMovie?.rank ?? baseMovie?.rank ?? merged.rank;
  merged.streams_on = localMovie?.streams_on || baseMovie?.streams_on || [];

  return merged;
}

function hydrateMovieServices(movie) {
  const services = {};

  for (const service of movie.streams_on || []) {
    if (serviceNames.includes(service)) {
      services[service] = {
        title: movie.title,
        synopsis: movie.synopsis,
      };
    }
  }

  return {
    ...movie,
    services,
  };
}

function buildAllMovies(countryMovies, rottenMovies) {
  const rottenByRank = new Map((rottenMovies || []).map(movie => [movie.rank, movie]));
  const localByRank = new Map((countryMovies || []).map(movie => [movie.rank, movie]));

  const merged = (rottenMovies || []).map(movie => {
    const localMovie = localByRank.get(movie.rank);
    return hydrateMovieServices(mergeMovieRecord(movie, localMovie));
  });

  const extraLocalMovies = (countryMovies || [])
    .filter(movie => !rottenByRank.has(movie.rank))
    .map(movie => hydrateMovieServices(mergeMovieRecord(null, movie)));

  return [...merged, ...extraLocalMovies];
}

function renderServiceFilters() {
  const controls = serviceNames.map(service => `
    <button
      type="button"
      class="service-filter-btn service-${service} ${selectedServices.has(service) ? 'active' : ''}"
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
    const badges = (movie.services ? Object.keys(movie.services) : [])
      .filter(service => serviceNames.includes(service))
      .map(service => `<span class="badge service-badge service-${service}">${serviceLabels[service] || service}</span>`);

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
          <a href="./" class="list-title-group" aria-label="Go back to country selection" style="cursor: pointer; text-decoration: none; color: inherit;">
            <span class="list-kicker">Streaming catalogue</span>
            <h1>${country.toUpperCase()}</h1>
          </a>
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

  const titleGroup = document.querySelector('.list-title-group');
  if (titleGroup && titleGroup.tagName !== 'A') {
    titleGroup.addEventListener('click', () => {
      window.location.href = './';
    });
    titleGroup.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        window.location.href = './';
      }
    });
  }
}

const initialServices = readSelectedServicesFromUrl();
if (initialServices.length) {
  initialServices.forEach(service => selectedServices.add(service));
}

fetch('./data/metadata.json')
  .then(r => r.json())
  .then(meta => {
    normalizeServiceMetadata(meta);

    return Promise.all([
      fetch(`./data/${country}/movies.json`).then(r => (r.ok ? r.json() : [])),
      fetch('./data/rotten_300.json').then(r => (r.ok ? r.json() : [])),
    ]);
  })
  .then(([countryMovies, rottenMovies]) => {
    allMovies = buildAllMovies(countryMovies, rottenMovies);
    const filteredMovies = getFilteredMovies(allMovies);
    renderMovies(filteredMovies);
  })
  .catch(() => {
    app.innerHTML = '<div class="alert alert-danger">Could not load country data.</div>';
  });
