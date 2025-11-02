import React from 'react';
import { Page } from '../components/Page';
import { ArchitectureContent } from './content/ArchitectureContent';

export function ArchitecturePage() {
  return (
    <Page title="System Architecture">
        <ArchitectureContent />
        <div className="mt-6 text-sm opacity-80 max-w-prose">Modular by design: Each component can operate independently or together. Councils, consultancies, and research teams can start small — linking the Assistant to existing systems — and expand as they need. The whole architecture is open, adaptable, and built for public use.</div>
    </Page>
  );
}