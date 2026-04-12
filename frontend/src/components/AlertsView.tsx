import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Clock, MapPin, ChevronRight, CheckCircle2, Siren, Zap, Filter } from 'lucide-react';
import { Alert } from '../api';

const P_COLORS: Record<string,string> = { Critical:'#dc2626', High:'#ea580c', Medium:'#ca8a04', Low:'#16a34a' };
const BORDER: Record<string,string>   = { Critical:'border-l-red-500', High:'border-l-orange-500', Medium:'border-l-yellow-500', Low:'border-l-green-500' };

type F = 'All'|'Critical'|'High'|'Medium'|'Low';

interface Props { alerts:Alert[]; selectedAlertId:string|null; onSelectAlert:(id:string)=>void; error:string|null; }

export function AlertsView({ alerts, selectedAlertId, onSelectAlert, error }: Props) {
  const [filter, setFilter] = useState<F>('All');

  const filtered = (filter==='All' ? alerts : alerts.filter(a=>a.priority_level===filter))
    .sort((a,b)=>{ const o=['Critical','High','Medium','Low']; return o.indexOf(a.priority_level)-o.indexOf(b.priority_level); });

  const counts = { Critical:alerts.filter(a=>a.priority_level==='Critical').length, High:alerts.filter(a=>a.priority_level==='High').length };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-black tracking-tight text-slate-800 dark:text-slate-100">Active Alerts</h2>
          <p className="text-slate-500 text-sm font-medium">AquaMind AI — Anomaly Detection Feed</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <span className="px-3 py-1.5 rounded-full bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 text-xs font-bold border border-red-200 dark:border-red-800">
            {counts.Critical} Critical
          </span>
          <span className="px-3 py-1.5 rounded-full bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400 text-xs font-bold border border-orange-200 dark:border-orange-800">
            {counts.High} High
          </span>
        </div>
      </div>

      {/* Filter pills */}
      <div className="flex gap-2 flex-wrap">
        {(['All','Critical','High','Medium','Low'] as F[]).map(f=>(
          <button key={f} onClick={()=>setFilter(f)} aria-label={`Filter ${f}`}
            className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all border ${filter===f ? 'bg-blue-600 text-white border-blue-600 shadow-lg shadow-blue-500/20' : 'bg-white dark:bg-slate-900 text-slate-500 border-slate-200 dark:border-slate-700 hover:border-blue-400'}`}>
            {f}
          </button>
        ))}
      </div>

      {error && (
        <div role="alert" className="rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">{error}</div>
      )}

      <div className="space-y-4">
        <AnimatePresence>
          {filtered.length > 0 ? filtered.map((alert, i) => {
            const color = P_COLORS[alert.priority_level] ?? '#6b7280';
            const isSel = alert.alert_id === selectedAlertId;
            return (
              <motion.div key={alert.alert_id}
                initial={{ x:-20, opacity:0 }} animate={{ x:0, opacity:1 }} exit={{ opacity:0 }} transition={{ delay:i*0.05 }}
                onClick={()=>onSelectAlert(alert.alert_id)}
                className={`glass-card rounded-3xl p-5 border-l-8 cursor-pointer transition-all hover:shadow-lg ${BORDER[alert.priority_level]??'border-l-slate-400'} ${isSel?'ring-2 ring-blue-500':''}`}>
                <div className="flex flex-col sm:flex-row justify-between gap-4">
                  <div className="flex gap-4">
                    <div className="p-3 rounded-2xl h-fit shrink-0" style={{ background:`${color}15`, color }}>
                      <Siren className="h-6 w-6"/>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-bold text-lg text-slate-800 dark:text-slate-100">{alert.anomaly_type}</h4>
                        <span className="badge text-[10px]" style={{ background:`${color}18`, color }}>{alert.priority_level}</span>
                        {alert.immediate_action_required && (
                          <span className="badge bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-[10px]">
                            <Zap className="h-2.5 w-2.5 mr-0.5"/> Urgent
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500 mb-3">
                        <div className="flex items-center gap-1 font-bold">
                          <MapPin className="h-3.5 w-3.5 text-blue-500"/>{alert.pipe_id}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5"/>{new Date(alert.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-6">
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Anomaly Score</div>
                          <div className="text-xl font-mono font-black" style={{ color }}>{(alert.anomaly_score*100).toFixed(0)}%</div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Fail Probability</div>
                          <div className="text-xl font-mono font-black text-slate-700 dark:text-slate-200">{(alert.failure_probability*100).toFixed(0)}%</div>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">Flow Rate</div>
                          <div className="text-xl font-mono font-black text-blue-500">{alert.flow_rate.toFixed(1)}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col justify-between items-start sm:items-end gap-3">
                    <span className="text-[10px] font-mono font-bold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                      #{alert.alert_id.slice(0,8)}
                    </span>
                    <button onClick={e=>{e.stopPropagation();onSelectAlert(alert.alert_id);}}
                      className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl font-bold text-sm shadow-lg shadow-blue-500/20 transition-all active:scale-95">
                      Analyze Impact <ChevronRight className="h-4 w-4"/>
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          }) : (
            <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} className="glass-card rounded-3xl p-16 flex flex-col items-center text-center">
              <CheckCircle2 className="h-16 w-16 text-green-500 mb-4"/>
              <h3 className="text-xl font-bold text-slate-700 dark:text-slate-200">All Clear</h3>
              <p className="text-slate-400 mt-2 text-sm">No alerts matching the current filter</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
