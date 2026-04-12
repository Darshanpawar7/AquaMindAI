import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, GitBranch, AlertTriangle, BarChart3, Zap,
  Bell, Sun, Moon, Menu, X, Waves, User, RefreshCw,
} from 'lucide-react';
import { Pipe, SimulationResult, getPipes } from './api';
import { useAlerts } from './hooks/useAlerts';
import { DashboardView } from './components/DashboardView';
import { PipeNetworkView } from './components/PipeNetworkView';
import { AlertsView } from './components/AlertsView';
import { AnalyticsView } from './components/AnalyticsView';
import { SimulateView } from './components/SimulateView';
import { AIInsightsPanel } from './components/AIInsightsPanel';

export type Tab = 'dashboard' | 'map' | 'alerts' | 'analytics' | 'simulate';

const NAV: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: 'Command Center', icon: LayoutDashboard },
  { id: 'map',       label: 'Pipe Network',   icon: GitBranch },
  { id: 'alerts',    label: 'Live Alerts',    icon: AlertTriangle },
  { id: 'analytics', label: 'Analytics',      icon: BarChart3 },
  { id: 'simulate',  label: 'Impact & AI',    icon: Zap },
];

const P_COLORS: Record<string, string> = {
  Critical: '#ef4444', High: '#f97316', Medium: '#eab308', Low: '#22c55e',
};

export default function App() {
  const { alerts, loading: alertsLoading, error: alertsError, refresh } = useAlerts(30000);
  const [pipes, setPipes]           = useState<Pipe[]>([]);
  const [pipesError, setPipesError] = useState<string | null>(null);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [activeTab, setActiveTab]   = useState<Tab>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode]     = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  useEffect(() => {
    getPipes()
      .then(setPipes)
      .catch((e) => setPipesError(e instanceof Error ? e.message : 'Failed to load pipes'));
  }, []);

  const selectedAlert = alerts.find((a) => a.alert_id === selectedAlertId) ?? null;
  const criticalCount = alerts.filter((a) => a.priority_level === 'Critical').length;
  const globalError   = alertsError || pipesError;

  function selectAlert(id: string, tab: Tab = 'simulate') {
    setSelectedAlertId(id);
    setSimulationResult(null);
    setActiveTab(tab);
  }

  const tickerItems = [...alerts]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 12);

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-[#060b14] text-slate-100 transition-colors duration-300">

        {/* Sidebar */}
        <aside className={`fixed left-0 top-0 z-50 h-full w-60 flex flex-col bg-[#080e1a] border-r border-white/[0.06] transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
          <div className="flex items-center gap-3 h-16 px-5 border-b border-white/[0.06] shrink-0">
            <div className="relative h-9 w-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
              <Waves className="h-4 w-4 text-white" />
              <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-green-400 border-2 border-[#080e1a] animate-pulse" />
            </div>
            <div>
              <div className="text-sm font-black tracking-tight bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent leading-none">AquaMind AI</div>
              <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-0.5">Smart Water Platform</div>
            </div>
          </div>

          <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
            <div className="text-[9px] font-bold text-slate-600 uppercase tracking-widest px-3 py-2 mt-1">Navigation</div>
            {NAV.map((item) => (
              <button key={item.id} onClick={() => setActiveTab(item.id)}
                className={`nav-btn ${activeTab === item.id ? 'nav-btn-active' : 'nav-btn-inactive'}`}>
                <item.icon className="h-4 w-4 shrink-0" />
                <span className="flex-1">{item.label}</span>
                {item.id === 'alerts' && criticalCount > 0 && (
                  <span className="ml-auto text-[9px] font-black px-1.5 py-0.5 rounded-md bg-red-500/20 text-red-400 border border-red-500/30">{criticalCount}</span>
                )}
              </button>
            ))}
          </nav>

          <div className="shrink-0 p-3 border-t border-white/[0.06] space-y-2">
            <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-3 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">System Status</span>
                <span className="flex items-center gap-1 text-[9px] font-bold text-green-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse inline-block" />LIVE
                </span>
              </div>
              {([['Pipes', pipes.length, '#06b6d4'], ['Alerts', alerts.length, '#a78bfa'], ['Critical', criticalCount, '#ef4444']] as [string, number, string][]).map(([k, v, c]) => (
                <div key={k} className="flex justify-between items-center">
                  <span className="text-slate-500">{k}</span>
                  <span className="font-mono font-bold text-xs" style={{ color: c }}>{v}</span>
                </div>
              ))}
            </div>
            <button onClick={() => setDarkMode(!darkMode)}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] transition-all">
              {darkMode ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
              {darkMode ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className={`transition-all duration-300 min-h-screen flex flex-col ${sidebarOpen ? 'pl-60' : 'pl-0'}`}>

          {/* Header */}
          <header className="sticky top-0 z-40 flex h-14 items-center justify-between px-5 bg-[#080e1a]/90 backdrop-blur-xl border-b border-white/[0.06] shrink-0">
            <div className="flex items-center gap-3">
              <button onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1.5 rounded-lg hover:bg-white/[0.08] transition-colors text-slate-400 hover:text-slate-200">
                {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <div className="hidden sm:block">
                <div className="text-xs font-bold text-slate-200 leading-tight">Smart Water Infrastructure</div>
                <div className="text-[9px] text-slate-500 uppercase tracking-widest font-bold">Real-time AI Monitoring</div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {globalError && (
                <span className="hidden md:flex items-center gap-1.5 text-[10px] text-red-400 font-medium bg-red-500/10 px-2.5 py-1 rounded-lg border border-red-500/20">
                  ⚠ {globalError}
                </span>
              )}
              <button onClick={refresh}
                className={`p-1.5 rounded-lg hover:bg-white/[0.08] transition-colors text-slate-400 hover:text-cyan-400 ${alertsLoading ? 'animate-spin' : ''}`}>
                <RefreshCw className="h-4 w-4" />
              </button>
              <div className="relative cursor-pointer p-1.5">
                <Bell className="h-4 w-4 text-slate-400" />
                {criticalCount > 0 && (
                  <span className="absolute top-0.5 right-0.5 h-3.5 w-3.5 flex items-center justify-center rounded-full bg-red-500 text-[8px] text-white font-bold ring-2 ring-[#080e1a]">
                    {criticalCount}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 pl-2 border-l border-white/[0.08]">
                <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center">
                  <User className="h-3.5 w-3.5 text-white" />
                </div>
                <div className="hidden md:block">
                  <div className="text-[10px] font-bold leading-none text-slate-200">Admin</div>
                  <div className="text-[9px] text-slate-500">Command Center</div>
                </div>
              </div>
            </div>
          </header>

          {/* Live ticker */}
          {tickerItems.length > 0 && (
            <div className="flex items-center h-8 bg-[#0a1020] border-b border-white/[0.04] overflow-hidden shrink-0">
              <div className="shrink-0 flex items-center gap-2 px-3 h-full bg-cyan-500/10 border-r border-cyan-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-[9px] font-black text-cyan-400 uppercase tracking-widest whitespace-nowrap">Live Feed</span>
              </div>
              <div className="flex-1 overflow-hidden">
                <div className="ticker-track flex gap-8 whitespace-nowrap text-[10px] text-slate-400 font-medium py-2 px-4">
                  {[...tickerItems, ...tickerItems].map((a, i) => (
                    <span key={i} className="flex items-center gap-2 cursor-pointer hover:text-cyan-400 transition-colors"
                      onClick={() => selectAlert(a.alert_id, 'alerts')}>
                      <span className="h-1.5 w-1.5 rounded-full shrink-0" style={{ background: P_COLORS[a.priority_level] }} />
                      <span className="font-bold" style={{ color: P_COLORS[a.priority_level] }}>{a.priority_level}</span>
                      <span>{a.pipe_id}</span>
                      <span className="text-slate-600">—</span>
                      <span>{a.anomaly_type}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 p-5 pb-24 overflow-auto">
            <AnimatePresence mode="wait">
              <motion.div key={activeTab}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.16, ease: 'easeOut' }}>
                {activeTab === 'dashboard' && (
                  <DashboardView alerts={alerts} pipes={pipes} onSelectAlert={(id: string) => selectAlert(id, 'simulate')} />
                )}
                {activeTab === 'map' && (
                  <PipeNetworkView pipes={pipes} alerts={alerts}
                    selectedAlertId={selectedAlertId}
                    onSelectAlert={(id: string) => selectAlert(id, 'simulate')} />
                )}
                {activeTab === 'alerts' && (
                  <AlertsView alerts={alerts} selectedAlertId={selectedAlertId}
                    onSelectAlert={(id: string) => selectAlert(id, 'simulate')} error={alertsError} />
                )}
                {activeTab === 'analytics' && (
                  <AnalyticsView alerts={alerts} pipes={pipes} />
                )}
                {activeTab === 'simulate' && (
                  <SimulateView selectedAlert={selectedAlert}
                    simulationResult={simulationResult}
                    onSimulationComplete={setSimulationResult} />
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>

        <AIInsightsPanel alerts={alerts} pipes={pipes} />
      </div>
    </div>
  );
}
