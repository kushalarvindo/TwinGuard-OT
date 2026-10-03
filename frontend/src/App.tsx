import React, { useState, useEffect } from 'react';
import { useTelemetry } from './hooks/useTelemetry';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import OnboardingModal from './components/OnboardingModal';
import SettingsModal from './components/SettingsModal';

import OverviewPage from './pages/OverviewPage';
import DigitalTwinPage from './pages/DigitalTwinPage';
import TelemetryPage from './pages/TelemetryPage';
import ModbusPage from './pages/ModbusPage';
import AttacksPage from './pages/AttacksPage';
import DetectionPage from './pages/DetectionPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ExperimentsPage from './pages/ExperimentsPage';
import EvaluationPage from './pages/EvaluationPage';
import DatasetsPage from './pages/DatasetsPage';
import SystemPage from './pages/SystemPage';

export type PageId =
  | 'overview'
  | 'twin'
  | 'telemetry'
  | 'modbus'
  | 'attacks'
  | 'detection'
  | 'analytics'
  | 'experiments'
  | 'evaluation'
  | 'datasets'
  | 'system';

export default function App() {
  const [page, setPage] = useState<PageId>('overview');
  const [isTourOpen, setIsTourOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const telemetry = useTelemetry();

  useEffect(() => {
    // Show onboarding tour automatically on first visit if not completed
    const completed = localStorage.getItem('twinguard_onboarding_completed');
    if (!completed) {
      setIsTourOpen(true);
    }
  }, []);

  const renderPage = () => {
    switch (page) {
      case 'overview':    return <OverviewPage telemetry={telemetry} />;
      case 'twin':        return <DigitalTwinPage telemetry={telemetry} />;
      case 'telemetry':   return <TelemetryPage telemetry={telemetry} />;
      case 'modbus':      return <ModbusPage />;
      case 'attacks':     return <AttacksPage />;
      case 'detection':   return <DetectionPage telemetry={telemetry} />;
      case 'analytics':   return <AnalyticsPage />;
      case 'experiments': return <ExperimentsPage />;
      case 'evaluation':  return <EvaluationPage />;
      case 'datasets':    return <DatasetsPage />;
      case 'system':      return <SystemPage />;
      default:            return <OverviewPage telemetry={telemetry} />;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar
        currentPage={page}
        onNavigate={setPage}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenTour={() => setIsTourOpen(true)}
      />
      <Header
        connected={telemetry.connected}
        latest={telemetry.latest}
        currentPage={page}
        onOpenTour={() => setIsTourOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />
      <main className="main-content">
        {renderPage()}
      </main>

      {/* Onboarding Tour Modal */}
      <OnboardingModal
        isOpen={isTourOpen}
        onClose={() => setIsTourOpen(false)}
        onNavigate={setPage}
      />

      {/* Settings & Safety Controls Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}
