/* RTS Quote — client logic with "Added lines" preview + exterior qty hint */

const typeSel    = document.getElementById('type');
const variantSel = document.getElementById('variant');
const monthsSel  = document.getElementById('months');
const qtyInput   = document.getElementById('qty');

const addBtn   = document.getElementById('add');
const calcBtn  = document.getElementById('calc');
const clearBtn = document.getElementById('clear');

const msg          = document.getElementById('msg');
const tableWrap    = document.getElementById('tableWrap');
const table        = document.getElementById('lines');
const tbody        = table.querySelector('tbody');
const subtotalCell = document.getElementById('subtotal');
const totalCell    = document.getElementById('total');
const savedCell    = document.getElementById('saved');

const upfrontSel   = document.getElementById('upfront');
const upfrontLabel = document.querySelector('label[for="upfront"]');

let items = []; // [{type_display, variant, months, qty}]

// --- helpers ---
function placeholderOptionHTML() { return '<option value="" disabled selected>Select…</option>'; }
function ensurePlaceholder(selectEl) {
  if (!selectEl.querySelector('option[value=""]')) {
    const opt = document.createElement('option');
    opt.value = ''; opt.disabled = true; opt.selected = true; opt.textContent = 'Select…';
    selectEl.insertBefore(opt, selectEl.firstChild);
  }
  selectEl.value = '';
}
function setDisabled(el, isDisabled) { el.disabled = !!isDisabled; }
function notify(text, kind = 'info') {
  msg.textContent = text;
  msg.style.background = kind === 'ok' ? '#ecfdf5'
    : kind === 'warn' ? '#fff7ed'
    : kind === 'err' ? '#fee2e2'
    : '#eef2ff';
  msg.style.color = kind === 'ok' ? '#065f46'
    : kind === 'warn' ? '#b45309'
    : kind === 'err' ? '#991b1b'
    : '#3730a3';
}

// --- populate ---
function populateVariants() {
  variantSel.innerHTML = placeholderOptionHTML();
  monthsSel.innerHTML  = placeholderOptionHTML();
  setDisabled(monthsSel, true);
  const type = typeSel.value;
  if (type === 'Exterior') {
    (window.EXTERIOR_PRODUCTS || []).forEach(p => {
      const opt = document.createElement('option'); opt.value = p; opt.textContent = p;
      variantSel.appendChild(opt);
    });
  } else if (type === 'Interior') {
    (window.INTERIOR_SIZES || []).forEach(s => {
      const opt = document.createElement('option'); opt.value = s; opt.textContent = s;
      variantSel.appendChild(opt);
    });
  }
}

function populateMonths() {
  monthsSel.innerHTML = placeholderOptionHTML();
  const type = typeSel.value, variant = variantSel.value;
  if (!type || !variant) return;
  if (type === 'Exterior') {
    (window.ALLOWED_MONTHS[variant] || []).forEach(m => {
      const opt = document.createElement('option'); opt.value = String(m); opt.textContent = String(m);
      monthsSel.appendChild(opt);
    });
  } else {
    [1,2,3,4,6,8,12].forEach(m => {
      const opt = document.createElement('option'); opt.value = String(m); opt.textContent = String(m);
      monthsSel.appendChild(opt);
    });
  }
}

// --- validation ---
function canAddLine() {
  return Boolean(typeSel.value && variantSel.value && monthsSel.value && qtyInput.value && Number(qtyInput.value) > 0);
}
function validateAddLine() {
  if (!typeSel.value)   return { ok: false, reason: 'Pick a Type first.' };
  if (!variantSel.value)return { ok: false, reason: 'Pick a Variant.' };
  if (!monthsSel.value) return { ok: false, reason: 'Pick Months.' };
  const qty = Number(qtyInput.value);
  if (!qty || qty < 1)  return { ok: false, reason: 'Quantity must be ≥ 1.' };
  return { ok: true };
}

// --- "Added lines" preview (mini cart) ---
let previewEl; // container we inject once

function ensurePreviewContainer() {
  if (previewEl) return previewEl;
  const cards = document.querySelectorAll('.card');
  const after = cards[0];
  previewEl = document.createElement('div');
  previewEl.className = 'card';
  previewEl.style.marginTop = '16px';
  previewEl.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <strong>Added lines</strong>
      <span id="preview-count" class="pill">0 items</span>
    </div>
    <div id="preview-body" class="stack"></div>
    <div id="preview-footer" style="margin-top:10px;font-size:13px;color:#374151;background:#f9fafb;border:1px solid #e5e7eb;border-radius:10px;padding:8px 10px;">
      Exterior units: <strong id="ext-count">0</strong> · 6+ discount: <strong id="ext-sixplus">Not yet</strong>
    </div>
  `;
  after.parentNode.insertBefore(previewEl, after.nextSibling);
  return previewEl;
}

function totalExteriorQty() {
  return items
    .filter(it => it.type_display === 'Exterior')
    .reduce((sum, it) => sum + Number(it.qty || 0), 0);
}

function renderPreview() {
  ensurePreviewContainer();
  const body  = previewEl.querySelector('#preview-body');
  const count = previewEl.querySelector('#preview-count');
  const extC  = previewEl.querySelector('#ext-count');
  const extS  = previewEl.querySelector('#ext-sixplus');

  if (items.length === 0) {
    body.innerHTML = `<div class="hint">No lines yet. Add a line above.</div>`;
    count.textContent = '0 items';
    extC.textContent = '0';
    extS.textContent = 'Not yet';
    extS.style.color = '#b45309'; // amber
    return;
  }

  const rows = items.map((it, idx) => `
    <tr>
      <td>${it.type_display}</td>
      <td>${it.variant}</td>
      <td class="right">${it.months}</td>
      <td class="right">${it.qty}</td>
      <td class="right">
        <button class="btn" data-remove="${idx}" style="padding:6px 10px">Remove</button>
      </td>
    </tr>
  `).join('');

  body.innerHTML = `
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr>
          <th>Type</th>
          <th>Variant</th>
          <th class="right">Months</th>
          <th class="right">Qty</th>
          <th class="right">Action</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  count.textContent = `${items.length} ${items.length === 1 ? 'item' : 'items'}`;

  body.querySelectorAll('button[data-remove]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = Number(btn.getAttribute('data-remove'));
      items.splice(idx, 1);
      renderPreview();
      notify('Removed line.', 'warn');
    });
  });

  const extQty = totalExteriorQty();
  extC.textContent = String(extQty);
  const eligible = extQty >= 6;
  extS.textContent = eligible ? 'Eligible' : 'Not yet';
  extS.style.color = eligible ? '#065f46' : '#b45309'; // green or amber
}

// --- result rendering ---
function renderLinesTable(data) {
  tbody.innerHTML = '';
  (data.items || []).forEach(it => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${it.type_display}</td>
      <td>${it.product}</td>
      <td>${it.code}</td>
      <td class="right">${it.months}</td>
      <td class="right">${it.qty}</td>
      <td class="right">$${Number(it.unit_price).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</td>
      <td class="right">$${Number(it.line_total).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</td>
    `;
    tbody.appendChild(tr);
  });
  subtotalCell.textContent = `$${Number(data.subtotal_base).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  totalCell.textContent    = `$${Number(data.total).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  savedCell.textContent    = `$${Number(data.saved).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  tableWrap.style.display  = '';
}

// --- events ---
document.addEventListener('DOMContentLoaded', () => {
  ensurePlaceholder(variantSel);
  ensurePlaceholder(monthsSel);
  setDisabled(variantSel, true);
  setDisabled(monthsSel, true);
  setDisabled(addBtn, true);

  // initial: hide Upfront until Exterior is chosen
  upfrontSel.value = 'No';
  if (upfrontSel.parentElement) upfrontSel.parentElement.style.display = 'none';
  if (upfrontLabel) upfrontLabel.style.display = 'none';

  notify('Pick Type → Variant → Months → Qty, then Add line.', 'info');
  ensurePreviewContainer();
  renderPreview();
});

// Type change — repopulate, reset, and hide/show Upfront
typeSel.addEventListener('change', () => {
  setDisabled(variantSel, false);
  populateVariants();
  ensurePlaceholder(variantSel);
  ensurePlaceholder(monthsSel);
  setDisabled(monthsSel, true);
  setDisabled(addBtn, true);

  const isInterior = (typeSel.value === 'Interior');
  if (isInterior) {
    upfrontSel.value = 'No'; // reset
    if (upfrontSel.parentElement) upfrontSel.parentElement.style.display = 'none';
    if (upfrontLabel) upfrontLabel.style.display = 'none';
  } else {
    if (upfrontSel.parentElement) upfrontSel.parentElement.style.display = '';
    if (upfrontLabel) upfrontLabel.style.display = '';
  }
});

// Variant change — enable Months
variantSel.addEventListener('change', () => {
  setDisabled(monthsSel, false);
  populateMonths();
  ensurePlaceholder(monthsSel);
  setDisabled(addBtn, !canAddLine());
});

// Months/Qty change — gate Add button
[monthsSel, qtyInput].forEach(el => {
  el.addEventListener('input', () => setDisabled(addBtn, !canAddLine()));
  el.addEventListener('change', () => setDisabled(addBtn, !canAddLine()));
});

// Add line
addBtn.addEventListener('click', () => {
  const v = validateAddLine();
  if (!v.ok) { notify(v.reason, 'warn'); return; }
  const type_display = typeSel.value;
  const variant = variantSel.value;
  const months  = parseInt(monthsSel.value, 10);
  const qty     = parseInt(qtyInput.value, 10);
  items.push({ type_display, variant, months, qty });
  renderPreview();
  notify(`Added: ${type_display} / ${variant} / ${months} / qty ${qty}`, 'ok');
  qtyInput.value = '';
  setDisabled(addBtn, true);
});

// Clear lines
clearBtn.addEventListener('click', () => {
  items = [];
  tbody.innerHTML = '';
  tableWrap.style.display = 'none';
  renderPreview();
  notify('Cleared all lines. Add new items and click Calculate.', 'warn');
});

// Calculate
calcBtn.addEventListener('click', async () => {
  if (items.length === 0) {
    notify('Add at least one line before calculating.', 'warn');
    return;
  }
  const discountSel = document.getElementById('discount');

  const payload = {
    items,
    discount_choice: discountSel.value,
    upfront_selected: (upfrontSel.value === 'Yes'),
  };

  try {
    notify('Calculating…');
    const res = await fetch('/quote', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Server error ${res.status}: ${text || 'no details'}`);
    }
    const data = await res.json();
    renderLinesTable(data);
    notify(`Applied: ${data.flags || 'None'}`, 'ok');
  } catch (err) {
    console.error(err);
    notify('Could not calculate quote. Please try again.', 'err');
  }
});
