import React from 'react';
import { Terminal } from 'lucide-react';
import { AuditRecord } from '../types';
import { Card } from '../components/common/Card';

interface AuditPageProps {
  logs: AuditRecord[];
}

export const AuditPage: React.FC<AuditPageProps> = ({ logs }) => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/30">
              IMMUTABLE AUDIT RECORD
            </span>
            <span className="text-xs font-mono text-emerald-400">
              ✓ APPEND-ONLY TAMPER-PROOF LOGS
            </span>
          </div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide mt-1">
            FORENSIC AUDIT TRAIL
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete tamper-proof accountability records for searches, watchlist updates, and alert acknowledgments
          </p>
        </div>
      </div>

      <Card title={`System & Security Action Records (${logs.length})`}>
        <div className="divide-y divide-slate-800/80 font-mono text-xs">
          {logs.map((log) => (
            <div
              key={log.id}
              className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/30 px-3 rounded-lg transition-colors"
            >
              <div className="flex items-center gap-3">
                <Terminal className="h-4 w-4 text-blue-400 flex-shrink-0" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                      {log.action}
                    </span>
                    <span className="text-slate-400">
                      Resource: <strong className="text-slate-200">{log.resource_type}</strong> ({log.resource_id})
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    User: <strong className="text-blue-300">{log.username}</strong> [{log.role}] • IP: {log.ip_address}
                  </p>
                </div>
              </div>

              <div className="text-right flex-shrink-0">
                <span className="text-emerald-400 font-bold">{log.status}</span>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  {new Date(log.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
