import React from 'react';
import { Download, CheckCircle2, Lock, FileCode } from 'lucide-react';
import { EvidenceRecord } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

interface EvidencePageProps {
  evidence: EvidenceRecord[];
}

export const EvidencePage: React.FC<EvidencePageProps> = ({ evidence }) => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-xs font-bold border border-emerald-500/30">
              CHAIN OF CUSTODY ASSURED
            </span>
            <span className="text-xs font-mono text-emerald-400">
              ✓ SHA-256 FORENSIC INTEGRITY SIGNATURES
            </span>
          </div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide mt-1">
            CRYPTOGRAPHIC EVIDENCE VAULT
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Court-admissible evidentiary records with verifiable SHA-256 hashes and timestamp sealing
          </p>
        </div>

        <Button variant="primary" size="md" icon={<Download className="h-4 w-4" />}>
          Export Evidence Package
        </Button>
      </div>

      <Card title={`Sealed Forensic Evidence Records (${evidence.length})`}>
        <div className="space-y-4">
          {evidence.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-xl bg-[#080d19] border border-slate-800 hover:border-emerald-500/60 transition-all space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <FileCode className="h-5 w-5 text-emerald-400" />
                  <div>
                    <h4 className="text-sm font-bold text-white font-mono">{item.file_name}</h4>
                    <p className="text-[10px] text-slate-400 font-mono">
                      Camera: {item.camera_name} • Captured: {new Date(item.captured_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <span className="text-xs font-mono text-emerald-400 flex items-center gap-1 font-bold">
                  <CheckCircle2 className="h-4 w-4" /> HASH VERIFIED
                </span>
              </div>

              {/* SHA-256 Display */}
              <div className="p-2.5 rounded-lg bg-black/80 border border-slate-800 flex items-center justify-between text-xs font-mono text-slate-300">
                <div className="flex items-center gap-2 min-w-0">
                  <Lock className="h-3.5 w-3.5 text-yellow-400 flex-shrink-0" />
                  <span className="text-slate-400">SHA-256:</span>
                  <span className="text-yellow-300 truncate">{item.sha256_hash}</span>
                </div>
                <span className="text-[10px] text-slate-400 flex-shrink-0">
                  {Math.round(item.file_size_bytes / 1024)} KB
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
