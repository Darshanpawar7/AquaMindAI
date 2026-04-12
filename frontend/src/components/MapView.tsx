import React from 'react';
import { motion } from 'framer-motion';
import { MapPin } from 'lucide-react';
import { Pipe, Alert } from '../api';

interface MapViewProps {
  pipes: Pipe[];
  alerts: Alert[];
  selectedPipeId: string | null;
  onSelectPipe: (id: string) => void;
}

const RISK_COLORS: Record<string, string> = {
  Critical: '#dc2626',
  High:     '#ea580c',
  Medium:   '#ca8a04',
  Low:      '#16a34a',
  None:     '#94a3b8',
};

function getPipeRiskLevel(pipeId: string, alerts: Alert[]): string {
  const pipeAlerts = alerts.filter((a) => a.pipe_id === pipeId);
  if (pipeAlerts.length === 0) return 'None';
  for (const level of ['Critical', 'High', 'Medium', 'Low']) {
    if (pipeAlerts.some((a) => a.priority_level === level)) return level;
  }
  return 'None';
}

export function MapView({ pipes, alerts, selectedPipeId, onSelectPipe }: MapViewProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
          <MapPin className="h-4 w-4 text-blue-500" />
          Pipe Network
          <span className="badge bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">{pipes.length} pipes</span>
        </h2>
        {/* Legend */}
        <div className="flex gap-3 flex-wrap">
          {Object.entries(RISK_COLORS).map(([level, color]) => (
            <div key={level} className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <div className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
              {level}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2">
        {pipes.map((pipe) => {
          const riskLevel = getPipeRiskLevel(pipe.pipe_id, alerts);
          const color = RISK_COLORS[riskLevel];
          const isSelected = pipe.pipe_id === selectedPipeId;
          return (
            <motion.div
              key={pipe.pipe_id}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => onSelectPipe(pipe.pipe_id)}
              title={`${pipe.pipe_id} — ${riskLevel} risk\nAge: ${pipe.age_years}y | Pop: ${pipe.population_affected}`}
              className={`p-2.5 rounded-xl cursor-pointer border-2 transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-lg shadow-blue-500/20'
                  : 'border-transparent hover:border-slate-200 dark:hover:border-slate-700'
              }`}
              style={{ background: isSelected ? undefined : `${color}12` }}
            >
              <div
                className="h-2.5 w-2.5 rounded-full mb-2"
                style={{
                  background: color,
                  boxShadow: riskLevel === 'Critical' ? `0 0 8px ${color}` : undefined,
                }}
              />
              <div className="text-[11px] font-bold text-slate-700 dark:text-slate-200 truncate">{pipe.pipe_id}</div>
              <div className="text-[10px] mt-0.5" style={{ color }}>{riskLevel}</div>
            </motion.div>
          );
        })}

        {pipes.length === 0 && (
          <div className="col-span-full text-center text-slate-400 text-sm py-12">
            No pipes loaded — seed the backend first
          </div>
        )}
      </div>
    </div>
  );
}
