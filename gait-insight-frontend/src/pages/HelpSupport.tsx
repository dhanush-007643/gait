import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Upload, Activity, BarChart2, Mail, HelpCircle } from 'lucide-react';
import Layout from '../components/layout/Layout';

const FAQS = [
  { q: 'What is GaitInsight?', a: 'GaitInsight is a research/educational software platform that analyses human walking patterns from wearable IMU sensor data using machine learning. It is a B.Tech Biotechnology capstone project focused on Human Anatomy and Physiology.' },
  { q: 'What gait classes does it detect?', a: 'The system classifies gait into 6 categories: Normal, Parkinsonian, Hemiplegic, Ataxic, Spastic, and Antalgic. Each class represents a distinct walking pattern associated with different neurological or musculoskeletal conditions.' },
  { q: 'What CSV format is required?', a: 'Your CSV must contain columns: timestamp, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z. Timestamps should be sequential and sensor values should be numeric.' },
  { q: 'What machine learning algorithm is used?', a: 'The backend uses a Random Forest Classifier trained with scikit-learn. Features extracted include cadence, walking speed, step length, stride length, step time, stride time, stance time, swing time, gait symmetry, and sensor statistics.' },
  { q: 'Is this a medical diagnostic tool?', a: 'No. GaitInsight is a research/educational prototype and is NOT a medical diagnostic device. It should not replace assessment by a qualified healthcare professional.' },
  { q: 'What is Demo Mode?', a: 'Demo Mode (VITE_USE_MOCK=true) uses synthetic, computer-generated data for all visualisations. No real patient data is used. A banner is displayed whenever synthetic data is active.' },
];

const WORKFLOW = [
  { icon: <Upload className="w-5 h-5" />, label: 'Sensor / CSV Data', desc: 'Upload raw IMU sensor recordings (acc + gyro)' },
  { icon: <Activity className="w-5 h-5" />, label: 'Preprocessing', desc: 'Noise filtering, magnitude computation, windowing' },
  { icon: <BarChart2 className="w-5 h-5" />, label: 'Feature Extraction', desc: '16+ biomechanical gait parameters computed' },
  { icon: <HelpCircle className="w-5 h-5" />, label: 'Machine Learning', desc: 'Random Forest classifies into 6 gait classes' },
  { icon: <Activity className="w-5 h-5" />, label: 'Gait Classification', desc: 'Prediction + confidence score returned' },
  { icon: <BarChart2 className="w-5 h-5" />, label: 'Report', desc: 'Full report with charts, parameters, and probability scores' },
];

function Accordion({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 text-left font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        aria-expanded={open}>
        {q}
        {open ? <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-400 flex-shrink-0" />}
      </button>
      {open && <div className="px-5 pb-4 text-sm text-slate-600 leading-relaxed border-t border-slate-100">{a}</div>}
    </div>
  );
}

export default function HelpSupport() {
  return (
    <Layout title="Help & Support" subtitle="Documentation, FAQs, and contact information">
      <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* FAQ */}
          <div className="card p-6">
            <h2 className="font-semibold text-slate-800 mb-4">Frequently Asked Questions</h2>
            <div className="space-y-2">
              {FAQS.map((f, i) => <Accordion key={i} q={f.q} a={f.a} />)}
            </div>
          </div>

          {/* Workflow */}
          <div className="card p-6">
            <h2 className="font-semibold text-slate-800 mb-5">How Gait Analysis Works</h2>
            <div className="relative">
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-100" />
              <div className="space-y-6">
                {WORKFLOW.map((step, i) => (
                  <div key={i} className="flex items-start gap-4 relative">
                    <div className="w-12 h-12 rounded-full bg-primary-600 flex items-center justify-center text-white flex-shrink-0 z-10">
                      {step.icon}
                    </div>
                    <div className="pt-2">
                      <p className="font-semibold text-slate-700">{step.label}</p>
                      <p className="text-sm text-slate-500 mt-0.5">{step.desc}</p>
                    </div>
                    {i < WORKFLOW.length - 1 && (
                      <ChevronDown className="absolute left-4 bottom-[-28px] w-4 h-4 text-slate-300" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card p-5">
            <h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <Mail className="w-4 h-4 text-primary-500" /> Contact Support
            </h3>
            <p className="text-sm text-slate-600 mb-3">For research queries or technical issues:</p>
            <p className="text-sm font-medium text-primary-600">support@gaitinsight.dev</p>
            <hr className="my-4 border-slate-100" />
            <p className="text-xs text-slate-500 leading-relaxed">
              This is an academic research prototype. Response times may vary during academic periods.
            </p>
          </div>
          <div className="card p-5 bg-amber-50 border-amber-200">
            <p className="text-xs text-amber-700 font-semibold mb-1">Medical Disclaimer</p>
            <p className="text-xs text-amber-600 leading-relaxed">
              This application is a research/educational prototype for gait pattern analysis.
              It is not a medical diagnostic device and should not replace assessment by a qualified healthcare professional.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
