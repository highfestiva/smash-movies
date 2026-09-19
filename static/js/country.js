const app = document.getElementById('app');
const country = new URLSearchParams(window.location.search).get('country') || 'se';

function renderMovies(items) {
  const cards = items.map(movie => {
    const badges = [];
    if (movie.services && movie.services.netflix) badges.push('<span class="badge bg-danger">Netflix</span>');
    if (movie.services && movie.services.hbo) badges.push('<span class="badge bg-primary">HBO</span>');
    if (movie.services && movie.services.prime) badges.push('<span class="badge bg-warning text-dark">Prime</span>');

    return `
      <div class="col-md-4 mb-4">
        <div class="card movie-card h-100 shadow-sm">
          ${movie.image ? `
            <div class="poster-shell" style="--poster-bg: url('${movie.image}');">
              <img class="poster-image" src="${movie.image}" alt="${movie.title}">
            </div>
          ` : '<div class="poster-shell"></div>'}
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">${movie.rank}. ${movie.title} (${movie.year || ''})</h5>
            <p class="card-text text-muted flex-grow-1">${movie.synopsis || 'No synopsis available.'}</p>
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
    countryHeader.textContent = country.toUpperCase();
  }

  app.innerHTML = `
    <div class="row">${cards}</div>
  `;
}

fetch('/data/rotten_300.json')
  .then(r => r.json())
  .then(rottenMovies => {
    const movies = rottenMovies.map(movie => ({ ...movie, services: {} }));

    const serviceFiles = ['netflix', 'hbo', 'prime'];
    const promises = serviceFiles.map(service =>
      fetch(`/data/${country}/${service}.json`)
        .then(res => (res.ok ? res.json() : []))
        .then(serviceMovies => {
          serviceMovies.forEach(serviceMovie => {
            const match = movies.find(m => m.rank === serviceMovie.rank);
            if (match) match.services[service] = serviceMovie;
          });
        })
        .catch(() => {})
    );

    Promise.all(promises).then(() => renderMovies(movies));
  })
  .catch(() => {
    app.innerHTML = '<div class="alert alert-danger">Could not load country data.</div>';
  });
