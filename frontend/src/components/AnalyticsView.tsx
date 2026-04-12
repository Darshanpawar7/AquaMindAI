import React from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Cell } from 'recharts';
import { Alert, Pipe } from '../api';

const TT = { contentStyle:{ backgroundColor:'#0f172a', border:'none', borderRadius:12, color:'#fff', fontSize:12 }, labelStyle:{ fontWeight:'bold' } };

interface Props { alerts:Alert[]; pipes:Pipe[]; }

export function AnalyticsView({ alerts, pipes }: Props) {
  // Build hourly flow data from alerts
  const hourlyMap: Record<string,{ hour:string; alerts:number; avgScore:number; total:number }> = {};
  alerts.forEach(a=>{
    const h = new Date(a.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
    if (!hourlyMap[h]) hourlyMap[h] = { hour:h, alerts:0, avgScore:0, total:0 };
    hourlyMap[h].alerts++;
    hourlyMap[h].avgScore += a.anomaly_score;
    hourlyMap[h].total++;
  });
  const hourlyData = Object.values(hourlyMap).slice(-12).map(d=>({ ...d, avgScore:parseFloat((d.avgScore/d.total).toFixed(2)) }));

  // Pipe age distribution
  const ageGroups = [
    { name:'0-5y',  count:pipes.filter(p=>p.age_years<=5).length },
    { name:'6-15y', count:pipes.filter(p=>p.age_years>5&&p.age_years<=15).length },
    { name:'16-25y',count:pipes.filter(p=>p.age_years>15&&p.age_years<=25).length },
    { name:'25y+',  count:pipes.filter(p=>p.age_years>25).length },
  ];
  const ageColors = ['#16a34a','#ca8a04','#ea580c','#dc2626'];

  // Priority over time
  const priorityTrend = ['Critical','High','Medium','Low'].map(p=>({
    name:p, count:alerts.filter(a=>a.priority_level===p).length,
    color:{ Critical:'#dc2626', High:'#ea580c', Medium:'#ca8a04', Low:'#16a34a' }[p]??'#6b7280',
  }));

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-black tracking-tight text-slate-800 dark:text-slate-100">Analytics</h2>
        <p className="text-slate-500 text-sm font-medium">Infrastructure health & anomaly insights</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card rounded-3xl p-6">
          <h4 className="text-base font-bold text-slate-700 dark:text-slate-200 mb-6">Alert Frequency (by hour)</h4>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="gAlerts" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3}/>
              <XAxis dataKey="hour" stroke="#64748b" axisLine={false} tickLine={false} fontSize={10}/>
              <YAxis stroke="#64748b" axisLine={false} tickLine={false} fontSize={10} allowDecimals={false}/>
              <Tooltip {...TT}/>
              <Area type="monotone" dataKey="alerts" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#gAlerts)" name="Alerts"/>
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card rounded-3xl p-6">
          <h4 className="text-base font-bold text-slate-700 dark:text-slate-200 mb-6">Pipe Age Distribution</h4>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={ageGroups} barSize={36}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3}/>
              <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} fontSize={11}/>
              <YAxis stroke="#64748b" axisLine={false} tickLine={false} fontSize={11} allowDecimals={false}/>
              <Tooltip {...TT}/>
              <Bar dataKey="count" radius={[8,8,0,0]} name="Pipes">
                {ageGroups.map((_,i)=><Cell key={i} fill={ageColors[i]}/>)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card rounded-3xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h4 className="text-base font-bold text-slate-700 dark:text-slate-200">Anomaly Score Over Time</h4>
          <div className="flex gap-4">
            <span className="flex items-center gap-2 text-xs font-bold text-slate-500"><div className="h-2.5 w-2.5 rounded-full bg-blue-500"/>Score</span>
            <span className="flex items-center gap-2 text-xs font-bold text-slate-500"><div className="h-2.5 w-2.5 rounded-full bg-purple-500"/>Fail Prob</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={[...alerts].sort((a,b)=>new Date(a.timestamp).getTime()-new Date(b.timestamp).getTime()).slice(-20).map(a=>({
            time: new Date(a.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),
            score: parseFloat(a.anomaly_score.toFixed(2)),
            prob:  parseFloat((a.failure_probability*100).toFixed(1)),
          }))}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.3}/>
            <XAxis dataKey="time" stroke="#64748b" axisLine={false} tickLine={false} fontSize={10}/>
            <YAxis stroke="#64748b" axisLine={false} tickLine={false} fontSize={10}/>
            <Tooltip {...TT}/>
            <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2.5} dot={{ r:3, fill:'#3b82f6' }} name="Anomaly Score"/>
            <Line type="monotone" dataKey="prob"  stroke="#7c3aed" strokeWidth={2} dot={false} strokeDasharray="4 2" name="Fail Prob %"/>
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Pipe stats table */}
      <div className="glass-card rounded-3xl p-6">
        <h4 className="text-base font-bold text-slate-700 dark:text-slate-200 mb-4">Infrastructure Summary</h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label:'Total Pipes',    value:pipes.length,                                                                  color:'#2563eb' },
            { label:'Avg Age',        value:`${pipes.length?Math.round(pipes.reduce((s,p)=>s+p.age_years,0)/pipes.length):0}y`, color:'#7c3aed' },
            { label:'Avg Diameter',   value:`${pipes.length?Math.round(pipes.reduce((s,p)=>s+p.diameter_mm,0)/pipes.length):0}mm`, color:'#0891b2' },
            { label:'Pop. Served',    value:pipes.reduce((s,p)=>s+p.population_affected,0).toLocaleString(),               color:'#16a34a' },
          ].map(s=>(
            <div key={s.label} className="rounded-2xl bg-slate-50 dark:bg-slate-800/50 p-4 text-center border border-slate-100 dark:border-slate-700">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">{s.label}</div>
              <div className="text-2xl font-black" style={{ color:s.color }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
