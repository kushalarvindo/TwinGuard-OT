import React, { useState } from 'react';
import { X, Compass, Zap, Layers, CheckCircle2 } from 'lucide-react';
import type { PageId } from '../App';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onNavigate?: (page: PageId) => void;
}

export default function OnboardingModal({ isOpen, onClose, onNavigate }: Props) {
  const [activeTab, setActiveTab] = useState<'tour' | 'workflow' | 'arch'>('tour');

  if (!isOpen) return null;

  const handleStart = (targetPage?: PageId) => {
    localStorage.setItem('twinguard_onboarding_completed', 'true');
    if (targetPage && onNavigate) {
      onNavigate(targetPage);
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container onboarding-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <div className="modal-category-chip">
              <span style={{ fontSize: 10 }}>🛡️</span>
              <span>ICS CYBERSECURITY PLATFORM</span>
            </div>
            <h2 className="modal-title">TwinGuard-OT: Process-Aware Digital Twin</h2>
            <p className="modal-desc">
              Welcome to the TwinGuard-OT industrial operations & cybersecurity operations center. 
              TwinGuard-OT pairs continuous hydrodynamic physical process simulation with virtual PLC control, 
              industrial Modbus TCP networking, controlled threat injection, and hybrid physics-ML anomaly detection.
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close Tour">
            <X size={18} />
          </button>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="modal-tabs">
          <button
            className={`modal-tab ${activeTab === 'tour' ? 'active' : ''}`}
            onClick={() => setActiveTab('tour')}
          >
            <Compass size={14} />
            🧭 Navigation Menu Tour (8 Core Modules)
          </button>
          <button
            className={`modal-tab ${activeTab === 'workflow' ? 'active' : ''}`}
            onClick={() => setActiveTab('workflow')}
          >
            <Zap size={14} />
            ⚡ 3-Step Guided Experiment Workflow
          </button>
          <button
            className={`modal-tab ${activeTab === 'arch' ? 'active' : ''}`}
            onClick={() => setActiveTab('arch')}
          >
            <Layers size={14} />
            📐 System Architecture & Modbus Map
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {activeTab === 'tour' && (
            <div className="onboarding-grid">
              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">🌊 1. Process SCADA Overview</span>
                  <span className="onboarding-tag cyan">Operations & HMI</span>
                </div>
                <p className="onboarding-card-desc">
                  Primary supervisory dashboard monitoring live water tank level, pump and valve states, and automated hysteresis control.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Interactive Rig:</strong> View animated dual-column water tanks comparing ground truth against reported sensor readings.
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">🔄 2. Digital Twin Shadow Model</span>
                  <span className="onboarding-tag indigo">Physics Reference</span>
                </div>
                <p className="onboarding-card-desc">
                  First-principles mass-balance differential equation solver running continuously in parallel with the live plant.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Key Metric:</strong> Physical Residual |r(t)| = |h_sensor - h_shadow| detects deception when PLC appears normal.
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">📡 3. Modbus Protocol Inspector</span>
                  <span className="onboarding-tag emerald">OT Network Forensics</span>
                </div>
                <p className="onboarding-card-desc">
                  Deep packet inspection of raw industrial Modbus TCP communication over localhost port 5020 (Unit ID 1).
                </p>
                <div className="onboarding-card-tip">
                  <strong>Forensics:</strong> Tracks Function Codes (FC03, FC06, FC16), transaction latency, and packet request rates (req/s).
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">🎯 4. Cyberattack Laboratory</span>
                  <span className="onboarding-tag rose">Red Team Injection</span>
                </div>
                <p className="onboarding-card-desc">
                  Isolated experimentation suite to safely execute 5 industrial cyberattacks against local simulation in real time.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Vectors:</strong> Sensor Spoofing, Unauthorized Write, Packet Replay, Command Flooding, Setpoint Manipulation.
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">🛡️ 5. Multi-Tier Anomaly Detection</span>
                  <span className="onboarding-tag purple">Blue Team SOC</span>
                </div>
                <p className="onboarding-card-desc">
                  Defense-in-depth correlation fusing deterministic domain rules, physics residuals, and scikit-learn Isolation Forest ML.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Correlation:</strong> Categorizes incidents into Normal, Cyber-Only, Process-Only, or Cyber-Physical Attacks.
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">📊 6. Statistical Process Analytics</span>
                  <span className="onboarding-tag amber">Process Dynamics</span>
                </div>
                <p className="onboarding-card-desc">
                  High-resolution exploratory data analysis of sensor drift, actuator correlations, and physical distribution curves.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Analytics:</strong> Interactive residual error histograms and sensor vs ground-truth scatter plots.
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">🏆 7. Empirical Evaluation Metrics</span>
                  <span className="onboarding-tag cyan">ML Benchmarking</span>
                </div>
                <p className="onboarding-card-desc">
                  Quantitative verification computing Accuracy, Precision, Recall, and F1-Scores across labelled datasets.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Scientific Proof:</strong> Dynamic benchmark recalculation, confusion matrices, and model comparison charts.
                </div>
              </div>

              <div className="onboarding-card">
                <div className="onboarding-card-header">
                  <span className="onboarding-card-title">💾 8. Datasets & Research Artifacts</span>
                  <span className="onboarding-tag emerald">Data Ops & Export</span>
                </div>
                <p className="onboarding-card-desc">
                  Full time-series data table inspector with instant CSV export of timestamped, ground-truth labelled experimental runs.
                </p>
                <div className="onboarding-card-tip">
                  <strong>Export:</strong> Download clean datasets ready for research reports, evaluation metrics, and external analysis.
                </div>
              </div>
            </div>
          )}

          {activeTab === 'workflow' && (
            <div className="onboarding-steps-container">
              <div className="onboarding-step-card">
                <div className="onboarding-step-num">1</div>
                <div className="onboarding-step-content">
                  <div className="onboarding-step-heading">Step 1: Observe Normal Baseline Operation</div>
                  <div className="onboarding-step-body">
                    Navigate to <strong>Overview</strong>. Confirm that the simulated water level naturally cycles within hysteresis limits (refill at 30%, shutoff at 80%). The top bar displays a green <code>NORMAL</code> badge with near-zero physical residual (&lt; 5%).
                  </div>
                  <button className="btn-secondary btn-sm" style={{ marginTop: 8 }} onClick={() => handleStart('overview')}>
                    Go to Overview
                  </button>
                </div>
              </div>

              <div className="onboarding-step-card">
                <div className="onboarding-step-num">2</div>
                <div className="onboarding-step-content">
                  <div className="onboarding-step-heading">Step 2: Inject a Controlled Cyber Threat</div>
                  <div className="onboarding-step-body">
                    Switch to <strong>Attack Simulator</strong>. Select <em>Sensor Spoofing</em> (falsified level = 20%) or <em>Command Flooding</em> (150 req/s), set duration to 12s, and execute the scenario. The attack runs against localhost:5020 without risking physical equipment.
                  </div>
                  <button className="btn-secondary btn-sm" style={{ marginTop: 8 }} onClick={() => handleStart('attacks')}>
                    Go to Attack Simulator
                  </button>
                </div>
              </div>

              <div className="onboarding-step-card">
                <div className="onboarding-step-num">3</div>
                <div className="onboarding-step-content">
                  <div className="onboarding-step-heading">Step 3: Analyze Multi-Tier Detection & Verification</div>
                  <div className="onboarding-step-body">
                    Go to <strong>Detection & Alerts</strong> and <strong>Digital Twin</strong>. Notice how the physical residual diverges past the 5.0% threshold while the reported sensor lies, triggering the Isolation Forest and cyber-physical correlation alarm. Then inspect <strong>Evaluation</strong> for quantitative F1-scores.
                  </div>
                  <button className="btn-secondary btn-sm" style={{ marginTop: 8 }} onClick={() => handleStart('detection')}>
                    Go to Detection
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'arch' && (
            <div className="onboarding-arch-container">
              <h4 style={{ color: 'var(--text)', margin: '0 0 12px 0', fontSize: 13 }}>
                Closed-Loop Cyber-Physical Digital Twin Architecture
              </h4>
              <div className="onboarding-arch-grid">
                <div className="arch-card" style={{ borderLeft: '3px solid #38bdf8' }}>
                  <div className="arch-card-title" style={{ color: '#38bdf8' }}>1. Physical Plant</div>
                  <div className="arch-card-desc">Continuous mass-balance dh/dt = (Qin - Qout)/A with Torricelli efflux discharge.</div>
                </div>
                <div className="arch-card" style={{ borderLeft: '3px solid #818cf8' }}>
                  <div className="arch-card-title" style={{ color: '#818cf8' }}>2. Virtual PLC</div>
                  <div className="arch-card-desc">Deterministic 5.0 Hz cyclic scan with hysteresis pump/valve control logic.</div>
                </div>
                <div className="arch-card" style={{ borderLeft: '3px solid #34d399' }}>
                  <div className="arch-card-title" style={{ color: '#34d399' }}>3. Modbus TCP</div>
                  <div className="arch-card-desc">Port 5020 slave holding registers 40001–40012 for industrial telemetry & commands.</div>
                </div>
                <div className="arch-card" style={{ borderLeft: '3px solid #fbbf24' }}>
                  <div className="arch-card-title" style={{ color: '#fbbf24' }}>4. Digital Twin</div>
                  <div className="arch-card-desc">Shadow physics reference calculating instantaneous residual |h_sensor - h_shadow|.</div>
                </div>
                <div className="arch-card" style={{ borderLeft: '3px solid #f87171' }}>
                  <div className="arch-card-title" style={{ color: '#f87171' }}>5. Threat Simulator</div>
                  <div className="arch-card-desc">Red team injector targeting Modbus registers with spoofing, writes, floods, replays.</div>
                </div>
                <div className="arch-card" style={{ borderLeft: '3px solid #c084fc' }}>
                  <div className="arch-card-title" style={{ color: '#c084fc' }}>6. Hybrid Detection</div>
                  <div className="arch-card-desc">Rule invariants + residual thresholding + scikit-learn Isolation Forest ML.</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <div className="modal-footer-tip">
            💡 <strong>Tip:</strong> Reopen this guided tour at any time from the top bar <code>🧭 Tour</code> button.
          </div>
          <button className="btn-primary" onClick={() => handleStart()}>
            <CheckCircle2 size={15} />
            Explore Dashboard & Get Started
          </button>
        </div>
      </div>
    </div>
  );
}
