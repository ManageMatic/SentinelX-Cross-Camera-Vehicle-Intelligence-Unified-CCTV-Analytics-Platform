import React, { useState, useMemo } from 'react';
import {
  Activity,
  CheckCircle2,
  Download,
  Filter,
  Key,
  Lock,
  Search,
  Shield,
  ShieldCheck,
  Terminal,
  UserCheck,
  Zap,
} from 'lucide-react';
import { AuditRecord } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

interface AuditPageProps {
  logs: AuditRecord[];
}

// Default Fallback Demo Audit Records
const defaultAuditLogs: AuditRecord[] = [
  {
    id: 'aud-001',
    timestamp: new Date(Date.now() - 3600000 * 0.2).toISOString(),
    username: 'inspector_patel',
    role: 'COMMAND_OFFICER',
    action: 'ALERT_DISPATCH',
    resource_type: 'ALERT',
    resource_id: 'alert-001',
    ip_address: '10.24.100.15',
    status: 'SUCCESS',
  },
  {
    id: 'aud-002',
    timestamp: new Date(Date.now() - 3600000 * 0.5).toISOString(),
    username: 'analyst_sharma',
    role: 'ANALYST',
    action: 'ANPR_SEARCH',
    resource_type: 'VEHICLE_INDEX',
    resource_id: 'GJ01AB1234',
    ip_address: '10.24.100.22',
    status: 'SUCCESS',
  },
  {
    id: 'aud-003',
    timestamp: new Date(Date.now() - 3600000 * 1.1).toISOString(),
    username: 'admin_gujarat',
    role: 'ADMIN',
    action: 'WATCHLIST_ADD',
    resource_type: 'HOTLIST',
    resource_id: 'GJ05CD5678',
    ip_address: '10.24.100.1',
    status: 'SUCCESS',
  },
  {
    id: 'aud-004',
    timestamp: new Date(Date.now() - 3600000 * 2.3).toISOString(),
    username: 'investigator_desai',
    role: 'INVESTIGATOR',
    action: 'EVIDENCE_EXPORT',
    resource_type: 'SECTION_65B',
    resource_id: 'ev-001',
    ip_address: '10.24.100.45',
    status: 'SUCCESS',
  },
  {
    id: 'aud-005',
    timestamp: new Date(Date.now() - 3600000 * 3.8).toISOString(),
    username: 'operator_mehta',
    role: 'OPERATOR',
    action: 'AUTH_LOGIN',
    resource_type: 'SESSION',
    resource_id: 'sess-8812',
    ip_address: '10.24.100.19',
    status: 'SUCCESS',
  },
];

export const AuditPage: React.FC<AuditPageProps> = ({ logs = [] }) => {
  const masterLogs = logs.length > 0 ? logs : defaultAuditLogs;

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('ALL');
  const [selectedAction, setSelectedAction] = useState<string>('ALL');
  const [notification, setNotification] = useState<string | null>(null);

  // Filter logs
  const filteredLogs = useMemo(() => {
    return masterLogs.filter((log) => {
      const matchesSearch =
        log.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.ip_address.includes(searchQuery) ||
        (log.resource_id && log.resource_id.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesRole = selectedRole === 'ALL' || log.role === selectedRole;
      const matchesAction = selectedAction === 'ALL' || log.action === selectedAction;
      return matchesSearch && matchesRole && matchesAction;
    });
  }, [masterLogs, searchQuery, selectedRole, selectedAction]);

  // Export CSV
  const handleExportAuditCSV = () => {
    const header = 'Audit ID,Timestamp,Username,Role,Action,Resource Type,Resource ID,IP Address,Status\n';
    const rows = filteredLogs
      .map(
        (l) =>
          `"${l.id}","${l.timestamp}","${l.username}","${l.role}","${l.action}","${l.resource_type}","${
            l.resource_id || ''
          }","${l.ip_address}","${l.status}"`
      )
      .join('\n');

    if (typeof window !== 'undefined' && typeof window.URL !== 'undefined' && typeof window.URL.createObjectURL === 'function') {
      const blob = new Blob([header + rows], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SentinelX_Compliance_Audit_${Date.now()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    }

    setNotification(`Exported ${filteredLogs.length} audit trail records to CSV.`);
    setTimeout(() => setNotification(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/40">
              IMMUTABLE AUDIT RECORD
            </span>
            <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="h-3.5 w-3.5" />
              APPEND-ONLY COMPLIANCE LOGS
            </span>
          </div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide mt-1">
            FORENSIC AUDIT TRAIL
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Complete tamper-proof accountability records for searches, watchlist updates, and alert acknowledgments
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<Download className="h-3.5 w-3.5" />}
            onClick={handleExportAuditCSV}
          >
            Export Audit Log
          </Button>
        </div>
      </div>

      {notification && (
        <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-700 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          {notification}
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-[#090e1a] p-3 rounded-xl border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
        <div className="relative">
          <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search user, action, IP..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#070b14] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="w-full bg-[#070b14] border border-slate-800 rounded-lg p-1.5 text-slate-200 focus:outline-none"
          >
            <option value="ALL">ALL USER ROLES</option>
            <option value="ADMIN">ADMIN</option>
            <option value="COMMAND_OFFICER">COMMAND_OFFICER</option>
            <option value="INVESTIGATOR">INVESTIGATOR</option>
            <option value="ANALYST">ANALYST</option>
            <option value="OPERATOR">OPERATOR</option>
          </select>
        </div>

        <div>
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="w-full bg-[#070b14] border border-slate-800 rounded-lg p-1.5 text-slate-200 focus:outline-none"
          >
            <option value="ALL">ALL AUDITED ACTIONS</option>
            <option value="ANPR_SEARCH">ANPR_SEARCH</option>
            <option value="WATCHLIST_ADD">WATCHLIST_ADD</option>
            <option value="ALERT_DISPATCH">ALERT_DISPATCH</option>
            <option value="EVIDENCE_EXPORT">EVIDENCE_EXPORT</option>
            <option value="AUTH_LOGIN">AUTH_LOGIN</option>
          </select>
        </div>
      </div>

      {/* Audit Log Stream */}
      <Card title={`System & Security Action Records (${filteredLogs.length})`}>
        <div className="divide-y divide-slate-800/80 font-mono text-xs">
          {filteredLogs.map((log) => (
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
                <span className="text-emerald-400 font-bold flex items-center justify-end gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  {log.status}
                </span>
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
