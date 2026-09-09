const tabs = document.querySelectorAll('.tab');
const forms = document.querySelectorAll('.upload-form');
const feedback = document.querySelector('#feedback');
const results = document.querySelector('#results');

tabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabs.forEach((item) => {
      const active = item === tab;
      item.classList.toggle('active', active);
      item.setAttribute('aria-selected', String(active));
    });
    forms.forEach((form) => {
      const active = form.id === tab.dataset.target;
      form.classList.toggle('active', active);
      form.hidden = !active;
    });
    feedback.textContent = '';
    feedback.className = 'feedback';
    results.innerHTML = '';
  });
});

document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => {
    const zone = input.closest('.dropzone');
    const label = zone.querySelector('.file-label');
    if (input.files.length) {
      label.textContent = input.files[0].name;
      zone.classList.add('has-file');
    } else {
      label.textContent = 'JPG, PNG ou PDF';
      zone.classList.remove('has-file');
    }
  });
});

function safe(value, fallback = 'Não identificado') {
  return value === null || value === undefined || value === '' ? fallback : String(value);
}

function cpfFormatado(cpf) {
  const value = safe(cpf, '');
  return /^\d{11}$/.test(value)
    ? value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
    : safe(cpf);
}

function statusCpf(status) {
  return ({ valid: 'Válido', corrected: 'Corrigido pelo OCR', invalid: 'Inválido', ambiguous: 'Ambíguo', not_found: 'Não identificado' })[status] || safe(status);
}

function detail(label, value) {
  return `<div class="detail"><dt>${label}</dt><dd>${safe(value)}</dd></div>`;
}

function alertas(evidences = []) {
  if (!evidences.length) return '<p class="file-label">Nenhum alerta encontrado.</p>';
  return `<ul class="alert-list">${evidences.map((item) => `<li class="alert-item ${item.severity === 'low' ? 'low' : ''}">${safe(item.message)}</li>`).join('')}</ul>`;
}

function documentoCards(analise, titulo = 'Documento') {
  const ocr = analise.ocr || {};
  const meta = analise.metadados || {};
  const fields = ocr.data?.fields || {};
  const metaData = meta.data || {};
  const scoreClass = (ocr.score || 0) > 0 ? 'warning' : '';
  return `
    <article class="result-card">
      <div class="card-heading"><h3>${titulo} · Dados extraídos</h3><span class="score ${scoreClass}">${safe(ocr.data?.confidence, '0')}% confiança</span></div>
      <dl class="details">
        ${detail('Nome', fields.nome)}
        ${detail('CPF', cpfFormatado(fields.cpf))}
        ${detail('Situação do CPF', statusCpf(fields.cpf_status))}
        ${detail('Datas', fields.datas?.join(', '))}
        ${detail('Pontuação de alertas', ocr.score ?? 0)}
      </dl>
    </article>
    <article class="result-card">
      <div class="card-heading"><h3>${titulo} · Metadados</h3><span class="score">${safe(metaData.type)}</span></div>
      <dl class="details">
        ${detail('Formato', metaData.format || metaData.type)}
        ${detail('Dimensões', metaData.width ? `${metaData.width} × ${metaData.height} px` : null)}
        ${detail('Páginas', metaData.pages)}
        ${detail('Software', metaData.software || metaData.creator)}
        ${detail('EXIF', metaData.exif && Object.keys(metaData.exif).length ? 'Encontrado' : 'Não encontrado')}
      </dl>
    </article>
    <article class="result-card wide">
      <div class="card-heading"><h3>Alertas de ${titulo.toLowerCase()}</h3></div>
      ${alertas([...(ocr.evidences || []), ...(meta.evidences || [])])}
    </article>`;
}

function renderSingle(data) {
  results.innerHTML = `<div class="results-grid">${documentoCards(data)}</div>`;
}

function renderPixel(pixel) {
  const global = pixel.analise_global || {};
  const classification = safe(global.classification);
  const attention = pixel.anomalia_detectada || /suspeita/i.test(classification);
  const stamp = Date.now();
  const visuals = [
    ['/results/hybrid_analysis.png', 'Análise regional combinada'],
    ['/results/xray_heatmap.png', 'Mapa ELA'],
    ['/results/continuity_map.png', 'Mapa de continuidade'],
    ['/results/continuity_heatmap.png', 'Mapa de calor dos pixels'],
  ];
  return `
    <article class="result-card wide">
      <div class="card-heading"><h2>Análise EOCR + Pixel</h2><span class="score ${attention ? 'warning' : ''}">${classification}</span></div>
      <div class="pixel-summary">
        <div class="metric"><span>Score combinado</span><strong>${safe(global.combined_score, '0')}/100</strong></div>
        <div class="metric"><span>Score de pixels</span><strong>${safe(global.pixel_score, '0')}</strong></div>
        <div class="metric"><span>Continuidade</span><strong>${safe(global.continuity_score, '0')}</strong></div>
        <div class="metric"><span>Geometria</span><strong>${safe(global.geometry_score, '0')}</strong></div>
        <div class="metric"><span>Regiões analisadas</span><strong>${safe(global.total_regions ?? pixel.total_regioes_texto, '0')}</strong></div>
        <div class="metric"><span>Regiões suspeitas</span><strong>${safe(global.suspicious_geometry_regions ?? pixel.lista_anomalias?.length, '0')}</strong></div>
      </div>
      <div class="visual-grid">
        ${visuals.map(([src, label]) => `<figure class="visual-card"><img src="${src}?v=${stamp}" alt="${label}"><figcaption>${label}</figcaption></figure>`).join('')}
      </div>
    </article>`;
}

function renderComplete(valid, pixel) {
  results.innerHTML = `${renderPixel(pixel)}<div class="results-grid">${documentoCards(valid)}</div>`;
}

function traducaoComparacao(value) {
  return ({ COMPATIVEL: 'Compatível', PARCIALMENTE_COMPATIVEL: 'Parcialmente compatível', DIVERGENTE: 'Divergente', INVALIDO: 'Inválido', AMBIGUO: 'Ambíguo', NAO_IDENTIFICADO: 'Não identificado', REQUER_REVISAO: 'Requer revisão', INCONSISTENTE: 'Inconsistente', 'SEM DADOS SUFICIENTES': 'Dados insuficientes' })[value] || safe(value);
}

function renderCompare(data) {
  const comparison = data.comparacao || {};
  const good = comparison.status === 'COMPATIVEL';
  const fields = comparison.campos || {};
  results.innerHTML = `
    <article class="result-card wide">
      <p class="eyebrow">RESULTADO DA COMPARAÇÃO</p>
      <h2 class="comparison-status ${good ? 'good' : 'attention'}">${traducaoComparacao(comparison.status)}</h2>
      <dl class="details">
        ${detail('Compatibilidade', comparison.compatibilidade === null ? null : `${comparison.compatibilidade}%`)}
        ${detail('Nome', traducaoComparacao(fields.nome))}
        ${detail('CPF', traducaoComparacao(fields.cpf))}
        ${detail('Datas', traducaoComparacao(fields.data))}
      </dl>
    </article>
    <div class="results-grid">
      ${documentoCards(data.documento1, 'Documento 1')}
      ${documentoCards(data.documento2, 'Documento 2')}
    </div>`;
}

async function enviar(form, url, renderer) {
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  feedback.className = 'feedback';
  feedback.innerHTML = '<span class="loader">Analisando o documento. Isso pode levar alguns segundos...</span>';
  results.innerHTML = '';

  try {
    const response = await fetch(url, { method: 'POST', body: new FormData(form) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.erro || 'Não foi possível concluir a análise.');
    feedback.textContent = 'Análise concluída.';
    renderer(data);
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    feedback.className = 'feedback error';
    feedback.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function enviarAnaliseCompleta(form) {
  const button = form.querySelector('button[type="submit"]');
  const arquivo = form.querySelector('#arquivo').files[0];
  const validData = new FormData();
  const pixelData = new FormData();
  validData.append('arquivo', arquivo);
  pixelData.append('imagem', arquivo);

  button.disabled = true;
  feedback.className = 'feedback';
  feedback.innerHTML = '<span class="loader">Executando OCR, metadados e análise de pixels...</span>';
  results.innerHTML = '';

  try {
    const [validResponse, pixelResponse] = await Promise.all([
      fetch('/valid/analisar', { method: 'POST', body: validData }),
      fetch('/analisar', { method: 'POST', body: pixelData }),
    ]);
    const [validResult, pixelResult] = await Promise.all([validResponse.json(), pixelResponse.json()]);
    if (!validResponse.ok) throw new Error(validResult.erro || 'Falha na análise dos dados.');
    if (!pixelResponse.ok) throw new Error(pixelResult.erro || 'Falha na análise de pixels.');
    feedback.textContent = 'Análise completa concluída.';
    renderComplete(validResult, pixelResult);
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    feedback.className = 'feedback error';
    feedback.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

document.querySelector('#single-form').addEventListener('submit', (event) => {
  event.preventDefault();
  enviarAnaliseCompleta(event.currentTarget);
});

document.querySelector('#compare-form').addEventListener('submit', (event) => {
  event.preventDefault();
  enviar(event.currentTarget, '/valid/comparar', renderCompare);
});
