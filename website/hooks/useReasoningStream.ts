import { useState, useCallback } from 'react';
import { PanelData } from '../components/app/PanelHost';

interface ReasonRequest {
  module: string;
  prompt: string;
  run_mode: 'stable' | 'deep';
  allow_web_fetch: boolean;
  site_data?: any;
  proposal_data?: any;
}

const KERNEL_URL = (import.meta as any).env?.VITE_KERNEL_URL ?? 'http://127.0.0.1:8081';

export function useReasoningStream() {
  const [panels, setPanels] = useState<PanelData[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [reasoning, setReasoning] = useState<string>('');

  const startReasoning = useCallback(async (request: ReasonRequest) => {
    setIsRunning(true);
    setPanels([]);
    setReasoning('');

    try {
      const response = await fetch(`${KERNEL_URL}/reason`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error('Failed to start reasoning');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

  let buffer = '';
  let lastEventType: string | null = null;

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim() || line.startsWith(':')) continue;

          if (line.startsWith('event:')) {
            lastEventType = line.substring(6).trim();
            continue;
          }

          if (line.startsWith('data:')) {
            const data = line.substring(5).trim();
            
            try {
              const parsed = JSON.parse(data);
              
              if (lastEventType === 'token') {
                setReasoning((prev) => prev + (parsed.token || parsed.data?.token || ''));
              } else if (lastEventType === 'intent') {
                const intent = parsed;
                
                if (intent.action === 'show_panel') {
                  setPanels((prev) => [
                    ...prev,
                    {
                      id: `${intent.panel}-${Date.now()}`,
                      type: intent.panel,
                      data: intent.data || {},
                      timestamp: Date.now(),
                    },
                  ]);
                }
              } else if (lastEventType === 'final') {
                // Analysis complete
                setIsRunning(false);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Reasoning error:', error);
      setIsRunning(false);
    }
  }, []);

  return {
    panels,
    isRunning,
    reasoning,
    startReasoning,
  };
}
