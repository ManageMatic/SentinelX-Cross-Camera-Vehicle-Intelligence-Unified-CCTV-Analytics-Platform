import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { WatchlistEntry } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CategoryBadge, PriorityBadge } from '../components/common/Badge';

interface WatchlistsPageProps {
  watchlists: WatchlistEntry[];
  onAddEntry?: () => void;
}

export const WatchlistsPage: React.FC<WatchlistsPageProps> = ({ watchlists }) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const filtered = watchlists.filter((w) =>
    filterCategory === 'ALL' ? true : w.category === filterCategory
  );

  return (
    <div className="space-y-6">
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide">
            HOTLISTS & WATCHLIST REPOSITORY
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time automated plate evaluation against FIRs, stolen vehicle registries, and wanted gangs
          </p>
        </div>

        <Button variant="primary" size="md" icon={<Plus className="h-4 w-4" />}>
          Add Hotlist Plate
        </Button>
      </div>

      {/* Category Tabs */}
      <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
        {['ALL', 'STOLEN', 'WANTED', 'SUSPICIOUS', 'VIP'].map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-3 py-1.5 rounded-lg border transition-all ${
              filterCategory === cat
                ? 'bg-blue-600 text-white font-bold border-blue-500 shadow-[0_0_10px_rgba(37,99,235,0.3)]'
                : 'bg-[#0d1424] text-slate-400 border-slate-800 hover:text-white'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Watchlist Entries Table */}
      <Card title={`Active Watchlist Plates (${filtered.length} Total)`}>
        <div className="divide-y divide-slate-800/80">
          {filtered.map((entry) => (
            <div
              key={entry.id}
              className="py-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-slate-800/30 px-3 rounded-xl transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="px-3 py-1.5 rounded-lg bg-black border border-yellow-500/60 text-yellow-300 font-mono font-black text-sm tracking-wider shadow-inner">
                  {entry.registration_normalized}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <CategoryBadge category={entry.category} />
                    <PriorityBadge priority={entry.priority} />
                  </div>
                  <p className="text-xs font-bold text-white mt-1.5">{entry.watchlist_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{entry.reason}</p>
                </div>
              </div>

              <div className="text-left md:text-right text-xs font-mono text-slate-400">
                <p>Case: <strong className="text-slate-200">{entry.case_number}</strong></p>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Added: {new Date(entry.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
