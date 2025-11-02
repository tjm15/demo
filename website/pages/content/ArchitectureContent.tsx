import React from 'react';
import { ModuleCard } from '../../components/ModuleCard';

const modules = [
    { title: "Policy & Knowledge Base", desc: "Stores and structures the content of plans, guidance, and strategies — showing which policies apply and why." },
    { title: "Spatial Analysis Engine", desc: "Brings maps, datasets, and local evidence into the same view, revealing limits, capacities, and opportunities." },
    { title: "Scenario Workspace", desc: "Lets planners model and compare options before decisions are made." },
    { title: "Assessment Support", desc: "Designed for everyday development management work — from small extensions to major infrastructure." },
    { title: "Visual Context Layer", desc: "Interprets plans, diagrams, and visuals to recognise character, scale, and design intent." },
    { title: "Interface & Audit Layer", desc: "Presents everything through a transparent interface where every source and step of reasoning is recorded." },
];

export function ArchitectureContent() {
  return (
    <>
        <p className="max-w-prose">The Planner’s Assistant works as a set of connected tools that share data, reasoning, and context. Each part has a clear job, but together they form one environment where planning evidence can be explored, tested, and explained.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
            {/* FIX: Destructuring module props in map to resolve incorrect 'key' prop error. */}
            {modules.map(({ title, desc }) => (
              <React.Fragment key={title}>
                <ModuleCard title={title} desc={desc} />
              </React.Fragment>
            ))}
        </div>
    </>
  );
}