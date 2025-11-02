import React from 'react';
import { Page } from '../components/Page';
import { ModuleCard } from '../components/ModuleCard';

const involvementItems = [
    { title: "For planners and officers", desc: "Explore the demo, see how it handles policies and sites, and share feedback." },
    { title: "For councils and public bodies", desc: "The system can be adapted to local evidence bases and existing GIS or document systems. Partner pilots are being developed to explore real‑world integration and open data publication." },
    { title: "For collaborators and technologists", desc: "The architecture is modular and well‑documented. You can build new analytical layers, connect external datasets, or contribute directly to the open repository." },
    { title: "For researchers and educators", desc: "The platform offers a live environment for studying digital planning, AI governance, and the design of public‑sector reasoning tools. It’s available for teaching, experimentation, and peer review." },
];

export function InvolvedPage() {
  const handleCardClick = (title: string) => {
    window.location.href = `mailto:hello@theplannersassistant.uk?subject=Inquiry: ${encodeURIComponent(title)}`;
  };

  return (
    <Page title="Get Involved">
      <div className="max-w-prose">
        <p>The Planner’s Assistant is an open project — designed to grow through collaboration between planners, technologists, and researchers. Its core tools are already live in prototype form, and new modules are being tested across the planning workflow.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-6">
        {/* FIX: Destructuring item props in map to resolve incorrect 'key' prop error. */}
    {involvementItems.map(({ title, desc }) => (
      <React.Fragment key={title}>
        <ModuleCard 
          title={title}
          desc={desc}
          onClick={() => handleCardClick(title)}
        />
      </React.Fragment>
    ))}
      </div>
      <div className="mt-6 text-[color:var(--muted)] max-w-prose space-y-4">
        <p>
          Public demos, documentation, and design papers will be released in stages as development continues. Further details and early thoughts can be found on my <a href="https://tim-mayoh.bearblog.dev/" target="_blank" rel="noopener noreferrer" className="text-[color:var(--accent)] hover:underline">personal site</a>.
        </p>
        <div className="font-medium text-[color:var(--ink)]">
          <strong>The Planner’s Assistant is not a product.</strong><br />It’s an emerging part of the civic infrastructure we all depend on — a shared effort to make planning more intelligent, transparent, and humane.
        </div>
      </div>
    </Page>
  );
}