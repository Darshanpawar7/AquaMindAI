import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock, Zap, Filter } from 'lucide-react';
import { Alert } from '../api';

interface AlertsPanelProps {
  alerts: Alert[];
  selectedAlertId: string | null;
  onSelectAlert: (id: string) => void;
  error: string | null;
}

const PRIORITY_COLORS: Record<string, string> = {
  Critical: '#dc2626',
  High:     '#ea580c',
  Medium:   '#ca8a04',
  Low:      '#16a34a',
};

type Filter = 'All' | 'Critical' | 'High' | 'Medium' | 'Low';

export function AlertsPanel({ alerts, selectedAlertId, onSelectAlert, error }: AlertsPanelProps) {
  const [filter, setFilter] = useState<Filter>('All');

  const filtered = filter === 'All' ? alerts : alerts.filter((a) => a.priority_level === filter);
  const sorted = [...filtered].sort((a, b) => {
    const order = ['Critical', 'High', 'Medium', 'Low'];
    return order.indexOf(a.priority_level) - order.indexOf(b.priority_level);
  });

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex items-center justify-between shrink-0">
        <h2 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          Alerts
          <span className="badge bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">{alerts.length}</span>
        </h2>
        <Filter className="h-4 w-4 text-slate-400" />
      </div>

      {/* Filter pills */}
      <div className="flex gap-1.5 flex-wrap shrink-0">
        {(['All', 'Critical', 'High', 'Medium', 'Low'] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            aria-label={`Filter by ${f}`}
            className={`px-2.5 py-1 rounded-full text-xs font-bold transition-all ${
              filter === f
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            {f === 'All' ? 'All' : f === 'Critical' ? '🔴 Crit' : f === 'High' ? '🟠 High' : f === 'Medium' ? '🟡 Med' : '🟢 Low'}
          </button>
        ))}
      </div>

      {error && (
        <div role="alert" className="shrink-0 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-xs text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="overflow-y-auto flex-1 space-y-2 pr-0.5">
        <AnimatePresence>
          {sorted.map((alert) => {
            const color = PRIORITY_COLORS[alert.priority_level] ?? '#6b7280';
            const isSelected = alert.alert_id === selectedAlertId;
            return (
              <motion.div
                key={alert.alert_id}
                layout
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                onClick={() => onSelectAlert(alert.alert_id)}
                className={`p-3 rounded-xl cursor-pointer border-2 transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-transparent bg-slate-50 dark:bg-slate-800/50 hover:border-slate-200 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="h-2 w-2 rounded-full shrink-0" style={{ background: color, boxShadow: `0 0 5px ${color}` }} />
                  <span className="badge text-[10px]" style={{ background: `${color}18`, color }}>{alert.priority_level}</span>
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-200">{alert.pipe_id}</span>
                  <span className="ml-auto text-[10px] text-slate-400 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 pl-4">
                  {alert.anomaly_type} — score: <span className="font-mono font-bold">{alert.anomaly_score.toFixed(2)}</span>
                </div>
                {alert.immediate_action_required && (
                  <div className="mt-1.5 pl-4 flex items-center gap-1 text-[10px] font-bold text-red-500">
                    <Zap className="h-3 w-3" /> Immediate Action Required
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {sorted.length === 0 && !error && (
          <div className="text-center text-slate-400 text-sm py-12">No alerts</div>
        )}
      </div>
    </div>
  );
}
