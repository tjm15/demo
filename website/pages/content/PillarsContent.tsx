import React from 'react';

// Copied from PillarsPage.tsx for mobile-specific presentation
const pillarsData = {
  spatial: {
    id: 'spatial',
    icon: '🧭',
    title: 'Spatial Plan Intelligence',
    subtitle: 'Tools for plan-making, strategy, and foresight.',
    intro: 'The Spatial Plan Intelligence suite brings together everything needed to build and test spatial strategies — from assembling the evidence base to drafting policy text. Each tool works independently but becomes more powerful when used together, creating a continuous workflow from data to decision.',
    subFeatures: [
      { title: 'Evidence Base', details: 'The Evidence Base lets planners query planning documents, explore geospatial data, and layer indicators such as housing need, transport accessibility, and environmental constraints. It turns dispersed evidence into a coherent, searchable foundation for plan-making.' },
      { title: 'Vision & Concepts', details: 'This module helps planners explore alternative spatial visions — generating schematic visuals, diagrams, and scenario maps that express possible futures. It supports early-stage design thinking and communication with communities and stakeholders.' },
      { title: 'Policy Drafter', details: 'The Policy Drafter analyses existing plans, suggests cross-references, checks alignment with national policy, and helps structure new policies consistently. Every recommendation is explained and traceable, supporting officers as they write and review plan text.' },
      { title: 'Strategy Modeler', details: 'The Strategy Modeler links growth options to indicators such as housing delivery, transport demand, and infrastructure capacity. It enables planners to compare scenarios quantitatively and qualitatively, supporting informed, evidence-led choices.' },
      { title: 'Site Assessment', details: 'Upload site boundaries or select locations to generate instant constraint summaries and opportunity analyses. The module integrates local datasets, designations, and policy layers to produce clear, consistent site reports.' },
      { title: 'Feedback Analysis', details: 'The Feedback Analysis tool analyses written submissions, identifying themes, sentiment, and actionable issues. It helps planners understand public priorities and refine policies with transparency and efficiency.' },
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
      { title: 'Application Intake', details: 'It organises plans, drawings, and supporting documents into a structured workspace, automatically identifying the relevant site boundary, applicable policies, and linked spatial layers. Every piece of evidence is traceable from the outset, creating a clear foundation for the case officer’s review.' },
      { title: 'Context & Policy Analysis', details: 'The Assistant maps key constraints, cross-references adopted and emerging policy, and retrieves comparable cases or appeal decisions. This establishes a transparent context for assessing compliance and identifying material considerations.' },
      { title: 'Reasoning Workspace', details: 'The system synthesises relevant factors — policy tests, site conditions, consultation responses — into a structured reasoning chain. Officers can refine, edit, or challenge each point, ensuring that the emerging report reflects human expertise supported by explainable analysis.' },
      { title: 'Report & Recommendation', details: 'An officer-style report is generated with full traceability: sources cited, reasoning steps visible, and any uncertainties flagged. Reports can be exported, reviewed, or compared across cases, creating a consistent and auditable decision record.' },
    ],
    conclusion: 'Together, these stages form Development Management Intelligence — a disciplined workflow that strengthens rather than replaces discretion, ensuring that decisions are faster, clearer, and demonstrably sound.'
  }
};

const PillarDetail = ({ data }) => (
    <div className="mb-8 last:mb-0">
        <div className="flex items-start gap-3 mb-4">
            <span className="text-3xl mt-1">{data.icon}</span>
            <div>
                <h3 className="text-lg font-semibold text-[color:var(--ink)]">{data.title}</h3>
                <p className="text-[color:var(--muted)]">{data.subtitle}</p>
            </div>
        </div>
        <div className="pl-2 space-y-4 border-l-2 border-[color:var(--edge)] ml-5">
            <p className="pl-4">{data.intro}</p>
            <div className="pl-4 space-y-4">
                {data.subFeatures.map((sub) => (
                    <div key={sub.title}>
                        <h4 className="font-semibold text-[color:var(--ink)]">{sub.title}</h4>
                        <p className="text-[color:var(--muted)] text-sm mt-1">{sub.details}</p>
                    </div>
                ))}
            </div>
            <p className="pl-4 font-medium text-[color:var(--ink)]">{data.conclusion}</p>
        </div>
    </div>
);

export function PillarsContent() {
    return (
        <>
            <PillarDetail data={pillarsData.spatial} />
            <PillarDetail data={pillarsData.development} />
        </>
    );
}