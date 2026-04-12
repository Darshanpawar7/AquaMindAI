import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, TrendingDown, TrendingUp, Loader2, Cpu, AlertCircle, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Alert, SimulationResult, RecommendationResult, runWhatIf, runExplain } from '../api';

const TT = { contentStyle:{ backgroundColor:'#0f172a', border:'none', borderRadius:10, color:'#fff', fontSize:12 } };

function mockReadings(pipeId: string) {
  const now = Date.now();
  return Array.from({length:24},(_,i)=>{
    const seed = pipeId.charCodeAt(pipeId.length-1)+i;
    return {
      time: new Date(now-(23-i)*3600000).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),
      flow: parseFloat((10+Math.sin(seed)*3+Math.random()*0.5).toFixed(2)),
      psi:  parseFloat((45+Math.cos(seed)*5+Math.random()*0.5).toFixed(2)),
    };
  });
}

interface Props { selectedAlert:Alert|null; simulationResult:SimulationResult|null; onSimulationComplete:(r:SimulationResult)=>void; }

export function SimulateView({ selectedAlert, simulationResult, onSimulationComplete }: Props) {
  const [simLoading, setSimLoading]   = useState(false);
  const [simError, setSimError]       = useState<string|null>(null);
  const [rec, setRec]                 = useState<RecommendationResult|null>(null);
  const [recLoading, setRecLoading]   = useState(false);
  const [recError, setRecError]       = useState<string|null>(null);
  const [sensorData, setSensorData]   = useState<{time:string;flow:number;psi:number}[]>([]);

  useEffect(()=>{
    if (selectedAlert) setSensorData(mockReadings(selectedAlert.pipe_id));
    else setSensorData([]);
  },[selectedAlert]);

  useEffect(()=>{
    if (!selectedAlert||!simulationResult) { setRec(null); setRecError(null); return; }
    setRecLoading(true); setRecError(null);
    runExplain({ alert_id: selectedAlert.alert_id, pipe_id:selectedAlert.pipe_id, loss_rate:selectedAlert.flow_rate, population_affected:1000, repair_cost:simulationResult.repair_scenario.repair_cost_usd, time_horizon_days:30 })
      .then(setRec).catch(e=>setRecError(e instanceof Error?e.message:'Failed')).finally(()=>setRecLoading(false));
  },[selectedAlert,simulationResult]);

  async function handleAnalyze() {
    if (!selectedAlert) return;
    setSimLoading(true); setSimError(null);
    try {
      const r = await runWhatIf({ alert_id:selectedAlert.alert_id, leak_rate:selectedAlert.flow_rate, population_affected:1000, repair_cost:5000, time_horizon_days:30 });
      onSimulationComplete(r);
    } catch(e) { setSimError(e instanceof Error?e.message:'Simulation failed'); }
    finally { setSimLoading(false); }
  }

  if (!selectedAlert) return (
    <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
      <Zap className="h-12 w-12 opacity-20"/>
      <p className="text-base font-medium">Select an alert from the Alerts tab to run impact simulation</p>
    </div>
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-black tracking-tight text-slate-800 dark:text-slate-100">Impact & AI Analysis</h2>
        <p className="text-slate-500 text-sm font-medium">Pipe: <span className="font-bold text-blue-500">{selectedAlert.pipe_id}</span> — {selectedAlert.anomaly_type}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sensor graph */}
        <div className="glass-card rounded-3xl p-6 space-y-5">
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-500"/> Sensor History — last 24h
          </h3>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Flow Rate (m³/h)</p>
            <ResponsiveContainer width="100%" height={130}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false}/>
                <XAxis dataKey="time" tick={{fontSize:9,fill:'#64748b'}} tickLine={false}/>
                <YAxis tick={{fontSize:9,fill:'#64748b'}} tickLine={false}/>
                <Tooltip {...TT}/>
                <Line type="monotone" dataKey="flow" stroke="#2563eb" strokeWidth={2.5} dot={false} name="Flow"/>
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Pressure (psi)</p>
            <ResponsiveContainer width="100%" height={130}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false}/>
                <XAxis dataKey="time" tick={{fontSize:9,fill:'#64748b'}} tickLine={false}/>
                <YAxis tick={{fontSize:9,fill:'#64748b'}} tickLine={false}/>
                <Tooltip {...TT}/>
                <ReferenceLine y={30} stroke="#dc2626" strokeDasharray="4 2" label={{value:'Min',fill:'#dc2626',fontSize:9}}/>
                <Line type="monotone" dataKey="psi" stroke="#7c3aed" strokeWidth={2.5} dot={false} name="Pressure"/>
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Impact simulator */}
        <div className="glass-card rounded-3xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
              <Zap className="h-4 w-4 text-orange-500"/> Impact Simulation
            </h3>
            <motion.button whileHover={{scale:1.03}} whileTap={{scale:0.97}} onClick={handleAnalyze} disabled={simLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors disabled:opacity-60 shadow-lg shadow-blue-500/20">
              {simLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin"/> : <Zap className="h-3.5 w-3.5"/>}
              {simLoading ? 'Analyzing…' : 'Run Analysis'}
            </motion.button>
          </div>
          {simError && <div role="alert" className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-xs text-red-700 dark:text-red-400">{simError}</div>}
          <AnimatePresence>
            {simulationResult && (
              <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-2xl bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/50 p-4">
                    <div className="flex items-center gap-2 mb-3"><TrendingDown className="h-4 w-4 text-red-500"/><span className="text-xs font-bold text-red-600 dark:text-red-400">Ignore</span></div>
                    <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                      <div className="flex justify-between"><span>Water loss</span><span className="font-bold font-mono">{simulationResult.ignore_scenario.total_water_loss_liters.toLocaleString()} L</span></div>
                      <div className="flex justify-between"><span>Cost</span><span className="font-bold font-mono">${simulationResult.ignore_scenario.financial_cost_usd.toLocaleString()}</span></div>
                      <div className="flex justify-between"><span>Damage</span><span className="font-bold font-mono">{simulationResult.ignore_scenario.infrastructure_damage_score.toFixed(3)}</span></div>
                    </div>
                  </div>
                  <div className="rounded-2xl bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800/50 p-4">
                    <div className="flex items-center gap-2 mb-3"><TrendingUp className="h-4 w-4 text-green-500"/><span className="text-xs font-bold text-green-600 dark:text-green-400">Repair</span></div>
                    <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                      <div className="flex justify-between"><span>Repair cost</span><span className="font-bold font-mono">${simulationResult.repair_scenario.repair_cost_usd.toLocaleString()}</span></div>
                      <div className="flex justify-between"><span>Water saved</span><span className="font-bold font-mono">{simulationResult.repair_scenario.water_loss_prevented_liters.toLocaleString()} L</span></div>
                      <div className="flex justify-between"><span>Net savings</span><span className="font-bold font-mono text-green-600">${simulationResult.savings_usd.toLocaleString()}</span></div>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800/50 px-4 py-3 text-xs text-blue-700 dark:text-blue-300">
                  <span className="font-bold">Recommendation: </span>{simulationResult.recommended_action}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          {!simulationResult && !simLoading && (
            <div className="flex flex-col items-center justify-center py-10 text-slate-400 text-sm gap-2">
              <Zap className="h-8 w-8 opacity-20"/>Click "Run Analysis" to simulate impact
            </div>
          )}
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="glass-card rounded-3xl p-6">
        <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2 mb-4">
          <Cpu className="h-4 w-4 text-purple-500"/> AI Recommendation
        </h3>
        {recLoading && <div className="flex items-center gap-2 text-slate-400 text-sm"><Loader2 className="h-4 w-4 animate-spin"/>Generating recommendation…</div>}
        {!recLoading && recError && (
          <div className="rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50 px-4 py-3 text-xs text-amber-700 dark:text-amber-400 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0"/>Recommendation unavailable in local mode (Bedrock not configured)
          </div>
        )}
        <AnimatePresence>
          {!recLoading && !recError && rec && (
            <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}
              className="rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 border border-blue-200 dark:border-blue-800/50 p-5 space-y-3">
              <div className="flex items-start gap-2">
                <span className="badge bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shrink-0">Action</span>
                <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{rec.recommended_action}</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed"><span className="font-bold">Urgency: </span>{rec.urgency_rationale}</p>
              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="rounded-xl bg-white/60 dark:bg-slate-800/60 p-3 text-center">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Net Savings</div>
                  <div className="text-xl font-black text-green-600">${rec.savings_usd.toLocaleString()}</div>
                </div>
                <div className="rounded-xl bg-white/60 dark:bg-slate-800/60 p-3 text-center">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Repair Cost</div>
                  <div className="text-xl font-black text-blue-600">${rec.repair_cost_usd.toLocaleString()}</div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        {!recLoading && !recError && !rec && !simulationResult && (
          <div className="text-center text-slate-400 text-sm py-6">Run impact simulation first to get AI recommendation</div>
        )}
      </div>
    </div>
  );
}
