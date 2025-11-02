import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ApplicablePolicies } from './panels/ApplicablePolicies';
import { KeyIssuesMatrix } from './panels/KeyIssuesMatrix';
import { Precedents } from './panels/Precedents';
import { PlanningBalance } from './panels/PlanningBalance';
import { DraftDecision } from './panels/DraftDecision';
import { PolicyEditor } from './panels/PolicyEditor';
import { ConflictHeatmap } from './panels/ConflictHeatmap';
import { ScenarioCompare } from './panels/ScenarioCompare';
import { VisualCompliance } from './panels/VisualCompliance';
import { ConsultationThemes } from './panels/ConsultationThemes';
import { EvidenceSnapshot } from './panels/EvidenceSnapshot';
import { MapPanel } from './panels/MapPanel';
import { MapView } from './panels/MapView';

export interface PanelData {
  id: string;
  type: string;
  data: any;
  timestamp: number;
}

interface PanelHostProps {
  panels: PanelData[];
  module: string;
}

const PANEL_COMPONENTS: Record<string, React.FC<{ data: any }>> = {
  applicable_policies: ApplicablePolicies,
  key_issues_matrix: KeyIssuesMatrix,
  precedents: Precedents,
  planning_balance: PlanningBalance,
  draft_decision: DraftDecision,
  policy_editor: PolicyEditor,
  conflict_heatmap: ConflictHeatmap,
  scenario_compare: ScenarioCompare,
  visual_compliance: VisualCompliance,
  consultation_themes: ConsultationThemes,
  evidence_snapshot: EvidenceSnapshot,
  map: MapPanel,
};

export function PanelHost({ panels, module }: PanelHostProps) {
  if (panels.length === 0) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-white rounded-xl border-2 border-dashed border-slate-300 shadow-sm">
        <div className="text-center px-6 max-w-md">
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-teal-100 to-teal-200 flex items-center justify-center">
            <svg className="w-10 h-10 text-teal-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p className="text-lg font-semibold text-slate-900 mb-2">Ready to Analyze</p>
          <p className="text-sm text-slate-500 mb-4">
            Enter your planning query on the left and click "Run Analysis" to see results here.
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-teal-50 text-teal-700 rounded-lg text-xs font-medium">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            Results will appear as interactive panels
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <AnimatePresence mode="popLayout">
        {panels.map((panel, index) => {
          const PanelComponent = PANEL_COMPONENTS[panel.type];
          
          if (!PanelComponent) {
            return null;
          }

          return (
            <motion.div
              key={panel.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{
                type: 'spring',
                stiffness: 260,
                damping: 20,
                delay: index * 0.1,
              }}
            >
              <PanelComponent data={panel.data} />
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
