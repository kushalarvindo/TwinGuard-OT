import React, { useState } from 'react';
import { useTelemetry } from './hooks/useTelemetry';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
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
  const telemetry = useTelemetry();

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
      <Sidebar currentPage={page} onNavigate={setPage} />
      <Header connected={telemetry.connected} latest={telemetry.latest} />
      <main className="main-content">
        {renderPage()}
      </main>
    </div>
  );
}
