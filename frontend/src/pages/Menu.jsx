import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, UtensilsCrossed, ImageIcon, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { api, fmtMoney } from "@/lib/api";

function ItemDialog({ open, setOpen, categories, items, initial, onSaved }) {
  const editing = !!initial?.id;
  const [form, setForm] = useState(
    initial || { category_id: categories[0]?.id || "", name: "", description: "", price: "", image_url: "", available: true, addon_item_ids: [] }
  );
  const [saving, setSaving] = useState(false);

  React.useEffect(() => {
    setForm(initial || { category_id: categories[0]?.id || "", name: "", description: "", price: "", image_url: "", available: true, addon_item_ids: [] });
  }, [initial, open, categories]);

  const save = async () => {
    if (!form.name || !form.price || !form.category_id) {
      toast.error("Name, price and category are required");
      return;
    }
    setSaving(true);
    try {
      const body = { ...form, price: parseFloat(form.price), addon_item_ids: form.addon_item_ids || [] };
      if (editing) await api.updateItem(initial.id, body);
      else await api.createItem(body);
      toast.success(editing ? "Item updated" : "Item added");
      setOpen(false);
      onSaved();
    } catch {
      toast.error("Could not save item");
    } finally {
      setSaving(false);
    }
  };

  const toggleAddon = (id) => {
    const cur = new Set(form.addon_item_ids || []);
    cur.has(id) ? cur.delete(id) : cur.add(id);
    setForm({ ...form, addon_item_ids: [...cur] });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto thin-scroll">
        <DialogHeader><DialogTitle className="font-display">{editing ? "Edit Item" : "Add Menu Item"}</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Category</Label>
            <Select value={form.category_id} onValueChange={(v) => setForm({ ...form, category_id: v })}>
              <SelectTrigger data-testid="item-category-select" className="mt-1.5"><SelectValue placeholder="Select category" /></SelectTrigger>
              <SelectContent>
                {categories.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Name</Label>
            <Input data-testid="item-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1.5" />
          </div>
          <div>
            <Label>Description</Label>
            <Textarea data-testid="item-desc-input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="mt-1.5" rows={2} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Price (PKR)</Label>
              <Input data-testid="item-price-input" type="number" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} className="mt-1.5" />
            </div>
            <div className="flex items-end pb-2">
              <div className="flex items-center gap-2">
                <Switch data-testid="item-available-switch" checked={form.available} onCheckedChange={(v) => setForm({ ...form, available: v })} />
                <span className="text-sm">Available</span>
              </div>
            </div>
          </div>
          <div>
            <Label>Image URL</Label>
            <Input data-testid="item-image-input" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} className="mt-1.5" placeholder="https://…" />
          </div>
          <div>
            <Label>Recommended add-ons (upsell)</Label>
            <div className="mt-2 flex flex-wrap gap-2 max-h-32 overflow-y-auto thin-scroll">
              {items.filter((it) => it.id !== initial?.id).map((it) => {
                const on = (form.addon_item_ids || []).includes(it.id);
                return (
                  <button
                    key={it.id}
                    type="button"
                    onClick={() => toggleAddon(it.id)}
                    className={`px-2.5 py-1 rounded-full text-xs border transition-colors ${on ? "bg-secondary text-secondary-foreground border-secondary" : "bg-card border-border text-muted-foreground hover:border-secondary/50"}`}
                  >
                    {it.name}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} className="rounded-full">Cancel</Button>
          <Button data-testid="save-item-btn" onClick={save} disabled={saving} className="rounded-full gap-2">
            {saving && <Loader2 className="w-4 h-4 animate-spin" />} Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Menu() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["menu"], queryFn: async () => (await api.getMenu()).data });
  const categories = data?.categories || [];
  const items = data?.items || [];

  const [itemDialog, setItemDialog] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [catDialog, setCatDialog] = useState(false);
  const [catName, setCatName] = useState("");

  const refetch = () => qc.invalidateQueries({ queryKey: ["menu"] });

  const toggleAvail = useMutation({
    mutationFn: ({ id, available }) => api.updateItem(id, { available }),
    onSuccess: refetch,
  });
  const delItem = useMutation({ mutationFn: (id) => api.deleteItem(id), onSuccess: () => { refetch(); toast.success("Item deleted"); } });
  const delCat = useMutation({ mutationFn: (id) => api.deleteCategory(id), onSuccess: () => { refetch(); toast.success("Category deleted"); } });

  const addCategory = async () => {
    if (!catName.trim()) return;
    await api.createCategory({ name: catName.trim(), sort_order: categories.length + 1 });
    setCatName("");
    setCatDialog(false);
    refetch();
    toast.success("Category added");
  };

  const openNewItem = () => { setEditingItem(null); setItemDialog(true); };
  const openEditItem = (it) => { setEditingItem(it); setItemDialog(true); };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-extrabold">Menu</h1>
          <p className="text-muted-foreground mt-1">Manage categories and items your AI can sell.</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={catDialog} onOpenChange={setCatDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="add-category-btn" className="rounded-full gap-2"><Plus className="w-4 h-4" /> Category</Button>
            </DialogTrigger>
            <DialogContent className="max-w-sm">
              <DialogHeader><DialogTitle className="font-display">Add Category</DialogTitle></DialogHeader>
              <Input data-testid="category-name-input" value={catName} onChange={(e) => setCatName(e.target.value)} placeholder="e.g. Wraps" />
              <DialogFooter>
                <Button data-testid="save-category-btn" onClick={addCategory} className="rounded-full">Add</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Button data-testid="add-item-btn" onClick={openNewItem} disabled={categories.length === 0} className="rounded-full gap-2"><Plus className="w-4 h-4" /> Item</Button>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading menu…</p>}
      {!isLoading && categories.length === 0 && (
        <Card className="rounded-2xl border-dashed border-2 p-10 text-center text-muted-foreground">
          <UtensilsCrossed className="w-8 h-8 mx-auto mb-3 opacity-40" />
          No categories yet. Add a category to start building your menu.
        </Card>
      )}

      {categories.map((cat) => {
        const catItems = items.filter((it) => it.category_id === cat.id);
        return (
          <div key={cat.id} data-testid={`menu-category-${cat.id}`}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-display text-xl font-bold">{cat.name} <span className="text-muted-foreground text-sm font-normal">({catItems.length})</span></h2>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="sm" data-testid={`delete-category-${cat.id}`} className="text-muted-foreground hover:text-destructive gap-1.5"><Trash2 className="w-3.5 h-3.5" /> Delete category</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete "{cat.name}"?</AlertDialogTitle>
                    <AlertDialogDescription>This will remove the category and all its items.</AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => delCat.mutate(cat.id)} className="bg-destructive hover:bg-destructive/90">Delete</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {catItems.map((it) => (
                <Card key={it.id} data-testid={`menu-item-${it.id}`} className={`rounded-2xl border-border shadow-sm overflow-hidden transition-all ${!it.available ? "opacity-60" : ""}`}>
                  <div className="h-32 bg-muted flex items-center justify-center overflow-hidden">
                    {it.image_url ? (
                      <img src={it.image_url} alt={it.name} className="w-full h-full object-cover" />
                    ) : (
                      <ImageIcon className="w-8 h-8 text-muted-foreground/40" />
                    )}
                  </div>
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-semibold text-sm truncate">{it.name}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">{it.description}</p>
                      </div>
                      <span className="font-display font-bold text-sm whitespace-nowrap">{fmtMoney(it.price)}</span>
                    </div>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
                      <div className="flex items-center gap-2">
                        <Switch
                          data-testid={`avail-switch-${it.id}`}
                          checked={it.available}
                          onCheckedChange={(v) => toggleAvail.mutate({ id: it.id, available: v })}
                        />
                        <span className="text-xs text-muted-foreground">{it.available ? "Available" : "Hidden"}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button variant="ghost" size="icon" data-testid={`edit-item-${it.id}`} onClick={() => openEditItem(it)} className="h-8 w-8"><Pencil className="w-4 h-4" /></Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="icon" data-testid={`delete-item-${it.id}`} className="h-8 w-8 text-muted-foreground hover:text-destructive"><Trash2 className="w-4 h-4" /></Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete "{it.name}"?</AlertDialogTitle>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction onClick={() => delItem.mutate(it.id)} className="bg-destructive hover:bg-destructive/90">Delete</AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
              {catItems.length === 0 && <p className="text-sm text-muted-foreground col-span-full">No items in this category.</p>}
            </div>
          </div>
        );
      })}

      {itemDialog && (
        <ItemDialog open={itemDialog} setOpen={setItemDialog} categories={categories} items={items} initial={editingItem} onSaved={refetch} />
      )}
    </div>
  );
}
