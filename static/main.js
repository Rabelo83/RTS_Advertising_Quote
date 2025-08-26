const typeSel = document.getElementById('type');
const variantSel = document.getElementById('variant');
const monthsSel = document.getElementById('months');
const qtyInput = document.getElementById('qty');
const addBtn = document.getElementById('add');

const discountSel = document.getElementById('discount');
const upfrontSel = document.getElementById('upfront');

const calcBtn = document.getElementById('calc');
const msg = document.getElementById('msg');

const table = document.getElementById('lines');
const tbody = table.querySelector('tbody');
const subtotalCell = document.getElementById('subtotal');
const totalCell = document.getElementById('total');
const savedCell = document.getElementById('saved');

// in-memory cart
const items = [];

function refreshVariantAndMonths() {
  variantSel.innerHTML = '';
  monthsSel.innerHTML = '';
  if (typeSel.value === 'Exterior') {
    window.EXTERIOR_PRODUCTS.forEach(p => {
      const opt = document.createElement('option');
      opt.textContent = p; opt.value = p;
      variantSel.appendChild(opt);
    });
    const allowed = window.ALLOWED_MONTHS[variantSel.value];
    allowed.forEach(m => {
      const opt = document.createElement('option');
      opt.textContent = m; opt.value = m;
      monthsSel.appendChild(opt);
    });
  } else {
    window.INTERIOR_SIZES.forEach(s => {
      const opt = document.createElement('option');
      opt.textContent = s; opt.value = s;
      variantSel.appendChild(opt);
    });
    // any positive months allowed for interior; offer 1–12 quick picks
    [1,2,3,4,6,8,12].forEach(m => {
      const opt = document.createElement('option');
      opt.textContent = m; opt.value = m;
      monthsSel.appendChild(opt);
    });
  }
}

typeSel.addEventListener('change', refreshVariantAndMonths);
variantSel.addEventListener('change', refreshVariantAndMonths);
refreshVariantAndMonths();

addBtn.addEventListener('click', () => {
  const type_display = typeSel.value;
  const variant = variantSel.value;
  const months = parseInt(monthsSel.value, 10);
  const qty = parseInt(qtyInput.value, 10) || 1;

  items.push({ type_display, variant, months, qty });
  msg.textContent = `Added: ${type_display} / ${variant} / ${months} / qty ${qty} (total items: ${items.length})`;
});

calcBtn.addEventListener('click', async () => {
  if (items.length === 0) {
    msg.textContent = 'Add at least one line.';
    return;
  }
  const payload = {
    items,
    discount_choice: discountSel.value,
    upfront_selected: (upfrontSel.value === 'Yes')
  };
  const res = await fetch('/quote', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await res.json();

  // fill table
  tbody.innerHTML = '';
  data.items.forEach(it => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${it.type_display}</td>
      <td>${it.product}</td>
      <td>${it.code}</td>
      <td>${it.months}</td>
      <td>${it.qty}</td>
      <td class="right">$${it.unit_price.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</td>
      <td class="right">$${it.line_total.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</td>
    `;
    tbody.appendChild(tr);
  });
  subtotalCell.textContent = `$${data.subtotal_base.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  totalCell.textContent    = `$${data.total.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  savedCell.textContent    = `$${data.saved.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;

  table.style.display = '';
  msg.textContent = `Applied: ${data.flags}`;
});
