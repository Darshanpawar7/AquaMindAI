import React from 'react';
import { motion } from 'framer-motion';
import { Droplets, AlertTriangle, Activity, Zap, TrendingUp, TrendingDown, ChevronRight } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, AreaChart, Area } from 'recharts';
import { Alert, Pipe } from '../api';

const P_COLORS: Record<string, string> = { Critical:'#dc2626', High:'#ea580c', Medium:'#ca8a04', Low:'#16a34a' };
const TT = { contentStyle:{ backgroundColor:'#0f172a', border:'none', borderRadius:10, color:'#fff', fontSize:12 } };

interface Props { alerts: Alert[]; pipes: Pipe[]; onSelectAlert:(id:string)=>void; }

function StatCard({ title, value, sub, icon:Icon, color, trend }:{ title:string; value:string; sub:string; icon:React.ElementType; color:string; trend:'up'|'down' }) {
  return (
    <motion.div whileHover={{ scale:1.02, y:-2 }} transition={{ type:'spring', stiffness:300 }} className="stat-card glass-card">
      <div className="absolute top-0 right-0 h-20 w-20 translate-x-6 -translate-y-6 rounded-full opacity-10 blur-2xl" style={{ background:color }} />
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">{title}</p>
          <h3 className="text-2xl font-black tracking-tight text-slate-800 dark:text-slate-100">{value}</h3>
          <div className="flex items-center mt-1.5 gap-1">
            {trend==='up' ? <TrendingUp className="h-3.5 w-3.5 text-green-500"/> : <TrendingDown className="h-3.5 w-3.5 text-red-500"/>}
            <span className={`text-xs font-bold ${trend==='up'?'text-green-500':'text-red-500'}`}>{sub}</span>
          </div>
        </div>
        <div className="p-2.5 rounded-xl" style={{ background:`${color}18` }}><Icon className="h-5 w-5" style={{ color }} /></div>
      </div>
    </motion.div>
  );
}

export function DashboardView({ alerts, pipes, onSelectAlert }: Props) {
  const criticalCount = alerts.filter(a => a.priority_level==='Critical').length;
  const highCount     = alerts.filter(a => a.priority_level==='High').length;
  const avgScore      = alerts.length > 0 ? (alerts.reduce((s,a)=>s+a.anomaly_score,0)/alerts.length).toFixed(2) : '—';
  const priorityData  = ['Critical','High','Medium','Low'].map(p=>({ name:p, count:alerts.filter(a=>a.priority_level===p).length, color:P_COLORS[p] }));
  const trendData     = [...alerts].sort((a,b)=>new Date(a.timestamp).getTime()-new Date(b.timestamp).getTime()).slice(-14).map(a=>({
    time: new Date(a.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),
    score: parseFloat(a.anomaly_score.toFixed(2)),
    prob:  parseFloat((a.failure_probability*100).toFixed(1)),
  }));
  const recent = [...alerts].sort((a,b)=>new Date(b.timestamp).getTime()-new Date(a.timestamp).getTime()).slice(0,8);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Alerts"    value={String(alerts.length)} sub={`${criticalCount} critical`} icon={AlertTriangle} color="#dc2626" trend={criticalCount>0?'down':'up'} />
        <StatCard title="Pipes Monitored" value={String(pipes.length)}  sub="All active"                  icon={Droplets}      color="#2563eb" trend="up" />
        <StatCard title="Avg Anomaly"     value={avgScore}              sub="Lower is better"             icon={Activity}      color="#7c3aed" trend="up" />
        <StatCard title="High Priority"   value={String(highCount+criticalCount)} sub="Need attention"    icon={Zap}           color="#ea580c" trend={highCount+criticalCount>0?'down':'up'} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card rounded-2xl p-5">
          <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-4">Anomaly Score Trend</h4>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="gScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false}/>
                <XAxis dataKey="time" tick={{fontSize:10,fill:'#64748b'}} tickLine={false}/>
                <YAxis tick={{fontSize:10,fill:'#64748b'}} tickLine={false} domain={[0,1]}/>
                <Tooltip {...TT}/>
                <Area type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={2.5} fill="url(#gScore)" name="Anomaly Score"/>
                <Line type="monotone" dataKey="prob" stroke="#7c3aed" strokeWidth={2} dot={false} name="Fail Prob %" strokeDasharray="4 2"/>
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-slate-400 text-sm flex-col gap-2">
              <span>No data yet</span>
              <code className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-xs">python simulator/seed_local.py</code>
            </div>
          )}
        </div>
        <div className="glass-card rounded-2xl p-5">
          <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-4">Priority Distribution</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={priorityData} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false}/>
              <XAxis dataKey="name" tick={{fontSize:10,fill:'#64748b'}} tickLine={false}/>
              <YAxis tick={{fontSize:10,fill:'#64748b'}} tickLine={false} allowDecimals={false}/>
              <Tooltip {...TT}/>
              <Bar dataKey="count" radius={[6,6,0,0]}>{priorityData.map(e=><Cell key={e.name} fill={e.color}/>)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200">Recent Alerts</h4>
          <span className="text-xs text-slate-400">{alerts.length} total</span>
        </div>
        {recent.length === 0 ? (
          <div className="text-center text-slate-400 text-sm py-8">No alerts yet — seed the backend</div>
        ) : (
          <div className="space-y-2">
            {recent.map(alert => {
              const color = P_COLORS[alert.priority_level] ?? '#6b7280';
              return (
                <motion.div key={alert.alert_id} whileHover={{ x:4 }} onClick={()=>onSelectAlert(alert.alert_id)}
                  className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:bg-blue-50 dark:hover:bg-slate-800 cursor-pointer transition-colors border border-transparent hover:border-blue-200 dark:hover:border-blue-800">
                  <div className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background:color, boxShadow:`0 0 6px ${color}` }}/>
                  <span className="badge shrink-0 text-[10px]" style={{ background:`${color}18`, color }}>{alert.priority_level}</span>
                  <span className="text-sm font-bold text-slate-700 dark:text-slate-200 shrink-0">{alert.pipe_id}</span>
                  <span className="text-xs text-slate-500 truncate flex-1">{alert.anomaly_type}</span>
                  <span className="text-xs font-mono text-slate-400 shrink-0">{new Date(alert.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</span>
                  {alert.immediate_action_required && <span className="badge bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 shrink-0 text-[10px]">⚡ Urgent</span>}
                  <ChevronRight className="h-4 w-4 text-slate-300 shrink-0"/>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
