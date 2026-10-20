"""website.py: the canteen website (port 8000).

Serves one page. The page's JavaScript calls the API server (server.py, port 5000)
for the menu and for placing and tracking orders.

Run:  python server.py     (terminal 1)
      python website.py    (terminal 2)
Open: http://localhost:8000
"""
from flask import Flask

app = Flask(__name__)

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Campus Bites</title>
<style>
  :root { --navy:#1f2a5a; --sky:#e8eefc; --gold:#f2b134; --ink:#1b1f33; --grey:#667085; --line:#d8def2; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:"Segoe UI", system-ui, sans-serif; background:#f5f7fd; color:var(--ink); }
  button { font:inherit; cursor:pointer; border:0; }
  .top { background:var(--navy); color:#fff; padding:22px 18px; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
  .top h1 { margin:0; font-size:1.6rem; }
  .top small { color:#c9d3f5; display:block; margin-top:4px; }
  .badge { padding:4px 12px; border-radius:99px; font-size:.78rem; font-weight:700; }
  .open { background:#d3f5df; color:#10663a; } .closed { background:#fde2d9; color:#9a3412; }
  .cartbtn { background:var(--gold); color:var(--ink); font-weight:800; padding:10px 16px; border-radius:10px; }
  .wrap { max-width:960px; margin:0 auto; padding:16px; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }
  .chip { padding:7px 13px; border-radius:8px; background:#fff; border:1px solid var(--line); color:var(--navy); font-size:.85rem; font-weight:600; }
  .chip.on { background:var(--navy); color:#fff; border-color:var(--navy); }
  .search { width:100%; padding:11px 12px; border:1px solid var(--line); border-radius:8px; font:inherit; margin:4px 0 16px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; }
  .card { background:#fff; border-radius:12px; padding:16px; border-top:4px solid var(--gold); box-shadow:0 2px 8px rgba(31,42,90,.07); display:flex; flex-direction:column; }
  .card h3 { margin:0 0 6px; color:var(--navy); }
  .card p { margin:0 0 10px; color:var(--grey); font-size:.9rem; line-height:1.45; flex:1; }
  .row { display:flex; justify-content:space-between; align-items:center; }
  .cat { background:var(--sky); color:var(--navy); padding:3px 9px; border-radius:6px; font-size:.72rem; font-weight:700; text-transform:uppercase; }
  .price { font-weight:800; font-size:1.1rem; }
  .tags { font-size:.75rem; color:var(--grey); margin:8px 0 12px; }
  .add { background:var(--navy); color:#fff; padding:10px; border-radius:8px; font-weight:700; }
  h2.sec { color:var(--navy); margin:30px 0 10px; }
  .panel { background:#fff; border-radius:12px; padding:16px; box-shadow:0 2px 8px rgba(31,42,90,.07); }
  .combo { display:flex; justify-content:space-between; gap:10px; padding:10px 0; border-bottom:1px dashed var(--line); font-size:.92rem; }
  input[type=range] { width:100%; }
  /* cart drawer */
  .drawer { position:fixed; top:0; right:0; height:100%; width:min(400px,100%); background:#fff; box-shadow:-6px 0 30px rgba(0,0,0,.18);
            transform:translateX(105%); transition:transform .25s; padding:20px; overflow:auto; z-index:20; }
  .drawer.open { transform:none; }
  .line { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid var(--line); gap:8px; }
  .qty button { width:28px; height:28px; border-radius:8px; background:var(--sky); font-weight:800; }
  .qty b { display:inline-block; min-width:26px; text-align:center; }
  textarea { width:100%; border:1px solid var(--line); border-radius:8px; padding:10px; font:inherit; margin-top:12px; }
  .total { display:flex; justify-content:space-between; font-size:1.25rem; font-weight:800; padding:14px 0; }
  .primary { width:100%; background:var(--gold); color:var(--ink); font-weight:800; padding:13px; border-radius:10px; }
  .ghost { background:var(--sky); color:var(--navy); padding:9px 14px; border-radius:8px; font-weight:700; }
  /* tracker */
  .steps { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:14px 0; }
  .step { padding:11px; text-align:center; border-radius:10px; background:#eceff8; font-size:.82rem; font-weight:700; color:var(--grey); }
  .step.on { background:#d9f0e1; color:#145a3a; }
  .toast { position:fixed; left:50%; bottom:20px; transform:translateX(-50%); background:var(--ink); color:#fff; padding:11px 18px; border-radius:10px; opacity:0; transition:opacity .2s; z-index:40; pointer-events:none; }
  .toast.show { opacity:1; }
  .empty { text-align:center; color:var(--grey); padding:26px; }
</style>
</head>
<body>
<div class="top">
  <div><h1 id="shop">Campus Bites</h1><small id="where"></small></div>
  <span id="state" class="badge closed">checking...</span>
  <button class="cartbtn" onclick="toggleCart()">Cart (<span id="count">0</span>)</button>
</div>

<div class="wrap">
  <div class="chips" id="days"></div>
  <div class="chips" id="cats"></div>
  <input class="search" id="search" placeholder="Search dishes...">
  <div class="grid" id="grid"></div>

  <h2 class="sec">Build a meal on a budget</h2>
  <div class="panel">
    <div class="row"><b id="budgetText">₹100</b><button class="ghost" onclick="findCombos()">Find combos</button></div>
    <input type="range" id="budget" min="40" max="250" step="5" value="100">
    <div id="combos"></div>
  </div>

  <h2 class="sec">Track your order</h2>
  <div class="panel" id="tracker"><div class="empty">No active order yet.</div></div>
</div>

<div class="drawer" id="drawer">
  <div class="row"><h2 style="margin:0">Your cart</h2><button class="ghost" onclick="toggleCart()">Close</button></div>
  <div id="lines"></div>
  <textarea id="note" rows="2" placeholder="Note for the kitchen (optional)"></textarea>
  <div class="total"><span>Total</span><span id="total">₹0</span></div>
  <button class="primary" onclick="placeOrder()">Place order</button>
</div>
<div class="toast" id="toast"></div>

<script>
const API = "http://localhost:5000/api";
const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
const CATS = ["All","Breakfast","Lunch","Snacks","Beverages","Dessert"];
let day = "", menu = [], cat = "All", cart = {}, timer = null;

const $ = id => document.getElementById(id);
const rupee = n => "₹" + n;
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

function toast(msg) {
  $("toast").textContent = msg; $("toast").classList.add("show");
  setTimeout(() => $("toast").classList.remove("show"), 2200);
}

async function api(path, options) {
  let res;
  try { res = await fetch(API + path, options); }
  catch (e) { throw new Error("Cannot reach the canteen server. Is server.py running?"); }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

/* ---------- menu ---------- */
async function loadStatus() {
  try {
    const s = await api("/status");
    $("shop").textContent = s.name;
    $("where").textContent = s.location + " · " + s.opening_hour + ":00 to " + s.closing_hour + ":00";
    $("state").textContent = s.open ? "Open now" : "Closed";
    $("state").className = "badge " + (s.open ? "open" : "closed");
    return s.today;
  } catch (e) { $("state").textContent = "Server offline"; toast(e.message); return DAYS[0]; }
}

async function loadMenu(d) {
  try {
    const data = await api("/menu?day=" + encodeURIComponent(d));
    day = data.day; menu = data.items;
    cart = {};                       // prices and items differ per day, so start a fresh cart
    renderChips(); renderMenu(); renderCart();
  } catch (e) { toast(e.message); }
}

function renderChips() {
  $("days").innerHTML = DAYS.map(d =>
    `<button class="chip ${d === day ? "on" : ""}" onclick="loadMenu('${d}')">${d.slice(0,3)}</button>`).join("");
  $("cats").innerHTML = CATS.map(c =>
    `<button class="chip ${c === cat ? "on" : ""}" onclick="setCat('${c}')">${c}</button>`).join("");
}

function setCat(c) { cat = c; renderChips(); renderMenu(); }

function renderMenu() {
  const q = $("search").value.toLowerCase().trim();
  const list = menu.filter(d => (cat === "All" || d.category === cat) &&
                                (!q || (d.name + " " + d.description).toLowerCase().includes(q)));
  $("grid").innerHTML = list.length ? list.map(d => `
    <div class="card">
      <h3>${esc(d.name)}</h3>
      <p>${esc(d.description)}</p>
      <div class="row"><span class="cat">${esc(d.category)}</span><span class="price">${rupee(d.price)}</span></div>
      <div class="tags">${d.veg ? "Veg" : "Non-veg"} · ${d.prep_time_minutes} min${d.popular ? " · Popular" : ""}</div>
      <button class="add" onclick="addToCart(${d.id})">Add to cart</button>
    </div>`).join("") : `<div class="empty" style="grid-column:1/-1">No dishes match.</div>`;
}

/* ---------- cart ---------- */
function toggleCart() { $("drawer").classList.toggle("open"); }

function addToCart(id) { cart[id] = (cart[id] || 0) + 1; renderCart(); toast("Added to cart"); }
function changeQty(id, n) { cart[id] += n; if (cart[id] <= 0) delete cart[id]; renderCart(); }

function renderCart() {
  const ids = Object.keys(cart);
  let total = 0, count = 0;
  $("lines").innerHTML = ids.length ? ids.map(id => {
    const d = menu.find(x => x.id == id); if (!d) return "";
    total += d.price * cart[id]; count += cart[id];
    return `<div class="line"><div><b>${esc(d.name)}</b><br><small>${rupee(d.price)} each</small></div>
      <div class="qty"><button onclick="changeQty(${id},-1)">−</button><b>${cart[id]}</b><button onclick="changeQty(${id},1)">+</button></div></div>`;
  }).join("") : `<div class="empty">Your cart is empty.</div>`;
  $("total").textContent = rupee(total);
  $("count").textContent = count;
}

async function placeOrder() {
  const items = Object.keys(cart).map(id => ({ item_id: Number(id), quantity: cart[id] }));
  if (!items.length) return toast("Your cart is empty");
  try {
    const order = await api("/orders", { method: "POST", headers: { "Content-Type": "application/json" },
                                         body: JSON.stringify({ items, note: $("note").value }) });
    cart = {}; $("note").value = ""; renderCart(); toggleCart();
    localStorage.setItem("lastOrder", order.id);
    toast("Order #" + order.id + " placed");
    track(order.id);
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  } catch (e) { toast(e.message); }
}

/* ---------- tracking ---------- */
async function track(id) {
  clearInterval(timer);
  await refreshOrder(id);
  timer = setInterval(() => refreshOrder(id), 5000);
}

async function refreshOrder(id) {
  try {
    const o = await api("/orders/" + id);
    const stage = { received: 0, preparing: 1, ready: 2, picked_up: 2 }[o.status];
    const steps = ["Received", "Preparing", "Ready"].map((s, i) =>
      `<div class="step ${stage !== undefined && i <= stage ? "on" : ""}">${s}</div>`).join("");
    const lines = o.items.map(l => `<div class="line"><span>${esc(l.name)} × ${l.quantity}</span><b>${rupee(l.line_total)}</b></div>`).join("");
    let action = "";
    if (o.status === "received") action = `<button class="ghost" onclick="cancelOrder(${o.id})">Cancel order</button>`;
    if (o.status === "ready") action = `<button class="ghost" onclick="pickup(${o.id})">Mark as picked up</button>`;
    const wait = ["received","preparing"].includes(o.status) ? `About ${o.minutes_left} min left` : "";
    $("tracker").innerHTML = `
      <div class="row"><b>Order #${o.id}</b><span class="cat">${o.status.replace("_"," ")}</span></div>
      ${o.status === "cancelled" ? `<p class="empty">This order was cancelled.</p>` : `<div class="steps">${steps}</div>`}
      <p>${wait}</p>${lines}
      <div class="total"><span>Total</span><span>${rupee(o.total)}</span></div>${action}`;
    if (["cancelled", "picked_up"].includes(o.status)) clearInterval(timer);
  } catch (e) { clearInterval(timer); toast(e.message); }
}

async function cancelOrder(id) {
  try { await api("/orders/" + id + "/cancel", { method: "POST" }); toast("Order cancelled"); refreshOrder(id); }
  catch (e) { toast(e.message); }
}
async function pickup(id) {
  try { await api("/orders/" + id + "/pickup", { method: "POST" }); toast("Enjoy your meal!"); refreshOrder(id); }
  catch (e) { toast(e.message); }
}

/* ---------- combos ---------- */
async function findCombos() {
  try {
    const d = await api("/combos?budget=" + $("budget").value);
    $("combos").innerHTML = d.combos.length ? d.combos.map(c => `
      <div class="combo"><span>${c.items.map(i => esc(i.name)).join(" + ")}</span><b>${rupee(c.total)}</b></div>`).join("")
      : `<div class="empty">Nothing fits that budget today.</div>`;
  } catch (e) { toast(e.message); }
}

/* ---------- start ---------- */
$("search").oninput = renderMenu;
$("budget").oninput = () => $("budgetText").textContent = rupee($("budget").value);
(async () => {
  const today = await loadStatus();
  await loadMenu(today);
  const last = localStorage.getItem("lastOrder");
  if (last) track(last);
})();
</script>
</body>
</html>"""


@app.get("/")
def index():
    return PAGE


if __name__ == "__main__":
    print("Canteen website running at http://localhost:8000")
    app.run(host="127.0.0.1", port=8000, debug=False)
