(() => {
  const $ = id => document.getElementById(id);
  const D = JSON.parse($('data').textContent);
  const PAIRS = D.pairs;
  const LN = { en: 'English', ha: 'Hausa', ig: 'Igbo', yo: 'Yoruba' };
  const pairName = p => { const [a, b] = p.split('->'); return `${LN[a]} → ${LN[b]}`; };
  const pairShort = p => p.replace('->', '→').toUpperCase();
  const byLabel = Object.fromEntries(D.mt.map(m => [m.label, m]));
  const natlas = byLabel.natlas, llama = byLabel.llama31;
  const hosted = D.mt.filter(m => m.run === 'hosted');
  const fmt = v => v.toFixed(1);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* headline figures */
  const best = D.mt[0];
  const lift = natlas.avg - llama.avg;
  $('f-lift').textContent = fmt(lift);
  const ha = D.asr.ha_ng;
  const figs = {
    'fig-lift': [`+${fmt(lift)}`, `chrF++ gained over its Llama 3.1 base, averaged across six directions`],
    'fig-share': [`${Math.round(natlas.avg / best.avg * 100)}%`, `of the best hosted model's translation score (${fmt(natlas.avg)} vs ${fmt(best.avg)}, ${esc(best.name)})`],
    'fig-asr': [`${fmt(ha['n-atlas'].wer)}%`, `of Hausa words wrong in speech-to-text, against ${fmt(ha['whisper-small'].wer)}% for stock Whisper`],
  };
  Object.entries(figs).forEach(([id, [b, s]]) => { $(id).innerHTML = `<div class="big num">${b}</div><p>${s}</p>`; });

  /* ticker: only numbers already on the page */
  const ey = 'en->yo';
  const tick = [
    `N-ATLaS <b>+${fmt(lift)}</b> chrF++ over Llama 3.1`,
    `Hausa speech <b>${fmt(ha['n-atlas'].wer)}%</b> WER vs ${fmt(ha['whisper-small'].wer)}%`,
    `English → Yoruba <b>${fmt(llama.scores[ey])} → ${fmt(natlas.scores[ey])}</b>`,
    `${esc(best.name)} <b>${fmt(best.avg)}</b> avg chrF++`,
    `N-ATLaS <b>${fmt(natlas.avg)}</b> avg chrF++`,
    `Igbo speech <b>${fmt(D.asr.ig_ng['n-atlas'].wer)}%</b> WER`,
    `Yoruba speech <b>${fmt(D.asr.yo_ng['n-atlas'].wer_nomarks)}%</b> WER without tone marks`,
    `100 items per language and direction`,
  ].map(t => `<span>${t}</span>`).join('');
  $('ticker').innerHTML = tick + tick;

  /* cover ghost: the six lifts, drawn large and faint */
  const G = (() => {
    const W = 600, H = 420, x = v => 20 + v / 70 * (W - 40);
    const rows = PAIRS.map((p, i) => {
      const y = 40 + i * ((H - 80) / (PAIRS.length - 1));
      const l = llama.scores[p], n = natlas.scores[p];
      const hs = hosted.map(m => m.scores[p]);
      return `<rect x="${x(Math.min(...hs))}" y="${y - 7}" width="${x(Math.max(...hs)) - x(Math.min(...hs))}" height="14" rx="5" fill="var(--band)"/>
        <line x1="${x(l)}" y1="${y}" x2="${x(n)}" y2="${y}" stroke="var(--ox)" stroke-width="2.5" opacity=".6"/>
        <circle cx="${x(l)}" cy="${y}" r="7" fill="var(--tan)"/><circle cx="${x(n)}" cy="${y}" r="9" fill="var(--ox)"/>`;
    }).join('');
    const grid = [0, 10, 20, 30, 40, 50, 60, 70].map(g => `<line x1="${x(g)}" y1="10" x2="${x(g)}" y2="${H - 10}" stroke="var(--rule)" stroke-dasharray="3 5"/>`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${grid}${rows}</svg>`;
  })();
  $('ghost').innerHTML = G;

  /* chapter index with a small chart each */
  const mini = (vals, max, color) => {
    const W = 200, H = 46, bw = W / vals.length;
    return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${vals.map((v, i) => {
      const h = Math.max(2, Math.min(v, max) / max * (H - 4));
      return `<rect x="${i * bw + 3}" y="${H - h}" width="${bw - 6}" height="${h}" rx="2" fill="${color(i)}"/>`;
    }).join('')}</svg>`;
  };
  const asrLangs = ['ha_ng', 'ig_ng', 'yo_ng'];
  const asrPairs = asrLangs.flatMap(l => [D.asr[l]['n-atlas'].wer, D.asr[l]['whisper-small'] ? D.asr[l]['whisper-small'].wer : 0]);
  const idx = [
    ['#mt', 'The Nigerian fine-tune works, but hosted models still lead', mini(PAIRS.flatMap(p => [llama.scores[p], natlas.scores[p]]), 70, i => i % 2 ? 'var(--ox)' : 'var(--tan)'), `+${fmt(lift)}`, 'chrF++ lift'],
    ['#asr', 'N-ATLaS hears Nigerian languages that stock Whisper can’t', mini(asrPairs, 120, i => i % 2 ? 'var(--band)' : 'var(--ox)'), `${fmt(ha['n-atlas'].wer)}%`, 'Hausa WER'],
    ['#ex', 'See what the scores mean', mini(D.mt.map(m => m.avg), 60, i => D.mt[i].label === 'natlas' ? 'var(--ox)' : 'var(--band)'), `${D.mt.length}`, 'models side by side'],
    ['#find', 'Findings', '', '7', 'findings'],
  ];
  $('index').innerHTML = idx.map(([h, t, m, b, s]) => `<a href="${h}"><h3>${t}</h3><span></span><div class="mini">${m}</div><div class="foot"><b class="num">${b}</b><span class="tag">${s}</span></div></a>`).join('');

  /* translation chart */
  const MAX = 70, pctN = v => Math.min(v, MAX) / MAX * 100, pct = v => `${pctN(v)}%`;
  let mtKey = 'scores';
  const tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true;
  $('mt-chart').appendChild(tip);

  function drawMT() {
    $('mt-rows').innerHTML = PAIRS.map((p, i) => {
      const hs = hosted.map(m => m[mtKey][p]);
      const lo = Math.min(...hs), hi = Math.max(...hs);
      const l = llama[mtKey][p], n = natlas[mtKey][p];
      const grid = [10, 20, 30, 40, 50, 60].map(g => `<div class="grid-line" style="left:${pct(g)}"></div>`).join('');
      const ticks = hs.map(v => `<div class="tick" style="left:${pct(v)}"></div>`).join('');
      const labels = i === 0 ? `<div class="direct" style="left:${pct(l)};color:var(--tan)">Llama</div>
        <div class="direct" style="left:${pct(n)};color:var(--ox)">N-ATLaS</div>
        <div class="direct" style="left:calc(${pct(hi)} + 10px);top:16px;color:var(--band-ink);transform:translateY(-50%)">Hosted</div>` : '';
      return `<div class="row" tabindex="0" data-pair="${p}" aria-label="${pairName(p)}: Llama ${fmt(l)}, N-ATLaS ${fmt(n)}, hosted ${fmt(lo)} to ${fmt(hi)}">
        <div class="dir">${pairShort(p)}<small>${pairName(p)}</small></div>
        <div class="track">${grid}
          <div class="band" style="left:${pct(lo)};width:calc(${pct(hi)} - ${pct(lo)})"></div>${ticks}
          <div class="lift" style="left:${pct(l)};width:calc(${pct(n)} - ${pct(l)})"></div>
          <div class="dot llama" style="left:${pct(l)}"></div>
          <div class="dot natlas" style="left:${pct(n)}" data-from="${pctN(l) - pctN(n)}"></div>${labels}
        </div></div>`;
    }).join('');
    setFrom();
    $('mt-scale').innerHTML = [0, 10, 20, 30, 40, 50, 60, 70].map(g => `<span style="left:${pct(g)}">${g}</span>`).join('');
    $('mt-strip').innerHTML = PAIRS.map(p => `<span>${pairShort(p)} <b>+${fmt(natlas[mtKey][p] - llama[mtKey][p])}</b></span>`).join('');
    $('mt-rows').querySelectorAll('.row').forEach(r => {
      const show = () => {
        const p = r.dataset.pair;
        const list = [...D.mt].sort((a, b) => b[mtKey][p] - a[mtKey][p]);
        tip.innerHTML = `<h4>${pairName(p)}</h4><table>${list.map(m => `<tr class="${m.label === 'natlas' ? 'hl' : ''}"><td>${esc(m.name)}</td><td>${fmt(m[mtKey][p])}</td></tr>`).join('')}</table>`;
        tip.hidden = false;
        const c = $('mt-chart').getBoundingClientRect(), rr = r.getBoundingClientRect();
        const below = rr.bottom - c.top + 6;
        tip.style.top = (below + tip.offsetHeight > c.height ? rr.top - c.top - tip.offsetHeight - 6 : below) + 'px';
        tip.style.left = Math.max(10, Math.min(c.width - tip.offsetWidth - 10, rr.left - c.left + 110)) + 'px';
      };
      const hide = () => { tip.hidden = true; };
      r.addEventListener('mouseenter', show); r.addEventListener('focus', show);
      r.addEventListener('mouseleave', hide); r.addEventListener('blur', hide);
      /* touch: tap a row to show its scores, tap again to hide */
      r.addEventListener('click', () => { if (tip.hidden || tip.dataset.pair !== r.dataset.pair) { show(); tip.dataset.pair = r.dataset.pair; } else { hide(); tip.dataset.pair = ''; } });
    });
    $('mt-table').innerHTML =
      `<tr><th>Model</th><th>Runs</th>${PAIRS.map(p => `<th>${pairShort(p)}</th>`).join('')}<th>Avg</th></tr>` +
      D.mt.map(m => {
        const v = PAIRS.map(p => m[mtKey][p]);
        return `<tr class="${m.label === 'natlas' ? 'hl' : ''}"><td>${esc(m.name)}</td><td>${esc(m.run)}</td>${v.map(x => `<td>${fmt(x)}</td>`).join('')}<td>${fmt(v.reduce((a, b) => a + b, 0) / v.length)}</td></tr>`;
      }).join('');
  }
  /* start offset for the travel-out moment, in px of the track */
  function setFrom() {
    $('mt-rows').querySelectorAll('.dot.natlas').forEach(d => {
      const w = d.parentElement.getBoundingClientRect().width;
      d.style.setProperty('--from', `${+d.dataset.from / 100 * w}px`);
    });
  }
  addEventListener('resize', setFrom);

  /* ASR chart */
  let asrKey = 'wer';
  const AMAX = 120, apct = v => `${Math.min(v, AMAX) / AMAX * 100}%`;
  function drawASR() {
    const langs = [['ha_ng', 'Hausa'], ['ig_ng', 'Igbo'], ['yo_ng', 'Yoruba']];
    $('asr-bars').innerHTML = langs.map(([code, name], i) => {
      const a = D.asr[code], n = a['n-atlas'][asrKey], w = a['whisper-small'] ? a['whisper-small'][asrKey] : null;
      const val = (v, cls) => v / AMAX > .72
        ? `<div class="bar-val inside ${cls}" style="right:calc(100% - ${apct(v)})">${fmt(v)}%</div>`
        : `<div class="bar-val" style="left:${apct(v)}">${fmt(v)}%</div>`;
      const nat = `<div class="bar-row"><div class="bar natlas" style="width:${apct(n)}"></div>${val(n, 'on-ox')}</div>`;
      const wh = w == null
        ? `<div class="bar-row"><div class="bar-val none" style="left:0">Stock Whisper has no Igbo</div></div>`
        : `<div class="bar-row"><div class="bar whisper" style="width:${apct(w)}"></div>${val(w, '')}</div>`;
      const cap = i === 0 ? `<div class="cap" style="left:${apct(100)}"><span class="cap-label">100%: as many errors as words</span></div>` : `<div class="cap" style="left:${apct(100)}"></div>`;
      return `<div class="lang" style="${i === 0 ? 'margin-top:20px' : ''}"><div class="dir">${name}</div><div class="bars">${cap}${nat}${wh}</div></div>`;
    }).join('');
  }

  /* examples */
  let exPair = 'en->ha', exIdx = 0;
  function drawEx(focusSel) {
    $('ex-dirs').innerHTML = PAIRS.map(p => `<button type="button" aria-pressed="${p === exPair}" data-p="${p}" aria-label="${pairName(p)}">${pairShort(p)}</button>`).join('');
    const n = natlas.examples[exPair].length;
    $('ex-nums').innerHTML = Array.from({ length: n }, (_, i) => `<button type="button" aria-pressed="${i === exIdx}" data-i="${i}">Example ${i + 1}</button>`).join('');
    const e0 = natlas.examples[exPair][exIdx];
    const [src, tgt] = exPair.split('->');
    $('ex-card').innerHTML =
      `<div class="ex-head"><div class="tag">${LN[src]} source</div><div class="ex-src" lang="${src}">${esc(e0.src)}</div>
        <div class="tag">Human ${LN[tgt]} reference</div><div class="ex-ref" lang="${tgt}">${esc(e0.ref)}</div></div>
       <div class="ex-list">${D.mt.map(m => {
         const h = m.examples[exPair][exIdx].hyp;
         return `<div class="ex-item ${m.label === 'natlas' ? 'hl' : ''}">
          <div class="ex-name">${esc(m.name)}<small>chrF++ ${fmt(m.scores[exPair])} on this direction</small></div>
          <div class="ex-out${h ? '' : ' empty'}" lang="${tgt}">${esc(h || '(no output)')}</div></div>`;
       }).join('')}</div>`;
    document.querySelectorAll('#ex-dirs button').forEach(b => b.onclick = () => { exPair = b.dataset.p; exIdx = 0; drawEx(`#ex-dirs [data-p="${exPair}"]`); });
    document.querySelectorAll('#ex-nums button').forEach(b => b.onclick = () => { exIdx = +b.dataset.i; drawEx(`#ex-nums [data-i="${exIdx}"]`); });
    if (focusSel) document.querySelector(focusSel)?.focus();
  }

  /* toggles */
  function toggle(onId, offId, fn) {
    $(onId).onclick = () => fn(true);
    $(offId).onclick = () => fn(false);
  }
  toggle('mt-marks', 'mt-nomarks', marks => {
    mtKey = marks ? 'scores' : 'scores_nomarks';
    $('mt-marks').setAttribute('aria-pressed', marks);
    $('mt-nomarks').setAttribute('aria-pressed', !marks);
    drawMT();
  });
  toggle('asr-marks', 'asr-nomarks', marks => {
    asrKey = marks ? 'wer' : 'wer_nomarks';
    $('asr-marks').setAttribute('aria-pressed', marks);
    $('asr-nomarks').setAttribute('aria-pressed', !marks);
    drawASR();
  });

  drawMT(); drawASR(); drawEx();

  /* one authored moment: the lift plays when the chart scrolls in; figures rise once */
  const chart = $('mt-chart');
  if (reduce || !('IntersectionObserver' in window)) {
    chart.classList.remove('pending');
    document.querySelectorAll('.rise').forEach(e => e.classList.add('in'));
  } else {
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      if (e.target === chart) requestAnimationFrame(() => chart.classList.remove('pending'));
      else e.target.classList.add('in');
      io.unobserve(e.target);
    }), { threshold: .35 });
    io.observe(chart);
    document.querySelectorAll('.rise').forEach(e => io.observe(e));
  }
})();
