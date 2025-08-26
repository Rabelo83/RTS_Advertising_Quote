/* RTS Quote — client logic (clean, validated, empty-by-default) */

/* ---------- DOM ---------- */
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

/* ---------- state ---------- */
let items = []; // [{type_display, variant, months, qty}]

/* ---------- helpers ---------- */
function placeholderOptionHTML() {
  return '<option value="" disabled selected>Select…</option>';
}

function ensurePlaceholder(selectEl) {
  if (!selectEl.querySelector('option[value=""]')) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.disabled = true;
    opt.selected = true;
    opt.textContent = 'Select…';
    selectEl.insertBefore(opt, selectEl.firstChild);
  }
  selectEl.value = '';
}

function setDisabled(el, isDisabled) {
  el.disabled = !!isDisabled;
}

function notify(text, kind = 'info') {
  // kind: info | ok | warn | err
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

/* ---------- population ---------- */
function populateVariants() {
  variantSel.innerHTML = placeholderOptionHTML();
  monthsSel.innerHTML  = placeholderOptionHTML();
  setDisabled(monthsSel, true);

  const type = typeSel.value;
  if (type === 'Exterior') {
    (window.EXTERIOR_PRODUCTS || []).forEach(p => {
      const opt = document.createElement('option');
      opt.value = p; opt.textContent = p;
      variantSel.appendChild(opt);
    });
  } else if (type === 'Interior') {
    (window.INTERIOR_SIZES || []).forEach(s => {
      const opt = document.createElement('option');
      opt.value = s; opt.textContent = s;
      variantSel.appendChild(opt);
    });
  }
}

function populateMonths() {
  monthsSel.innerHTML = placeholderOptionHTML();
  const type    = typeSel.value;
  const variant = variantSel.value;

  if (!type || !variant) return;

  if (type === 'Exterior') {
    const allowed = (window.ALLOWED_MONTHS || {})[variant] || [];
    allowed.forEach(m => {
      const opt = document.createElement('option');
      opt.value = String(m); opt.textContent = String(m);
      monthsSel.appendChild(opt);
    });
  } else {
    // interior quick picks
    [1, 2, 3, 4, 6, 8, 12].forEach(m => {
      const opt = document.createElement('option');
      opt.value = String(m); opt.textContent = String(m);
      monthsSel.appendChild(opt);
    });
  }
}

/* ---------- validation ---------- */
function canAddLine() {
  return Boolean(
    typeSel.value &&
    variantSel.value &&
    monthsSel.value &&
    qtyInput.value &&
    Number(qtyInput.value) > 0
  );
}

function validateAddLine() {
  if (!typeSel.value)   return { ok: false, reason: 'Pick a Type first.' };
  if (!variantSel.value)return { ok: false, reason: 'Pick a Variant.' };
  if (!monthsSel.value) return { ok: false, reason: 'Pick Months.' };
  const qty = Number(qtyInput.value);
  if (!qty || qty < 1)  return { ok: false, reason: 'Quantity must be ≥ 1.' };
  return { ok: true };
}

/* ---------- render ---------- */
function renderLinesTable(data) {
  // data = { items:[], subtotal_base, total, saved, flags, ... }
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

  tableWrap.style.display = '';
}

/* ---------- events ---------- */
document.addEventListener('DOMContentLoaded', () => {
  // start with everything blank/disabled
  ensurePlaceholder(variantSel);
  ensurePlaceholder(monthsSel);
  setDisabled(variantSel, true);
  setDisabled(monthsSel, true);
  setDisabled(addBtn, true);
  notify('Pick Type → Variant → Months → Qty, then Add line.', 'info');
});

typeSel.addEventListener('change', () => {
  setDisabled(variantSel, false);
  populateVariants();
  ensurePlaceholder(variantSel);
  ensurePlaceholder(monthsSel);
  setDisabled(monthsSel, true);
  setDisabled(addBtn, true);
});

variantSel.addEventListener('change', () => {
  setDisabled(monthsSel, false);
  populateMonths();
  ensurePlaceholder(monthsSel);
  setDisabled(addBtn, !canAddLine());
});

[monthsSel, qtyInput].forEach(el => {
  el.addEventListener('input', () => {
    setDisabled(addBtn, !canAddLine());
  });
  el.addEventListener('change', () => {
    setDisabled(addBtn, !canAddLine());
  });
});

addBtn.addEventListener('click', () => {
  const v = validateAddLine();
  if (!v.ok) {
    notify(v.reason, 'warn');
    return;
  }
  const type_display = typeSel.value;
  const variant = variantSel.value;
  const months  = parseInt(monthsSel.value, 10);
  const qty     = parseInt(qtyInput.value, 10);

  items.push({ type_display, variant, months, qty });

  notify(`Added: ${type_display} / ${variant} / ${months} / qty ${qty} (Total lines: ${items.length})`, 'ok');

  // reset only qty to avoid extra clicks; leave the selectors as chosen
  qtyInput.value = '';
  setDisabled(addBtn, true);
});

clearBtn.addEventListener('click', () => {
  items = [];
  tbody.innerHTML = '';
  tableWrap.style.display = 'none';
  notify('Cleared all lines. Add new items and click Calculate.', 'warn');
});

calcBtn.addEventListener('click', async () => {
  if (items.length === 0) {
    notify('Add at least one line before calculating.', 'warn');
    return;
  }

  const discountSel = document.getElementById('discount');
  const upfrontSel  = document.getElementById('upfront');

  const payload = {
    items,
    discount_choice: discountSel.value,              // "None" | "Agency 10%" | "PSA 10%"
    upfront_selected: (upfrontSel.value === 'Yes'),  // boolean
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
