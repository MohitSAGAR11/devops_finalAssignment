import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api.js';
import ProductForm from './ProductForm.jsx';

const currency = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' });

function stockState(product) {
  if (product.quantity === 0) return { key: 'out', label: 'Out of stock' };
  if (product.low_stock) return { key: 'low', label: 'Low stock' };
  return { key: 'ok', label: 'In stock' };
}

export default function App() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('ALL');
  const [lowOnly, setLowOnly] = useState(false);
  const [editing, setEditing] = useState(null); // null = closed, {} = new, product = edit

  const load = useCallback(async () => {
    try {
      const [list, summary] = await Promise.all([api.list(), api.stats()]);
      setProducts(list);
      setStats(summary);
      setError('');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const run = async (action) => {
    try {
      await action();
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const categories = useMemo(
    () => [...new Set(products.map((p) => p.category))].sort(),
    [products],
  );

  const visible = products.filter((p) => {
    const term = search.trim().toLowerCase();
    const matchesTerm =
      !term ||
      p.name.toLowerCase().includes(term) ||
      p.sku.toLowerCase().includes(term) ||
      p.supplier.toLowerCase().includes(term);
    const matchesCategory = category === 'ALL' || p.category === category;
    return matchesTerm && matchesCategory && (!lowOnly || p.low_stock);
  });

  const save = async (form) => {
    if (editing?.id) await api.update(editing.id, form);
    else await api.create(form);
    setEditing(null);
    await load();
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="logo" aria-hidden="true">▣</span>
          <div>
            <strong>Inventory Manager</strong>
            <small>Warehouse stock control</small>
          </div>
        </div>
        <button className="btn primary" onClick={() => setEditing({})}>
          + Add product
        </button>
      </header>

      <main className="page">
        {error && (
          <div className="banner" role="alert">
            <span>⚠ {error}</span>
            <button className="link" onClick={() => setError('')}>Dismiss</button>
          </div>
        )}

        <section className="kpis">
          <Kpi label="Products" value={stats?.totalProducts ?? '—'} />
          <Kpi label="Units in stock" value={stats?.totalUnits ?? '—'} />
          <Kpi
            label="Need reorder"
            value={stats?.lowStock ?? '—'}
            hint={stats ? `${stats.outOfStock} out of stock` : ''}
            tone={stats?.lowStock ? 'warn' : ''}
          />
          <Kpi
            label="Inventory value"
            value={stats ? currency.format(stats.inventoryValue) : '—'}
          />
        </section>

        <section className="card">
          <div className="toolbar">
            <input
              className="search"
              type="search"
              placeholder="Search name, SKU or supplier…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search products"
            />
            <select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Category">
              <option value="ALL">All categories</option>
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <label className="toggle">
              <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
              Needs reorder only
            </label>
          </div>

          {loading ? (
            <p className="empty">Loading inventory…</p>
          ) : visible.length === 0 ? (
            <p className="empty">
              {products.length ? 'No products match these filters.' : 'No products yet — add your first one.'}
            </p>
          ) : (
            <table className="products">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Category</th>
                  <th className="num">Unit price</th>
                  <th>Stock</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {visible.map((p) => {
                  const state = stockState(p);
                  return (
                    <tr key={p.id}>
                      <td data-label="SKU"><code>{p.sku}</code></td>
                      <td data-label="Product">
                        <strong>{p.name}</strong>
                        <small>{p.supplier}</small>
                      </td>
                      <td data-label="Category">{p.category}</td>
                      <td data-label="Unit price" className="num">{currency.format(p.unit_price)}</td>
                      <td data-label="Stock">
                        <div className="stock">
                          <button
                            className="step"
                            aria-label={`Ship one ${p.name}`}
                            disabled={p.quantity === 0}
                            onClick={() => run(() => api.adjust(p.id, -1))}
                          >−</button>
                          <span className="qty">{p.quantity}</span>
                          <button
                            className="step"
                            aria-label={`Receive one ${p.name}`}
                            onClick={() => run(() => api.adjust(p.id, 1))}
                          >+</button>
                          <span className={`pill ${state.key}`}>{state.label}</span>
                        </div>
                        <small>Reorder at {p.reorder_level}</small>
                      </td>
                      <td className="actions">
                        <button className="btn ghost" onClick={() => setEditing(p)}>Edit</button>
                        <button
                          className="btn ghost danger"
                          onClick={() => {
                            if (confirm(`Delete ${p.name}?`)) run(() => api.remove(p.id));
                          }}
                        >Delete</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>
      </main>

      {editing && <ProductForm product={editing} onSave={save} onClose={() => setEditing(null)} />}
    </div>
  );
}

function Kpi({ label, value, hint, tone = '' }) {
  return (
    <div className={`kpi ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}
