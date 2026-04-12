import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, TrendingDown, TrendingUp, Loader2 } from 'lucide-react';
import { Alert, SimulationResult, runWhatIf } from '../api';

interface ImpactSimulatorProps {
  selectedAlert: Alert | null;
  onSimulationComplete: (result: SimulationResult) => void;
}

export function ImpactSimulator({ selectedAlert, onSimulationComplete }: ImpactSimulatorProps) {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    if (!selectedAlert) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runWhatIf({
        alert_id: selectedAlert.alert_id,
        leak_rate: selectedAlert.flow_rate,
        population_affected: 1000,
        repair_cost: 5000,
        time_horizon_days: 30,
      });
      setResult(res);
      onSimulationComplete(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Impact simulation failed');
    } finally {
      setLoading(false);
    }
  }

  if (!selectedAlert) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400 text-sm gap-2">
        <Zap className="h-8 w-8 opacity-30" />
        Select an alert to run impact simulation
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
          <Zap className="h-4 w-4 text-orange-500" />
          Impact Simulation — <span className="text-blue-500">{selectedAlert.pipe_id}</span>
        </h3>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={handleAnalyze}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-colors disabled:opacity-60 disabled:cursor-not-allowed shadow-lg shadow-blue-500/20"
        >
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
          {loading ? 'Analyzing…' : 'Analyze Impact'}
        </motion.button>
      </div>

      {error && (
        <div role="alert" className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-xs text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 gap-3"
          >
            <div className="rounded-xl bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800/50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="h-4 w-4 text-red-500" />
                <span className="text-xs font-bold text-red-600 dark:text-red-400">Ignore Scenario</span>
              </div>
              <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                <div className="flex justify-between">
                  <span>Water loss</span>
                  <span className="font-bold font-mono">{result.ignore_scenario.total_water_loss_liters.toLocaleString()} L</span>
                </div>
                <div className="flex justify-between">
                  <span>Financial cost</span>
                  <span className="font-bold font-mono">${result.ignore_scenario.financial_cost_usd.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Damage score</span>
                  <span className="font-bold font-mono">{result.ignore_scenario.infrastructure_damage_score.toFixed(3)}</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800/50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span className="text-xs font-bold text-green-600 dark:text-green-400">Repair Scenario</span>
              </div>
              <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                <div className="flex justify-between">
                  <span>Repair cost</span>
                  <span className="font-bold font-mono">${result.repair_scenario.repair_cost_usd.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Water saved</span>
                  <span className="font-bold font-mono">{result.repair_scenario.water_loss_prevented_liters.toLocaleString()} L</span>
                </div>
                <div className="flex justify-between">
                  <span>Net savings</span>
                  <span className="font-bold font-mono text-green-600">${result.savings_usd.toLocaleString()}</span>
                </div>
              </div>
            </div>

            <div className="col-span-2 rounded-xl bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800/50 px-4 py-3 text-xs text-blue-700 dark:text-blue-300">
              <span className="font-bold">Recommendation: </span>{result.recommended_action}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
