import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Loader2, AlertCircle } from 'lucide-react';
import { Alert, SimulationResult, RecommendationResult, runExplain } from '../api';

interface RecommendationPanelProps {
  selectedAlert: Alert | null;
  simulationResult: SimulationResult | null;
}

export function RecommendationPanel({ selectedAlert, simulationResult }: RecommendationPanelProps) {
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedAlert || !simulationResult) {
      setRecommendation(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    runExplain({
      pipe_id: selectedAlert.pipe_id,
      loss_rate: selectedAlert.flow_rate,
      population_affected: 1000,
      repair_cost: simulationResult.repair_scenario.repair_cost_usd,
      time_horizon: 30,
    })
      .then(setRecommendation)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to fetch recommendation'))
      .finally(() => setLoading(false));
  }, [selectedAlert, simulationResult]);

  if (!selectedAlert) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400 text-sm gap-2">
        <Cpu className="h-8 w-8 opacity-30" />
        Run impact simulation to get AI recommendation
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
        <Cpu className="h-4 w-4 text-purple-500" />
        AI Recommendation
      </h3>

      {loading && (
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <Loader2 className="h-4 w-4 animate-spin" />
          Generating recommendation…
        </div>
      )}

      {!loading && error && (
        <div className="rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50 px-4 py-3 text-xs text-amber-700 dark:text-amber-400 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Recommendation unavailable (Bedrock not configured in local mode)
        </div>
      )}

      <AnimatePresence>
        {!loading && !error && recommendation && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 border border-blue-200 dark:border-blue-800/50 p-4 space-y-3"
          >
            <div className="flex items-start gap-2">
              <span className="badge bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 shrink-0">Action</span>
              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{recommendation.recommended_action}</span>
            </div>
            <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              <span className="font-bold text-slate-700 dark:text-slate-200">Urgency: </span>
              {recommendation.urgency_rationale}
            </div>
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div className="rounded-lg bg-white/60 dark:bg-slate-800/60 p-3 text-center">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Net Savings</div>
                <div className="text-lg font-black text-green-600">${recommendation.savings_usd.toLocaleString()}</div>
              </div>
              <div className="rounded-lg bg-white/60 dark:bg-slate-800/60 p-3 text-center">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Repair Cost</div>
                <div className="text-lg font-black text-blue-600">${recommendation.repair_cost_usd.toLocaleString()}</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
