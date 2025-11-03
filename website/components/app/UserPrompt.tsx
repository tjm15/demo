import React, { useState } from 'react';
import { AlertCircle, HelpCircle } from 'lucide-react';

interface UserPromptProps {
  promptId: string;
  question: string;
  inputType: 'text' | 'select' | 'multiselect' | 'confirm' | 'number';
  options?: Array<{ value: string; label: string }>;
  defaultValue?: any;
  onSubmit: (response: { value: any }) => void;
  onCancel?: () => void;
}

export function UserPrompt({
  promptId,
  question,
  inputType,
  options = [],
  defaultValue,
  onSubmit,
  onCancel,
}: UserPromptProps) {
  const [value, setValue] = useState<any>(defaultValue || '');
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

  const handleSubmit = () => {
    let responseValue = value;
    
    if (inputType === 'multiselect') {
      responseValue = selectedOptions;
    } else if (inputType === 'confirm') {
      responseValue = value === true || value === 'yes';
    } else if (inputType === 'number') {
      responseValue = parseFloat(value) || 0;
    }
    
    onSubmit({ value: responseValue });
  };

  const handleMultiToggle = (optionValue: string) => {
    setSelectedOptions(prev =>
      prev.includes(optionValue)
        ? prev.filter(v => v !== optionValue)
        : [...prev, optionValue]
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 p-6 border border-slate-200">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="p-2 rounded-lg bg-teal-100">
            <HelpCircle className="w-5 h-5 text-teal-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-slate-900 mb-1">
              Input Required
            </h3>
            <p className="text-sm text-slate-600 whitespace-pre-wrap">
              {question}
            </p>
          </div>
        </div>

        {/* Input Area */}
        <div className="mb-6">
          {inputType === 'text' && (
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-200"
              placeholder="Enter your response..."
              autoFocus
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
          )}

          {inputType === 'number' && (
            <input
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-200"
              placeholder="Enter a number..."
              autoFocus
            />
          )}

          {inputType === 'select' && (
            <div className="space-y-2">
              {options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setValue(opt.value)}
                  className={`w-full px-4 py-3 rounded-lg border-2 text-left transition-colors ${
                    value === opt.value
                      ? 'border-teal-500 bg-teal-50 text-teal-900'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                      value === opt.value ? 'border-teal-500' : 'border-slate-300'
                    }`}>
                      {value === opt.value && (
                        <div className="w-2 h-2 rounded-full bg-teal-500" />
                      )}
                    </div>
                    <span className="font-medium">{opt.label}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {inputType === 'multiselect' && (
            <div className="space-y-2">
              {options.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleMultiToggle(opt.value)}
                  className={`w-full px-4 py-3 rounded-lg border-2 text-left transition-colors ${
                    selectedOptions.includes(opt.value)
                      ? 'border-teal-500 bg-teal-50 text-teal-900'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                      selectedOptions.includes(opt.value)
                        ? 'border-teal-500 bg-teal-500'
                        : 'border-slate-300'
                    }`}>
                      {selectedOptions.includes(opt.value) && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                          <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" fill="none" />
                        </svg>
                      )}
                    </div>
                    <span className="font-medium">{opt.label}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {inputType === 'confirm' && (
            <div className="flex gap-3">
              <button
                onClick={() => setValue(true)}
                className={`flex-1 px-4 py-3 rounded-lg border-2 font-medium transition-colors ${
                  value === true
                    ? 'border-teal-500 bg-teal-500 text-white'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                }`}
              >
                Yes
              </button>
              <button
                onClick={() => setValue(false)}
                className={`flex-1 px-4 py-3 rounded-lg border-2 font-medium transition-colors ${
                  value === false
                    ? 'border-red-500 bg-red-500 text-white'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                }`}
              >
                No
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          {onCancel && (
            <button
              onClick={onCancel}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-medium transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleSubmit}
            className="px-6 py-2 rounded-lg bg-teal-600 text-white hover:bg-teal-700 font-medium transition-colors shadow-sm"
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}
