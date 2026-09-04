import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Square, RotateCcw, Wifi, WifiOff, Activity, Footprints } from 'lucide-react';
import Layout from '../components/layout/Layout';
import SensorChart from '../components/ui/SensorChart';
import GaitBadge from '../components/ui/GaitBadge';
import ChartCard from '../components/ui/ChartCard';
import { generateSensorPoints } from '../data/mockData';
import type { SensorPoint, GaitClass } from '../types';

const SIMULATION_CLASS: GaitClass = 'normal';
const INTERVAL_MS = 50;
const CHUNK = 3;

export default function LiveMonitoring() {
  const [running, setRunning]     = useState(false);
  const [paused, setPaused]       = useState(false);
  const [data, setData]           = useState<SensorPoint[]>([]);
  const [stepCount, setStepCount] = useState(0);
  const [elapsed, setElapsed]     = useState(0);
  const [cadence, setCadence]     = useState(0);

  const allPoints = useRef<SensorPoint[]>(generateSensorPoints(500, SIMULATION_CLASS));
  const idxRef    = useRef(0);
  const timerRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const clockRef  = useRef<ReturnType<typeof setInterval> | null>(null);

  const start = () => {
    if (running && !paused) return;
    setRunning(true); setPaused(false);
    timerRef.current = setInterval(() => {
      const slice = allPoints.current.slice(idxRef.current, idxRef.current + CHUNK);
      idxRef.current = (idxRef.current + CHUNK) % allPoints.current.length;
      setData(prev => [...prev.slice(-150), ...slice]);
      setStepCount(v => v + (Math.random() > 0.94 ? 1 : 0));
    }, INTERVAL_MS);
    clockRef.current = setInterval(() => setElapsed(v => v + 1), 1000);
  };

  const pause = () => {
    setPaused(true);
    if (timerRef.current) clearInterval(timerRef.current);
    if (clockRef.current) clearInterval(clockRef.current);
  };

  const stop = () => {
    setRunning(false); setPaused(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (clockRef.current) clearInterval(clockRef.current);
  };

  const restart = () => {
    stop(); setData([]); setStepCount(0); setElapsed(0); idxRef.current = 0;
    allPoints.current = generateSensorPoints(500, SIMULATION_CLASS);
  };

  useEffect(() => {
    setCadence(elapsed > 0 ? Math.round((stepCount / elapsed) * 60) : 0);
  }, [stepCount, elapsed]);

  useEffect(() => () => { stop(); }, []);

  const fmtTime = (s: number) => `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;

  return (
    <Layout title="Live Monitoring" subtitle="Simulated real-time gait sensor data stream">
      {/* Simulation mode banner */}
      <div className="mb-5 flex items-center gap-3 p-3.5 bg-amber-50 border border-amber-200 rounded-xl">
        <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <Activity className="w-4 h-4 text-amber-600" />
        </div>
        <div>
          <p className="text-sm font-semibold text-amber-700">SIMULATION MODE</p>
          <p className="text-xs text-amber-600">
            This page simulates real-time sensor data for demonstration. No physical wearable device is connected.
            Data is synthetically generated.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Controls + status */}
        <div className="space-y-4">
          {/* Connection card */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Connection Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Sensor Link</span>
                <span className={`flex items-center gap-1.5 text-xs font-medium ${running ? 'text-green-600' : 'text-slate-400'}`}>
                  {running ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
                  {running ? 'Simulated' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Streaming</span>
                <span className={`flex items-center gap-1.5 text-xs font-medium ${running && !paused ? 'text-green-600' : 'text-slate-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${running && !paused ? 'bg-green-500 animate-pulse' : 'bg-slate-300'}`} />
                  {running && !paused ? 'Active' : paused ? 'Paused' : 'Stopped'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Elapsed</span>
                <span className="text-sm font-mono font-semibold text-slate-700">{fmtTime(elapsed)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Timestamp</span>
                <span className="text-xs text-slate-500">{new Date().toLocaleTimeString()}</span>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Controls</h3>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={start} disabled={running && !paused} className="btn-primary justify-center py-2">
                <Play className="w-4 h-4" /> {paused ? 'Resume' : 'Start'}
              </button>
              <button onClick={pause} disabled={!running || paused} className="btn-secondary justify-center py-2">
                <Pause className="w-4 h-4" /> Pause
              </button>
              <button onClick={stop} disabled={!running} className="btn-secondary justify-center py-2">
                <Square className="w-4 h-4" /> Stop
              </button>
              <button onClick={restart} className="btn-secondary justify-center py-2">
                <RotateCcw className="w-4 h-4" /> Restart
              </button>
            </div>
          </div>

          {/* Live metrics */}
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Live Metrics</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-1.5"><Footprints className="w-4 h-4 text-primary-400" /> Step Count</span>
                <span className="text-lg font-bold text-slate-800">{stepCount}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Cadence</span>
                <span className="text-sm font-semibold text-primary-600">{cadence} <span className="text-xs text-slate-400">steps/min</span></span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Est. Speed</span>
                <span className="text-sm font-semibold text-green-600">~1.35 <span className="text-xs text-slate-400">m/s</span></span>
              </div>
              <hr className="border-slate-100" />
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Gait Class</span>
                <GaitBadge gaitClass={SIMULATION_CLASS} size="sm" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Confidence</span>
                <span className="text-sm font-semibold text-slate-700">93.1%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="lg:col-span-2 space-y-5">
          <ChartCard title="Live Acceleration" subtitle="Accelerometer X, Y, Z axes (m/s²)">
            <SensorChart data={data} type="acceleration" height={200} />
            {!running && <div className="flex items-center justify-center h-20 text-slate-400 text-sm">Press Start to begin simulation</div>}
          </ChartCard>
          <ChartCard title="Live Gyroscope" subtitle="Angular velocity X, Y, Z axes (°/s)">
            <SensorChart data={data} type="gyroscope" height={200} />
          </ChartCard>
        </div>
      </div>
    </Layout>
  );
}
