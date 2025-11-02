import React, { useState } from 'react';
import { Upload, Link as LinkIcon, X, FileText, Globe, Loader2 } from 'lucide-react';

interface AddEvidenceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (data: AddEvidenceData) => void;
}

export interface AddEvidenceData {
  method: 'upload' | 'url';
  title: string;
  type: string;
  topicTags: string[];
  file?: File;
  url?: string;
  author?: string;
  publisher?: string;
  year?: number;
  notes?: string;
}

const EVIDENCE_TYPES = [
  'SHMA',
  'HENA',
  'SFRA',
  'Viability Study',
  'SHELAA',
  'Transport Assessment',
  'Environmental Impact',
  'Heritage Assessment',
  'Retail Study',
  'Employment Land',
  'Infrastructure Capacity',
  'Other',
];

const TOPIC_TAGS = [
  'housing',
  'economy',
  'transport',
  'environment',
  'climate',
  'heritage',
  'infrastructure',
  'social',
  'retail',
  'design',
];

export function AddEvidenceDialog({ isOpen, onClose, onAdd }: AddEvidenceDialogProps) {
  const [method, setMethod] = useState<'upload' | 'url'>('upload');
  const [title, setTitle] = useState('');
  const [type, setType] = useState('SHMA');
  const [topicTags, setTopicTags] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [author, setAuthor] = useState('');
  const [publisher, setPublisher] = useState('');
  const [year, setYear] = useState<string>('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toggleTopic = (topic: string) => {
    setTopicTags((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || (method === 'upload' && !file) || (method === 'url' && !url)) {
      return;
    }

    setIsSubmitting(true);
    
    await onAdd({
      method,
      title,
      type,
      topicTags,
      file: file || undefined,
      url: method === 'url' ? url : undefined,
      author: author || undefined,
      publisher: publisher || undefined,
      year: year ? parseInt(year) : undefined,
      notes: notes || undefined,
    });

    setIsSubmitting(false);
    handleReset();
    onClose();
  };

  const handleReset = () => {
    setTitle('');
    setType('SHMA');
    setTopicTags([]);
    setFile(null);
    setUrl('');
    setAuthor('');
    setPublisher('');
    setYear('');
    setNotes('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-teal-100 flex items-center justify-center">
              <Upload className="w-5 h-5 text-teal-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Add Evidence</h2>
              <p className="text-sm text-slate-500">Upload a file or provide a URL</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Method Toggle */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Source Method</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMethod('upload')}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-colors ${
                  method === 'upload'
                    ? 'border-teal-500 bg-teal-50 text-teal-700'
                    : 'border-slate-200 hover:border-slate-300 text-slate-600'
                }`}
              >
                <FileText className="w-5 h-5" />
                <span className="font-medium">Upload File</span>
              </button>
              <button
                type="button"
                onClick={() => setMethod('url')}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-colors ${
                  method === 'url'
                    ? 'border-teal-500 bg-teal-50 text-teal-700'
                    : 'border-slate-200 hover:border-slate-300 text-slate-600'
                }`}
              >
                <Globe className="w-5 h-5" />
                <span className="font-medium">From URL</span>
              </button>
            </div>
          </div>

          {/* File Upload or URL */}
          {method === 'upload' ? (
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                File <span className="text-red-500">*</span>
              </label>
              <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:border-teal-400 transition-colors">
                <input
                  type="file"
                  accept=".pdf,.csv,.xlsx,.zip,.gpkg,.shp"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-3 text-slate-400" />
                  <p className="text-sm font-medium text-slate-700 mb-1">
                    {file ? file.name : 'Click to upload or drag and drop'}
                  </p>
                  <p className="text-xs text-slate-500">
                    PDF, CSV, XLSX, ZIP, GeoPackage, or Shapefile
                  </p>
                </label>
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                URL <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.gov.uk/evidence/document.pdf"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                required={method === 'url'}
              />
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Strategic Housing Market Assessment 2024"
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              required
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Evidence Type <span className="text-red-500">*</span>
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              required
            >
              {EVIDENCE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Topic Tags */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Topic Tags</label>
            <div className="flex flex-wrap gap-2">
              {TOPIC_TAGS.map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => toggleTopic(topic)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                    topicTags.includes(topic)
                      ? 'bg-teal-500 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Author</label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="GL Hearn"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Publisher</label>
              <input
                type="text"
                value={publisher}
                onChange={(e) => setPublisher(e.target.value)}
                placeholder="Westminster Council"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Year</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="2024"
              min="1900"
              max={new Date().getFullYear()}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Key findings, context, or methodology notes..."
              rows={3}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title || (method === 'upload' && !file) || (method === 'url' && !url)}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Add Evidence
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
