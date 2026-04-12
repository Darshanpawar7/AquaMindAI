import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Droplets, Clock, Users } from 'lucide-react';
import { Pipe, Alert } from '../api';

const RISK_COLORS: Record<string,string> = { Critical:'#dc2626', High:'#ea580c', Medium:'#ca8a04', Low:'#16a34a', None:'#94a3b8' };

function getRisk(pipeId: string, alerts: Alert[]): string {
  const pa = alerts.filter(a=>a.pipe_id===pipeId);
  if (!pa.length) return 'None';
  for (const l of ['Critical','High','Medium','Low']) if (pa.some(a=>a.priority_level===l)) return l;
  return 'None';
}

interface Props { pipes:Pipe[]; alerts:Alert[]; selectedAlertId:string|null; onSelectAlert:(id:string)=>void; }

export function PipeNetworkView({ pipes, alerts, selectedAlertId, onSelectAlert }: Props) {
  const selectedPipeId = alerts.find(a=>a.alert_id===selectedAlertId)?.pipe_id ?? null;

  const stats = {
    critical: pipes.filter(p=>getRisk(p.pipe_id,alerts)==='Critical').length,
    high:     pipes.filter(p=>getRisk(p.pipe_id,alerts)==='High').length,
    normal:   pipes.filter(p=>getRisk(p.pipe_id,alerts)==='None').length,
  };

  return (
    <div className="space-y-5">
      {/* Summary row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label:'Total Pipes',  value:pipes.length,    color:'#2563eb' },
          { label:'Critical',     value:stats.critical,  color:'#dc2626' },
          { label:'High Risk',    value:stats.high,      color:'#ea580c' },
          { label:'Normal',       value:stats.normal,    color:'#16a34a' },
        ].map(s=>(
          <div key={s.label} className="glass-card rounded-2xl p-4 flex items-center gap-3">
            <div className="h-3 w-3 rounded-full shrink-0" style={{ background:s.color, boxShadow:`0 0 8px ${s.color}` }}/>
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{s.label}</div>
              <div className="text-xl font-black" style={{ color:s.color }}>{s.value}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <h2 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
            <MapPin className="h-4 w-4 text-blue-500"/>
            Pipe Network Map
            <span className="badge bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">{pipes.length} pipes</span>
          </h2>
          <div className="flex gap-3 flex-wrap">
            {Object.entries(RISK_COLORS).map(([level,color])=>(
              <div key={level} className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                <div className="h-2.5 w-2.5 rounded-full" style={{ background:color }}/>
                {level}
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
          {pipes.map(pipe=>{
            const risk  = getRisk(pipe.pipe_id, alerts);
            const color = RISK_COLORS[risk];
            const alert = alerts.find(a=>a.pipe_id===pipe.pipe_id);
            const isSel = pipe.pipe_id===selectedPipeId;
            return (
              <motion.div key={pipe.pipe_id}
                whileHover={{ scale:1.04, y:-3 }} whileTap={{ scale:0.97 }}
                onClick={()=>{ if(alert) onSelectAlert(alert.alert_id); }}
                className={`p-3 rounded-2xl cursor-pointer border-2 transition-all ${isSel ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-transparent hover:border-slate-200 dark:hover:border-slate-700'}`}
                style={{ background: isSel ? `${color}20` : `${color}10` }}>
                <div className="flex items-center justify-between mb-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${risk==='Critical'?'pulse-critical':''}`}
                    style={{ background:color, boxShadow:`0 0 6px ${color}` }}/>
                  <span className="text-[9px] font-bold uppercase" style={{ color }}>{risk}</span>
                </div>
                <div className="text-xs font-bold text-slate-700 dark:text-slate-200 truncate mb-1">{pipe.pipe_id}</div>
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1 text-[10px] text-slate-500">
                    <Droplets className="h-2.5 w-2.5"/>{pipe.diameter_mm}mm
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-slate-500">
                    <Clock className="h-2.5 w-2.5"/>{pipe.age_years}y old
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-slate-500">
                    <Users className="h-2.5 w-2.5"/>{pipe.population_affected.toLocaleString()}
                  </div>
                </div>
                {alert && (
                  <div className="mt-2 text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background:`${color}20`, color }}>
                    {alert.anomaly_type}
                  </div>
                )}
              </motion.div>
            );
          })}
          {pipes.length===0 && (
            <div className="col-span-full text-center text-slate-400 text-sm py-16">
              No pipes loaded — run <code className="mx-1 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs">python simulator/seed_local.py</code>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
