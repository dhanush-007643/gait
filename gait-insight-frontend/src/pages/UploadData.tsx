import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2, ChevronRight } from 'lucide-react';
import Layout from '../components/layout/Layout';
import { uploadApi } from '../services/api';
import clsx from 'clsx';

const REQUIRED_COLS = ['timestamp','acc_x','acc_y','acc_z','gyro_x','gyro_y','gyro_z'];
const STEPS = ['Uploading','Processing','Feature Extraction','Classification','Complete'];

type StepStatus = 'pending'|'active'|'done'|'error';

export default function UploadData() {
  const navigate = useNavigate();
  const inputRef  = useRef<HTMLInputElement>(null);
  const [file, setFile]           = useState<File|null>(null);
  const [dragging, setDragging]   = useState(false);
  const [progress, setProgress]   = useState(0);
  const [step, setStep]           = useState(-1);
  const [sessionId, setSessionId] = useState('');
  const [error, setError]         = useState('');
  const [done, setDone]           = useState(false);

  const acceptFile = (f: File) => {
    if (!f.name.endsWith('.csv')) { setError('Only CSV files are supported.'); return; }
    setFile(f); setError(''); setStep(-1); setDone(false); setProgress(0); setSessionId('');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0]; if (f) acceptFile(f);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setError(''); setStep(0); setProgress(0); setDone(false);
    try {
      const result = await uploadApi.uploadCsv(file, pct => {
        setProgress(pct);
        if (pct >= 25) setStep(1);
        if (pct >= 50) setStep(2);
        if (pct >= 75) setStep(3);
        if (pct >= 100) setStep(4);
      });
      if (result.status === 'error') { setError(result.message); setStep(-1); return; }
      setSessionId(result.session_id);
      setDone(true);
    } catch (err: any) {
      const msg = err?.response?.data?.error || err?.response?.data?.detail || err?.message || 'Upload failed. Please try again.';
      setError(msg);
      setStep(-1);
    }
  };

  const getStepStatus = (i: number): StepStatus => {
    if (step < 0) return 'pending';
    if (i < step) return 'done';
    if (i === step) return 'active';
    return 'pending';
  };

  return (
    <Layout title="Upload Gait Data" subtitle="Upload CSV files containing accelerometer and gyroscope sensor data">
      <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload card */}
        <div className="lg:col-span-2 space-y-5">
          <div className="card p-6">
            <h2 className="font-semibold text-slate-800 mb-4">Upload Gait Sensor Data</h2>

            {/* Drop zone */}
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => !file && inputRef.current?.click()}
              className={clsx(
                'border-2 border-dashed rounded-xl p-10 flex flex-col items-center gap-4 transition-all cursor-pointer',
                dragging ? 'border-primary-400 bg-primary-50' : 'border-slate-200 hover:border-primary-300 hover:bg-slate-50',
                file && 'cursor-default'
              )}
            >
              <div className="w-14 h-14 rounded-full bg-primary-50 flex items-center justify-center">
                <Upload className="w-7 h-7 text-primary-500" />
              </div>
              <div className="text-center">
                <p className="font-semibold text-slate-700">Drag & Drop your CSV file here</p>
                <p className="text-slate-400 text-sm mt-1">or</p>
              </div>
              {!file && (
                <button type="button" onClick={() => inputRef.current?.click()} className="btn-primary">
                  Browse File
                </button>
              )}
              <p className="text-xs text-slate-400">Supported format: CSV only · Max size: 10 MB</p>
              <input ref={inputRef} type="file" accept=".csv" className="hidden"
                onChange={e => e.target.files?.[0] && acceptFile(e.target.files[0])} />
            </div>

            {/* File info */}
            {file && (
              <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white rounded-lg border border-slate-200 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-primary-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800 text-sm">{file.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <button onClick={() => { setFile(null); setStep(-1); setDone(false); setError(''); }}
                    className="text-slate-400 hover:text-slate-600 p-1" aria-label="Remove file">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
                <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
              </div>
            )}

            {/* Progress steps */}
            {step >= 0 && (
              <div className="mt-5">
                <p className="mb-2 text-right text-xs font-medium text-slate-500">{progress}% uploaded</p>
                <div className="flex items-center gap-2 mb-3">
                  {STEPS.map((label, i) => {
                    const status = getStepStatus(i);
                    return (
                      <React.Fragment key={label}>
                        <div className="flex flex-col items-center gap-1">
                          <div className={clsx('w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors',
                            status === 'done' && 'bg-green-500 text-white',
                            status === 'active' && 'bg-primary-600 text-white animate-pulse',
                            status === 'pending' && 'bg-slate-200 text-slate-400'
                          )}>
                            {status === 'done' ? '✓' : status === 'active' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : i + 1}
                          </div>
                          <p className="text-xs text-slate-500 text-center leading-tight w-16">{label}</p>
                        </div>
                        {i < STEPS.length - 1 && <div className={clsx('flex-1 h-0.5 mb-5 transition-colors', i < step ? 'bg-green-400' : 'bg-slate-200')} />}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Success */}
            {done && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="font-semibold text-green-700 text-sm">Analysis Complete!</p>
                    <p className="text-xs text-green-600">Session: {sessionId}</p>
                  </div>
                </div>
                <button onClick={() => navigate(`/sessions/${sessionId}`)} className="btn-primary text-xs py-1.5 px-3">
                  View Results <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Analyze button */}
            {file && !done && step < 0 && (
              <button onClick={handleAnalyze} className="btn-primary w-full justify-center mt-4 py-2.5">
                Analyze Gait Data
              </button>
            )}
          </div>
        </div>

        {/* Guidelines */}
        <div className="space-y-5">
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Required CSV Columns</h3>
            <ul className="space-y-2">
              {REQUIRED_COLS.map(col => (
                <li key={col} className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full bg-primary-400 flex-shrink-0" />
                  <code className="font-mono text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">{col}</code>
                </li>
              ))}
            </ul>
          </div>
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Upload Guidelines</h3>
            <ol className="space-y-2.5 text-xs text-slate-600 list-decimal list-inside">
              <li>Upload gait sensor data in CSV format.</li>
              <li>Ensure all required columns are present.</li>
              <li>Timestamps should be valid and sequential.</li>
              <li>Avoid missing sensor values (NaN).</li>
              <li>Recommended sampling rate: 50–200 Hz.</li>
            </ol>
          </div>
          <div className="card p-4 bg-amber-50 border-amber-200">
            <p className="text-xs text-amber-700 leading-relaxed">
              <strong>Research Use Only.</strong> This tool is for educational and research purposes.
              Do not upload identifiable personal health data.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
