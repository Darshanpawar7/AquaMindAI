import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';

interface SensorGraphProps {
  pipeId: string | null;
}

interface DataPoint {
  time: string;
  flow_rate: number;
  pressure: number;
}

function mockReadings(pipeId: string): DataPoint[] {
  const points: DataPoint[] = [];
  const now = Date.now();
  for (let i = 23; i >= 0; i--) {
    const seed = pipeId.charCodeAt(pipeId.length - 1) + i;
    points.push({
      time: new Date(now - i * 3600 * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      flow_rate: parseFloat((10 + Math.sin(seed) * 3 + Math.random() * 0.5).toFixed(2)),
      pressure: parseFloat((45 + Math.cos(seed) * 5 + Math.random() * 0.5).toFixed(2)),
    });
  }
  return points;
}

export function SensorGraph({ pipeId }: SensorGraphProps) {
  const [data, setData] = useState<DataPoint[]>([]);

  useEffect(() => {
    if (!pipeId) { setData([]); return; }
    setData(mockReadings(pipeId));
  }, [pipeId]);

  if (!pipeId) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
        Select an alert or pipe to view sensor history
      </div>
    );
  }

  const tooltipStyle = { backgroundColor: '#0f172a', border: 'none', borderRadius: 10, color: '#fff', fontSize: 12 };

  return (
    <div className="space-y-6">
      <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
        <Activity className="h-4 w-4 text-blue-500" />
        Sensor History — <span className="text-blue-500">{pipeId}</span>
        <span className="text-xs text-slate-400 font-normal ml-1">last 24h</span>
      </h3>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Flow Rate (m³/h)</p>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Line type="monotone" dataKey="flow_rate" stroke="#2563eb" strokeWidth={2.5} dot={false} name="Flow Rate" />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}>
        <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Pressure (psi)</p>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <ReferenceLine y={30} stroke="#dc2626" strokeDasharray="4 2" label={{ value: 'Min', fill: '#dc2626', fontSize: 10 }} />
            <Line type="monotone" dataKey="pressure" stroke="#7c3aed" strokeWidth={2.5} dot={false} name="Pressure" />
          </LineChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
}
