import React, { useState, useMemo } from 'react';
import {
  Bell,
  CheckCircle2,
  Database,
  Download,
  Filter,
  Flame,
  Plus,
  Radio,
  Search,
  Shield,
  ShieldAlert,
  Trash2,
  Upload,
  UserCheck,
  Zap,
} from 'lucide-react';
import { WatchlistEntry, WatchlistCategory, AlertPriority } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { CategoryBadge, PriorityBadge } from '../components/common/Badge';

interface WatchlistsPageProps {
  watchlists: WatchlistEntry[];
  onAddEntry?: (entry: WatchlistEntry) => void;
  onDeleteEntry?: (id: string) => void;
  onToggleEntryStatus?: (id: string) => void;
}

// Default Fallback Demo Watchlist Entries for Gujarat Police
const defaultWatchlistEntries: WatchlistEntry[] = [
  {
    id: 'wl-001',
    watchlist_id: 'WANTED_GANGS',
    watchlist_name: 'Gujarat Inter-District Gold Heist Gang',
    registration_raw: 'GJ01AB1234',
    registration_normalized: 'GJ01AB1234',
    category: 'WANTED',
    priority: 'CRITICAL',
    case_number: 'FIR-2026-AHM-0412',
    reason: 'Wanted under IPC 395/397 for armed jewelry heist in Navrangpura, Ahmedabad.',
    is_active: true,
    created_at: new Date(Date.now() - 3600000 * 48).toISOString(),
  },
  {
    id: 'wl-002',
    watchlist_id: 'STOLEN_REGISTRY',
    watchlist_name: 'Surat Diamond Corridor Hijack Alert',
    registration_raw: 'GJ05CD5678',
    registration_normalized: 'GJ05CD5678',
    category: 'STOLEN',
    priority: 'HIGH',
    case_number: 'FIR-2026-SUR-1109',
    reason: 'Commercial vehicle reported stolen from Surat Varachha textile hub.',
    is_active: true,
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
  {
    id: 'wl-003',
    watchlist_id: 'DRUG_CARTEL',
    watchlist_name: 'Coastal Narcotics Smuggling Intercept',
    registration_raw: 'GJ06XY9999',
    registration_normalized: 'GJ06XY9999',
    category: 'SUSPICIOUS',
    priority: 'HIGH',
    case_number: 'FIR-2026-VAD-8841',
    reason: 'Vehicle observed frequenting unauthorized ports along Bharuch/Surat coastline.',
    is_active: true,
    created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
  },
  {
    id: 'wl-004',
    watchlist_id: 'VIP_ESCORT',
    watchlist_name: 'State Dignitary Convoy Escort Protocol',
    registration_raw: 'GJ18GA0001',
    registration_normalized: 'GJ18GA0001',
    category: 'VIP',
    priority: 'LOW',
    case_number: 'VIP-GANDHINAGAR-01',
    reason: 'Official Governor & Chief Minister Escort Vehicle — Green corridor auto-clear.',
    is_active: true,
    created_at: new Date(Date.now() - 3600000 * 72).toISOString(),
  },
];

export const WatchlistsPage: React.FC<WatchlistsPageProps> = ({
  watchlists = [],
  onAddEntry,
  onDeleteEntry,
  onToggleEntryStatus,
}) => {
  const [entries, setEntries] = useState<WatchlistEntry[]>(
    watchlists.length > 0 ? watchlists : defaultWatchlistEntries
  );
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [statusNotification, setStatusNotification] = useState<string | null>(null);

  // New Hotlist Form State
  const [newPlate, setNewPlate] = useState('');
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const [newCategory, setNewCategory] = useState<WatchlistCategory>('WANTED');
  const [newPriority, setNewPriority] = useState<AlertPriority>('CRITICAL');
  const [newCaseNumber, setNewCaseNumber] = useState('');
  const [newReason, setNewReason] = useState('');

  // Filtering
  const filtered = useMemo(() => {
    return entries.filter((w) => {
      const matchesCategory = filterCategory === 'ALL' || w.category === filterCategory;
      const matchesSearch =
        w.registration_normalized.toLowerCase().includes(searchQuery.toLowerCase()) ||
        w.watchlist_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (w.case_number && w.case_number.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    });
  }, [entries, filterCategory, searchQuery]);

  // Add Watchlist Plate Action
  const handleCreateWatchlistEntry = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlate.trim()) return;

    const normalized = newPlate.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
    const newEntry: WatchlistEntry = {
      id: `wl-${Date.now()}`,
      watchlist_id: newCategory,
      watchlist_name: newWatchlistName || `${newCategory} Alert — ${normalized}`,
      registration_raw: newPlate.trim().toUpperCase(),
      registration_normalized: normalized,
      category: newCategory,
      priority: newPriority,
      case_number: newCaseNumber || `FIR-${new Date().getFullYear()}-GP-${Math.floor(1000 + Math.random() * 9000)}`,
      reason: newReason || 'Added via Gujarat Police Tactical Command Watchlist Manager.',
      is_active: true,
      created_at: new Date().toISOString(),
    };

    setEntries([newEntry, ...entries]);
    if (onAddEntry) onAddEntry(newEntry);

    // Reset Form & Close Modal
    setNewPlate('');
    setNewWatchlistName('');
    setNewCaseNumber('');
    setNewReason('');
    setShowAddModal(false);

    setStatusNotification(`Added ${normalized} to hotlist. Valkey in-memory index synchronized.`);
    setTimeout(() => setStatusNotification(null), 4000);
  };

  // Toggle Status
  const handleToggleStatus = (id: string) => {
    setEntries((prev) =>
      prev.map((e) => (e.id === id ? { ...e, is_active: !e.is_active } : e))
    );
    if (onToggleEntryStatus) onToggleEntryStatus(id);
  };

  // Delete Plate
  const handleDelete = (id: string, plate: string) => {
    setEntries((prev) => prev.filter((e) => e.id !== id));
    if (onDeleteEntry) onDeleteEntry(id);
    setStatusNotification(`Removed ${plate} from active hotlist repository.`);
    setTimeout(() => setStatusNotification(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Header Panel */}
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-rose-500 animate-pulse" />
            <h1 className="text-xl font-black text-white font-mono tracking-wide">
              HOTLISTS & WATCHLIST REPOSITORY
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Statewide automated FIR plate matching & sub-millisecond Valkey in-memory lookup
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span className="px-3 py-1 rounded-lg bg-blue-950/80 border border-blue-800 text-blue-400 text-xs font-mono font-bold flex items-center gap-1.5">
            <Database className="h-3.5 w-3.5" />
            Valkey Synced (&lt;0.5ms)
          </span>

          <Button
            variant="primary"
            size="md"
            icon={<Plus className="h-4 w-4" />}
            onClick={() => setShowAddModal(true)}
          >
            Add Hotlist Plate
          </Button>
        </div>
      </div>

      {statusNotification && (
        <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-700 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          {statusNotification}
        </div>
      )}

      {/* Category Tabs & Quick Search */}
      <div className="bg-[#090e1a] p-3 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          {['ALL', 'WANTED', 'STOLEN', 'SUSPICIOUS', 'VIP'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all ${
                filterCategory === cat
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                  : 'bg-[#070b14] text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search hotlist plate or case..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#070b14] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:border-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Watchlist Entries Table */}
      <Card
        title={`Active Watchlist Plates (${filtered.length} Total Targets)`}
        subtitle="Monitored in real time across all statewide Gujarat CCTV gateway streams"
      >
        {filtered.length === 0 ? (
          <div className="py-12 text-center font-mono text-slate-400">
            <Shield className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm">No hotlist entries matching query.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {filtered.map((entry) => (
              <div
                key={entry.id}
                className={`py-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 px-3 rounded-xl transition-colors ${
                  entry.is_active ? 'hover:bg-slate-800/30' : 'opacity-60 bg-slate-950/40'
                }`}
              >
                {/* Left: Plate + Categories */}
                <div className="flex items-center gap-4">
                  <div className="px-3.5 py-1.5 rounded-lg bg-black border-2 border-yellow-400 text-yellow-300 font-mono font-black text-base tracking-wider shadow-inner">
                    {entry.registration_normalized}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <CategoryBadge category={entry.category} />
                      <PriorityBadge priority={entry.priority} />
                      <span
                        className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          entry.is_active
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {entry.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                      </span>
                    </div>
                    <p className="text-xs font-bold text-white font-mono mt-1.5">
                      {entry.watchlist_name}
                    </p>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">{entry.reason}</p>
                  </div>
                </div>

                {/* Right: Case Reference + Actions */}
                <div className="flex items-center gap-4 w-full md:w-auto justify-between md:justify-end">
                  <div className="text-left md:text-right text-xs font-mono text-slate-400">
                    <p>
                      Case: <strong className="text-amber-400">{entry.case_number}</strong>
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      Added: {new Date(entry.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant={entry.is_active ? 'secondary' : 'outline'}
                      size="sm"
                      onClick={() => handleToggleStatus(entry.id)}
                    >
                      {entry.is_active ? 'Deactivate' : 'Activate'}
                    </Button>

                    <button
                      onClick={() => handleDelete(entry.id, entry.registration_normalized)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                      title="Delete Hotlist Plate"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Add Hotlist Plate Modal */}
      {showAddModal && (
        <Modal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="ADD PLATE TO STATEWIDE HOTLIST"
          subtitle="Enters plate into Gujarat Police high-priority in-memory Valkey index"
          icon={<Plus className="h-5 w-5 text-rose-400" />}
          maxWidth="md"
        >
          <form onSubmit={handleCreateWatchlistEntry} className="space-y-4 font-mono text-xs">
            {/* Registration Plate */}
            <div>
              <label className="block text-slate-300 font-bold mb-1">
                VEHICLE REGISTRATION NUMBER *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. GJ01AB9999"
                value={newPlate}
                onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
                className="w-full bg-[#070b14] border border-blue-500/60 rounded-xl px-3 py-2 text-sm text-yellow-300 font-black tracking-wider uppercase focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Watchlist Name / Alert Tag */}
            <div>
              <label className="block text-slate-300 mb-1">WATCHLIST / OPERATION NAME</label>
              <input
                type="text"
                placeholder="e.g. Operation Hawk Eye / FIR Wanted"
                value={newWatchlistName}
                onChange={(e) => setNewWatchlistName(e.target.value)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Category & Priority */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-300 mb-1">CATEGORY</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value as WatchlistCategory)}
                  className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2 text-white focus:outline-none"
                >
                  <option value="WANTED">WANTED (Criminal FIR)</option>
                  <option value="STOLEN">STOLEN (Vehicle Theft)</option>
                  <option value="SUSPICIOUS">SUSPICIOUS (Surveillance)</option>
                  <option value="VIP">VIP (High Dignitary)</option>
                  <option value="SPECIAL_INTEREST">SPECIAL INTEREST</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1">ALERT PRIORITY</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value as AlertPriority)}
                  className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2 text-white focus:outline-none"
                >
                  <option value="CRITICAL">CRITICAL (Immediate Siren)</option>
                  <option value="HIGH">HIGH (Intercept Notice)</option>
                  <option value="MEDIUM">MEDIUM (Standard Log)</option>
                  <option value="LOW">LOW (Informational)</option>
                </select>
              </div>
            </div>

            {/* Case Reference Number */}
            <div>
              <label className="block text-slate-300 mb-1">POLICE STATION FIR / CASE NUMBER</label>
              <input
                type="text"
                placeholder="e.g. FIR-2026-AHM-9021"
                value={newCaseNumber}
                onChange={(e) => setNewCaseNumber(e.target.value)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none"
              />
            </div>

            {/* Reason / Notes */}
            <div>
              <label className="block text-slate-300 mb-1">REASON / BRIEF CASE SYNOPSIS</label>
              <textarea
                rows={3}
                placeholder="Details of the crime or vehicle observation..."
                value={newReason}
                onChange={(e) => setNewReason(e.target.value)}
                className="w-full bg-[#070b14] border border-slate-700 rounded-lg p-2 text-white focus:outline-none"
              />
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <Button variant="ghost" size="sm" onClick={() => setShowAddModal(false)}>
                Cancel
              </Button>
              <Button variant="danger" size="sm" type="submit" icon={<Flame className="h-3.5 w-3.5" />}>
                Commit to Hotlist
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
