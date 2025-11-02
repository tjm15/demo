import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Page } from '../components/Page';

const pillarsData = {
  spatial: {
    id: 'spatial',
    icon: '🧭',
    title: 'Spatial Plan Intelligence',
    subtitle: 'Tools for plan-making, strategy, and foresight.',
    intro: 'The Spatial Plan Intelligence suite brings together everything needed to build and test spatial strategies — from assembling the evidence base to drafting policy text. Each tool works independently but becomes more powerful when used together, creating a continuous workflow from data to decision.',
    subFeatures: [
      { title: 'Evidence Base', description: 'Build your foundation by connecting maps, datasets, and documents in one place.', details: 'The Evidence Base lets planners query planning documents, explore geospatial data, and layer indicators such as housing need, transport accessibility, and environmental constraints. It turns dispersed evidence into a coherent, searchable foundation for plan-making.' },
      { title: 'Vision & Concepts', description: 'Translate evidence into spatial ideas.', details: 'This module helps planners explore alternative spatial visions — generating schematic visuals, diagrams, and scenario maps that express possible futures. It supports early-stage design thinking and communication with communities and stakeholders.' },
      { title: 'Policy Drafter', description: 'Draft, refine, and validate planning policy.', details: 'The Policy Drafter analyses existing plans, suggests cross-references, checks alignment with national policy, and helps structure new policies consistently. Every recommendation is explained and traceable, supporting officers as they write and review plan text.' },
      { title: 'Strategy Modeler', description: 'Explore the long-term implications of different spatial strategies.', details: 'The Strategy Modeler links growth options to indicators such as housing delivery, transport demand, and infrastructure capacity. It enables planners to compare scenarios quantitatively and qualitatively, supporting informed, evidence-led choices.' },
      { title: 'Site Assessment', description: 'Conduct detailed, map-based site assessments.', details: 'Upload site boundaries or select locations to generate instant constraint summaries and opportunity analyses. The module integrates local datasets, designations, and policy layers to produce clear, consistent site reports.' },
      { title: 'Feedback Analysis', description: 'Synthesise consultation responses and stakeholder input.', details: 'The Feedback Analysis tool analyses written submissions, identifying themes, sentiment, and actionable issues. It helps planners understand public priorities and refine policies with transparency and efficiency.' },
    ],
    conclusion: 'These six tools form the analytical core of Spatial Plan Intelligence — linking data, policy, and place into one coherent environment for planning strategy and evidence-based decision-making.'
  },
  development: {
    id: 'development',
    icon: '🏗️',
    title: 'Development Management Intelligence',
    subtitle: 'From small household extensions to nationally significant infrastructure projects.',
    intro: 'It provides structured support for professional judgement — connecting policy, context, and reasoning in one continuous process.',
    subFeatures: [
      { title: 'Application Intake', description: 'The starting point for assessment.', details: 'It organises plans, drawings, and supporting documents into a structured workspace, automatically identifying the relevant site boundary, applicable policies, and linked spatial layers. Every piece of evidence is traceable from the outset, creating a clear foundation for the case officer’s review.' },
      { title: 'Context & Policy Analysis', description: 'A situational overview that combines location, policy, and precedent.', details: 'The Assistant maps key constraints, cross-references adopted and emerging policy, and retrieves comparable cases or appeal decisions. This establishes a transparent context for assessing compliance and identifying material considerations.' },
      { title: 'Reasoning Workspace', description: 'Where professional judgement is developed and recorded.', details: 'The system synthesises relevant factors — policy tests, site conditions, consultation responses — into a structured reasoning chain. Officers can refine, edit, or challenge each point, ensuring that the emerging report reflects human expertise supported by explainable analysis.' },
      { title: 'Report & Recommendation', description: 'The outcome of the process.', details: 'An officer-style report is generated with full traceability: sources cited, reasoning steps visible, and any uncertainties flagged. Reports can be exported, reviewed, or compared across cases, creating a consistent and auditable decision record.' },
    ],
    conclusion: 'Together, these stages form Development Management Intelligence — a disciplined workflow that strengthens rather than replaces discretion, ensuring that decisions are faster, clearer, and demonstrably sound.'
  }
};

const PillarTab = ({ isActive, onClick, icon, title, subtitle }) => {
  return (
    <motion.button
      onClick={onClick}
      className={`w-full text-left p-4 md:p-6 rounded-2xl border transition-all duration-300 ${isActive ? 'bg-[color:var(--panel)] shadow-md' : 'bg-transparent hover:bg-[color:var(--surface)]'}`}
      style={{ borderBottom: `4px solid ${isActive ? 'var(--accent)' : 'var(--edge)'}`}}
      role="tab"
      aria-selected={isActive}
    >
      <div className="text-2xl mb-2">{icon}</div>
      <h2 className="text-lg md:text-xl font-semibold text-[color:var(--ink)]">{title}</h2>
      <p className="mt-1 text-sm text-[color:var(--muted)] hidden sm:block">{subtitle}</p>
    </motion.button>
  );
};

const SubFeatureCard = ({ title, description, details, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="bg-[color:var(--panel)] border border-[color:var(--edge)] rounded-xl p-5"
    >
      <h3 className="font-semibold text-[color:var(--ink)]">{title}</h3>
      <p className="text-sm text-[color:var(--accent)] font-medium mt-1">{description}</p>
      <p className="text-[color:var(--muted)] mt-3">{details}</p>
    </motion.div>
  );
};

const PillarContent = ({ data }) => {
  return (
    <div className="bg-transparent border border-[color:var(--edge)] rounded-2xl p-6 md:p-8" role="tabpanel">
      <p className="max-w-prose">{data.intro}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mt-6">
        {data.subFeatures.map((sub, index) => (
          <SubFeatureCard key={sub.title} index={index} {...sub} />
        ))}
      </div>
      <p className="mt-6 font-medium text-[color:var(--ink)] max-w-prose">{data.conclusion}</p>
    </div>
  );
};

export function PillarsPage() {
  const [activeTab, setActiveTab] = React.useState('spatial');

  return (
    <Page title="Pillars of the Assistant">
      <div className="grid grid-cols-2 gap-4 mb-8" role="tablist" aria-label="Pillars">
        <PillarTab
          isActive={activeTab === 'spatial'}
          onClick={() => setActiveTab('spatial')}
          {...pillarsData.spatial}
        />
        <PillarTab
          isActive={activeTab === 'development'}
          onClick={() => setActiveTab('development')}
          {...pillarsData.development}
        />
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.4, ease: 'easeInOut' }}
        >
          {activeTab === 'spatial' && <PillarContent data={pillarsData.spatial} />}
          {activeTab === 'development' && <PillarContent data={pillarsData.development} />}
        </motion.div>
      </AnimatePresence>
    </Page>
  );
}