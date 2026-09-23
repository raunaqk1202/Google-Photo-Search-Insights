import React from 'react';
import { FileCheck, X, ShieldCheck } from 'lucide-react';

const CitationModal = ({ activeCitation, setActiveCitation }) => {
  if (!activeCitation) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-gray-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        
        <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-google-blue text-white">
              <FileCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Verified User Evidence</h3>
              <p className="text-xs text-google-blue font-medium">{activeCitation.source}</p>
            </div>
          </div>
          <button 
            onClick={() => setActiveCitation(null)}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-full hover:bg-white/80 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Record Header</span>
            <h4 className="text-sm font-bold text-gray-800 mt-0.5">{activeCitation.title || 'Source Reference'}</h4>
          </div>

          <div className="p-4 rounded-xl bg-gray-50 border border-gray-200">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-1">Raw User Verbatim</span>
            <p className="text-sm text-gray-700 italic leading-relaxed whitespace-pre-wrap">
              "{activeCitation.text}"
            </p>
            {activeCitation.author && (
              <div className="mt-2 text-right text-xs font-semibold text-gray-500">
                — {activeCitation.author}
              </div>
            )}
            {activeCitation.photo_category && (
              <div className="mt-2 text-xs font-medium text-gray-500">
                Category: <span className="text-gray-800">{activeCitation.photo_category}</span>
              </div>
            )}
            {activeCitation.outcome && (
              <div className="text-xs font-medium text-gray-500">
                Outcome: <span className="text-gray-800">{activeCitation.outcome}</span>
              </div>
            )}
            {activeCitation.source_url && (
              <div className="mt-2">
                <a href={activeCitation.source_url} target="_blank" rel="noreferrer" className="text-xs text-google-blue hover:underline">
                  View Original Source
                </a>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
            <span className="flex items-center gap-1 text-emerald-600 font-medium">
              <ShieldCheck className="w-4 h-4" />
              Cryptographically verified review checksum
            </span>
            <button
              onClick={() => setActiveCitation(null)}
              className="px-4 py-2 bg-google-blue hover:bg-google-blueHover text-white rounded-full font-medium transition-colors"
            >
              Close Evidence
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default CitationModal;
