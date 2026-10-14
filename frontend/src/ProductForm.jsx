import { useState } from 'react';

const EMPTY = {
  sku: '',
  name: '',
  description: '',
  category: 'General',
  supplier: '',
  quantity: 0,
  reorder_level: 10,
  unit_price: 0,
};

export default function ProductForm({ product, onSave, onClose }) {
  const isEdit = Boolean(product.id);
  const [form, setForm] = useState({ ...EMPTY, ...product });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const set = (field) => (e) => {
    const value = e.target.type === 'number' ? Number(e.target.value) : e.target.value;
    setForm((f) => ({ ...f, [field]: value }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const { sku, name, description, category, supplier, quantity, reorder_level, unit_price } = form;
      await onSave({
        sku: sku.trim(),
        name: name.trim(),
        description,
        category: category.trim() || 'General',
        supplier: supplier.trim() || 'Unspecified',
        quantity,
        reorder_level,
        unit_price,
      });
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <div className="overlay" onClick={onClose}>
      <form className="dialog" onSubmit={submit} onClick={(e) => e.stopPropagation()}>
        <div className="dialog-head">
          <h2>{isEdit ? 'Edit product' : 'Add product'}</h2>
          <button type="button" className="btn ghost" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {error && <p className="form-error">{error}</p>}

        <div className="grid">
          <label>SKU<input required maxLength={40} value={form.sku} onChange={set('sku')} placeholder="KB-001" /></label>
          <label>Name<input required maxLength={200} value={form.name} onChange={set('name')} placeholder="Mechanical keyboard" /></label>
          <label>Category<input maxLength={100} value={form.category} onChange={set('category')} /></label>
          <label>Supplier<input maxLength={120} value={form.supplier} onChange={set('supplier')} placeholder="Unspecified" /></label>
          <label>Quantity<input type="number" min="0" required value={form.quantity} onChange={set('quantity')} /></label>
          <label>Reorder level<input type="number" min="0" required value={form.reorder_level} onChange={set('reorder_level')} /></label>
          <label>Unit price (₹)<input type="number" min="0" step="0.01" required value={form.unit_price} onChange={set('unit_price')} /></label>
        </div>
        <label>Description<textarea value={form.description} onChange={set('description')} rows={3} /></label>

        <div className="dialog-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={saving}>{saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add product'}</button>
        </div>
      </form>
    </div>
  );
}
