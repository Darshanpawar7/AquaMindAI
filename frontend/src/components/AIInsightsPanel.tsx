import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, Sparkles, ChevronUp, ChevronDown, X, AlertCircle } from 'lucide-react';
import { Alert, Pipe } from '../api';

interface Props { alerts: Alert[]; pipes: Pipe[]; }

export function AIInsightsPanel({ alerts, pipes }: Props) {
  const [open, setOpen] = useState(false);

  const criticalAlerts = alerts.filter(a => a.priority_level === 'Critical');
  const highAlerts     = alerts.filter(a => a.priority_level === 'High');
  const avgScore       = alerts.length ? (alerts.reduce((s,a)=>s+a.anomaly_score,0)/alerts.length) : 0;
  const oldPipes       = pipes.filter(p => p.age_years > 20);

  const insights = [
    criticalAlerts.length > 0
      ? `⚠ ${criticalAlerts.length} critical anomaly${criticalAlerts.length>1?'s':''} detected on ${[...new Set(criticalAlerts.map(a=>a.pipe_id))].slice(0,3).join(', ')}. Immediate inspection recommended.`
      : '✓ No critical anomalies detected. System operating normally.',
    highAlerts.length > 0
      ? `🔶 ${highAlerts.length} high-priority alert${highAlerts.length>1?'s':''} require attention within 24 hours.`
      : '✓ No high-priority alerts pending.',
    avgScore > 0.6
      ? `📊 Average anomaly score is elevated at ${(avgScore*100).toFixed(0)}%. Consider increasing monitoring frequency.`
      : `📊 Average anomaly score is ${(avgScore*100).toFixed(0)}% — within acceptable range.`,
    oldPipes.length > 0
      ? `🔧 ${oldPipes.length} pipe${oldPipes.length>1?'s':''} are over 20 years old and may require proactive replacement.`
      : '✓ All pipes within acceptable age range.',
  ];

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity:0, y:40, scale:0.92 }}
            animate={{ opacity:1, y:0, scale:1 }}
            exit={{ opacity:0, y:40, scale:0.92 }}
            transition={{ type:'spring', stiffness:300, damping:25 }}
            className="mb-4 w-80 md:w-96 rounded-3xl shadow-2xl overflow-hidden border border-blue-500/20"
            style={{ background:'rgba(15,23,42,0.97)', backdropFilter:'blur(16px)' }}
          >
            <div className="p-4 bg-gradient-to-r from-blue-600 to-indigo-600 flex justify-between items-center">
              <div className="flex items-center gap-2 text-white">
                <Sparkles className="h-4 w-4"/>
                <span className="font-bold text-sm">AI Grid Insights</span>
              </div>
              <button onClick={()=>setOpen(false)} className="p-1 hover:bg-white/20 rounded-lg transition-colors text-white">
                <X className="h-4 w-4"/>
              </button>
            </div>
            <div className="p-5 space-y-3 max-h-80 overflow-y-auto">
              {insights.map((insight, i) => (
                <motion.div key={i} initial={{ opacity:0, x:-10 }} animate={{ opacity:1, x:0 }} transition={{ delay:i*0.08 }}
                  className="flex gap-3 p-3 rounded-2xl bg-white/5 border border-white/10">
                  <div className="text-sm text-slate-300 leading-relaxed">{insight}</div>
                </motion.div>
              ))}
              <div className="flex items-start gap-2 p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 mt-2">
                <AlertCircle className="h-4 w-4 text-blue-400 shrink-0 mt-0.5"/>
                <p className="text-[11px] text-blue-300 leading-relaxed font-medium">
                  Insights generated from {alerts.length} alerts across {pipes.length} monitored pipes.
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale:1.05 }} whileTap={{ scale:0.95 }}
        onClick={()=>setOpen(!open)}
        className="flex items-center gap-3 px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-2xl shadow-blue-500/30 transition-colors ring-4 ring-blue-500/20"
      >
        <BrainCircuit className="h-5 w-5"/>
        <span className="font-bold text-sm">AI Insights</span>
        {open ? <ChevronDown className="h-4 w-4"/> : <ChevronUp className="h-4 w-4"/>}
        {alerts.filter(a=>a.priority_level==='Critical').length > 0 && (
          <span className="h-2 w-2 rounded-full bg-red-400 animate-pulse"/>
        )}
      </motion.button>
    </div>
  );
}
