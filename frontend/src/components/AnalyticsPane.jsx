import React from 'react';
import { MessageSquare, ArrowRight, AlertTriangle, Quote, TrendingUp } from 'lucide-react';

const AnalyticsPane = ({ 
  filterThreshold, 
  setFilterThreshold, 
  totalScraped, 
  filteredCount,
  initialSources,
  initialOpportunities,
  selectedOpp,
  setSelectedOpp,
  setInputValue
}) => {
  return (
    <main className="w-full h-full overflow-y-auto p-4 md:p-6 lg:p-7 space-y-8 bg-[#F8FAFD]">
      
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Retrieval Insights & Opportunities
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Synthesizing raw multi-channel sentiment, friction logs, and user search failures.
        </p>
      </div>

      <div className="space-y-4">
        {/* Overview Stats (Row 1) */}
        <div className="grid grid-cols-2 gap-4">
          {/* Total Scraped Card */}
          <div className="bg-white rounded-xl p-4 border border-[#dadce0] border-t-4 border-t-violet-500 shadow-sm flex flex-col justify-center items-center text-center min-h-[96px]">
            <div className="text-2xl font-bold text-gray-900 font-mono leading-tight">{(totalScraped || 0).toLocaleString()}</div>
            <div className="text-[13px] text-gray-600 mt-1 font-medium">Reviews Scraped</div>
          </div>

          {/* Classified Reviews Card */}
          <div className="bg-white rounded-xl p-4 border border-[#dadce0] border-t-4 border-t-pink-500 shadow-sm flex flex-col justify-center items-center text-center min-h-[96px]">
            <div className="text-2xl font-bold text-gray-900 font-mono leading-tight">{(filteredCount || 0).toLocaleString()}</div>
            <div className="text-[13px] text-gray-600 mt-1 font-medium">Classified Reviews</div>
          </div>
        </div>

        {/* Grid of sources (Row 2) */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* Dynamic Source Cards */}
          {initialSources.map((source) => (
            <div 
              key={source.id} 
              className="bg-white rounded-xl p-4 border border-[#dadce0] border-t-4 shadow-sm flex flex-col justify-center items-center text-center min-h-[96px] hover:shadow-md transition-shadow"
              style={{ borderTopColor: source.color }}
            >
              <div className="text-2xl font-bold text-gray-900 font-mono leading-tight">{source.count.toLocaleString()}</div>
              <div className="text-[13px] text-gray-600 mt-1 font-medium">{source.name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Opportunities List */}
      <div className="bg-white rounded-2xl p-5 border border-[#dadce0] shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-amber-50 text-amber-700">
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-gray-900">Ranked Product Opportunities</h2>
              <p className="text-xs text-gray-500">Synthesized engineering and retrieval friction priorities</p>
            </div>
          </div>
        </div>

        <div className="p-3 mb-4 rounded-lg bg-gray-50 border border-gray-200/70 flex flex-col gap-1.5">
          <p className="text-xs text-gray-700 font-semibold">
            Score (out of 100) = 35% Reach + 30% User Pain + 20% Business Impact + 15% Evidence Strength
          </p>
          <p className="text-xs text-gray-600">
            <strong>Reach</strong>: Logarithmic scale of review frequency. <strong>User Pain, Business Impact, Evidence Strength</strong>: Averages of LLM-assigned scores.
          </p>
        </div>

        <div className="p-2.5 mb-4 rounded-lg bg-gray-50 border border-gray-200/70 text-xs italic text-gray-700 flex items-start gap-2">
          <Quote className="w-3.5 h-3.5 text-gray-400 shrink-0 mt-0.5" />
          <span>Click to query assistant for direct quotes, user inferences, and failure modes.</span>
        </div>

        <div className="space-y-3">
          {initialOpportunities.map((opp) => {
            const isSelected = selectedOpp === opp.id;
            return (
              <div
                key={opp.id}
                onClick={() => setSelectedOpp(opp.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected 
                    ? 'border-google-blue bg-blue-50/40 shadow-sm ring-1 ring-google-blue/30' 
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50/50'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-sm text-gray-900">{opp.title}</span>
                  </div>
                </div>

                <p className="text-xs text-gray-600 leading-relaxed mb-3">
                  {opp.description}
                </p>

                <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs bg-gray-50 p-2.5 rounded-lg border border-gray-100">
                  <div className="flex items-center gap-1"><span className="font-medium text-gray-500">Reach:</span> <span className="font-semibold text-gray-700">{opp.reach_score?.toFixed(1) || 'N/A'}/5</span></div>
                  <div className="flex items-center gap-1"><span className="font-medium text-gray-500">User Pain:</span> <span className="font-semibold text-gray-700">{opp.user_pain?.toFixed(1) || 'N/A'}/5</span></div>
                  <div className="flex items-center gap-1"><span className="font-medium text-gray-500">Business Impact:</span> <span className="font-semibold text-gray-700">{opp.business_impact?.toFixed(1) || 'N/A'}/5</span></div>
                  <div className="flex items-center gap-1"><span className="font-medium text-gray-500">Evidence Strength:</span> <span className="font-semibold text-gray-700">{opp.evidence_strength?.toFixed(1) || 'N/A'}/5</span></div>
                </div>

                <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-gray-100 text-xs">
                  <div className="flex items-center gap-2 text-google-blue font-medium">
                    <span><strong>{opp.impact}</strong></span>
                  </div>

                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setInputValue(`Tell me more about how users experience "${opp.title}".`);
                    }}
                    className="text-xs font-semibold text-gray-600 hover:text-google-blue flex items-center gap-1 hover:underline"
                  >
                    <span>Query Assistant</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
};

export default AnalyticsPane;
