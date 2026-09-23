import React, { useState, useEffect } from 'react';
import AnalyticsPane from './components/AnalyticsPane';
import ChatPane from './components/ChatPane';
import CitationModal from './components/CitationModal';
import { RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const defaultOpportunities = [];

function App() {
  // Analytics State
  const [leftWidth, setLeftWidth] = useState(55);
  const [filterThreshold, setFilterThreshold] = useState(85);
  const [totalScraped, setTotalScraped] = useState(0);
  const [filteredCount, setFilteredCount] = useState(0);
  const [sources, setSources] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [selectedOpp, setSelectedOpp] = useState(null);

  useEffect(() => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
    fetch(`${baseUrl}/api/v1/data/dashboard`)
      .then(res => res.json())
      .then(data => {
        setTotalScraped(data.totalScraped);
        setFilteredCount(data.filteredCount);

        const colorMap = {
          'reddit': { name: 'Reddit', color: '#FB923C', bgColor: 'bg-orange-50', textColor: 'text-orange-700' },
          'youtube': { name: 'YouTube', color: '#FF0000', bgColor: 'bg-red-50', textColor: 'text-red-700' },
          'playstore': { name: 'Play Store', color: '#34A853', bgColor: 'bg-emerald-50', textColor: 'text-emerald-700' },
          'appstore': { name: 'App Store', color: '#4285F4', bgColor: 'bg-blue-50', textColor: 'text-blue-700' },
          'community': { name: 'Google Support', color: '#FBBC05', bgColor: 'bg-amber-50', textColor: 'text-amber-700' }
        };

        const mappedSources = data.sources.map(s => {
          const c = colorMap[s.source] || colorMap['reddit'];
          return { id: s.source, count: s.count, ...c };
        });
        setSources(mappedSources);

        const formatString = (str) => {
          if (!str || typeof str !== 'string') return str;
          return str.replace(/_/g, ' ')
            .replace(/\b\w/g, char => char.toUpperCase());
        };

        const mappedOpps = data.opportunities.map((opp, idx) => ({
          ...opp,
          title: formatString(opp.title),
          category: formatString(opp.category),
          badge: `Priority ${idx + 1}`,
          badgeColor: idx === 0 ? 'bg-red-100 text-red-800 border-red-200' : 'bg-amber-100 text-amber-800 border-amber-200',
          quote: 'Click to query assistant for direct quotes from real users.',
          impact: opp.impact || 'N/A',
        }));

        setOpportunities(mappedOpps);
        if (mappedOpps.length > 0) {
          setSelectedOpp(mappedOpps[0].id);
        }
      })
      .catch(err => console.error('Failed to fetch dashboard data:', err));
  }, []);

  // Chat State
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: 'Hello! I am the UX Research Assistant. I can help you analyze user friction and search failures in Google Photos based on scraped reviews. How can I help you today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeCitation, setActiveCitation] = useState(null);

  // Stream handler
  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputValue.trim()) return;

    const query = inputValue.trim();
    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    const assistantMsgId = Date.now() + 1;
    let assistantText = '';

    // Add empty assistant message that will be streamed into
    setMessages(prev => [...prev, {
      id: assistantMsgId,
      sender: 'assistant',
      text: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);

    try {
      // We will point to the live FastAPI backend
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
      const response = await fetch(`${baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let citationsBlock = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // The backend yields JSON strings separated by newlines
        const lines = chunk.split('\n').filter(line => line.trim() !== '');

        for (const line of lines) {
          try {
            const data = JSON.parse(line);

            if (data.type === 'token') {
              assistantText += data.content;
              setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, text: assistantText } : m
              ));
            } else if (data.type === 'citations') {
              citationsBlock = data.citations;
              // We could attach citations to the message object if needed
              setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, citations: citationsBlock } : m
              ));
            } else if (data.type === 'error') {
              assistantText += `\n[Error: ${data.content}]`;
              setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, text: assistantText } : m
              ));
            }
          } catch (err) {
            console.error("Failed to parse JSON stream chunk", line, err);
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? { ...m, text: "Error connecting to research assistant API." } : m
      ));
    } finally {
      setIsTyping(false);
    }
  };

  const handleCitationClick = async (citId) => {
    // Fetch live citation from DB
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
      const response = await fetch(`${baseUrl}/api/v1/citations/${citId}`);
      if (response.ok) {
        const data = await response.json();
        setActiveCitation({
          title: `Source Record [${citId}]`,
          source: data.source,
          source_url: data.source_url,
          text: data.original_text,
          photo_category: data.photo_category,
          outcome: data.outcome
        });
      } else {
        setActiveCitation({
          title: `Citation [${citId}]`,
          source: 'System',
          text: 'Citation not found or database error.'
        });
      }
    } catch (err) {
      console.error(err);
      setActiveCitation({
        title: `Citation [${citId}]`,
        source: 'Error',
        text: 'Failed to load citation from backend.'
      });
    }
  };

  const renderFormattedText = (text) => {
    // Collapse multiple newlines (3 or more) into standard double newlines to fix extra spacing
    let processedText = text.replace(/\n{3,}/g, '\n\n');

    // Remove OpenAI-style bracketed citations like 【1】 or 【1†source】
    processedText = processedText.replace(/【.*?】/g, '');
    
    // Remove loose dash citations (e.g. "- 1" or "- \n 2") often appended by LLMs at the end of quotes
    processedText = processedText.replace(/\s*-\s*[\n\r]*\s*\d{1,2}(\s*,\s*\d{1,2})*\s*(?=\n|$)/g, '');

    // Convert basic [1] citations into [1](citation:1) so react-markdown can parse them as links
    processedText = processedText.replace(/\[(\d+)\]/g, '[$1](citation:$1)');

    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node, ...props }) => {
            if (props.href && props.href.startsWith('citation:')) {
              const citId = props.href.replace('citation:', '');
              return (
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    handleCitationClick(citId);
                  }}
                  className="inline-flex items-center justify-center mx-1 px-2 py-0.5 text-xs font-semibold text-google-blue bg-blue-100/90 hover:bg-blue-200 text-google-blue hover:text-google-blueHover rounded-full transition-all cursor-pointer shadow-xs border border-blue-200"
                  title="View verified research citation"
                >
                  [{citId}]
                </button>
              );
            }

            let isNumberOnly = false;
            if (typeof props.children === 'string' && /^\d+$/.test(props.children.trim())) {
              isNumberOnly = true;
            } else if (Array.isArray(props.children) && props.children.length === 1 && typeof props.children[0] === 'string' && /^\d+$/.test(props.children[0].trim())) {
              isNumberOnly = true;
            }

            if (isNumberOnly) {
              return <span className="text-gray-700">{props.children}</span>;
            }

            return <a {...props} className="text-blue-500 hover:underline" />;
          },
          table: ({ node, ...props }) => (
            <div className="w-full overflow-x-auto my-3 shadow-sm rounded-lg border border-gray-200">
              <table className="w-full text-sm border-collapse table-fixed" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => <thead className="bg-gray-100/80 border-b border-gray-200" {...props} />,
          th: ({ node, ...props }) => <th className="px-4 py-2 font-semibold text-gray-700 text-left break-words" {...props} />,
          td: ({ node, ...props }) => <td className="px-4 py-3 border-b border-gray-100 align-top text-gray-600 break-words whitespace-pre-wrap" {...props} />,
          h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-4 mb-1 text-gray-800" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-3 mb-1 text-gray-800" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-md font-bold mt-3 mb-1 text-gray-800" {...props} />,
          ul: ({ node, ...props }) => <ul className="list-disc pl-5 mb-2 text-gray-700" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal pl-5 mb-2 text-gray-700" {...props} />,
          li: ({ node, ...props }) => <li className="mb-0.5" {...props} />,
          p: ({ node, ...props }) => <p className="mb-2 text-gray-700 leading-relaxed last:mb-0" {...props} />,
          strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
          em: ({ node, ...props }) => <em className="italic text-gray-800" {...props} />,
          blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-200 pl-4 py-1 my-3 text-gray-600 italic bg-gray-50/50 rounded-r-lg" {...props} />,
          code: ({ node, inline, ...props }) => inline
            ? <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-[13px] font-mono" {...props} />
            : <code className="block bg-gray-50 p-3 rounded-lg overflow-x-auto text-[13px] font-mono border border-gray-100 my-2" {...props} />
        }}
      >
        {processedText}
      </ReactMarkdown>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-[#F8FAFD] text-slate-800 font-sans">

      {/* Top Google App Bar */}
      <header className="h-16 bg-white border-b border-[#dadce0] flex items-center justify-between px-6 z-20 shrink-0 shadow-xs">
        <div className="flex items-center space-x-3">
          <div className="relative w-8 h-8 flex items-center justify-center">
            <svg viewBox="0 0 48 48" className="w-8 h-8">
              <path fill="#EA4335" d="M24 13.5V3a10.5 10.5 0 0 0-10.5 10.5H24z" />
              <path fill="#4285F4" d="M34.5 24H45a10.5 10.5 0 0 0-10.5-10.5V24z" />
              <path fill="#34A853" d="M24 34.5V45a10.5 10.5 0 0 0 10.5-10.5H24z" />
              <path fill="#FBBC05" d="M13.5 24H3a10.5 10.5 0 0 0 10.5 10.5V24z" />
            </svg>
          </div>

          <div className="flex items-baseline space-x-2">
            <span className="text-lg font-bold tracking-tight text-gray-800">Google Photo Search Insights</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-google-blue border border-blue-100 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-google-blue animate-pulse"></span>
              AI Discovery Engine
            </span>
          </div>
          <span className="text-gray-300 text-sm">|</span>
          <span className="text-xs text-gray-500 font-medium">Internal UX Research Suite • PM Workspace</span>
        </div>


      </header>

      {/* Main Dual-Pane Workspace */}
      <div 
        className="flex-1 flex flex-col lg:flex-row overflow-hidden" 
        style={{ '--left-width': `${leftWidth}%` }}
      >
        <div className="w-full lg:w-[var(--left-width)] lg:flex-none h-full overflow-hidden">
          <AnalyticsPane
            filterThreshold={filterThreshold}
            setFilterThreshold={setFilterThreshold}
            totalScraped={totalScraped}
            filteredCount={filteredCount}
            initialSources={sources}
            initialOpportunities={opportunities}
            selectedOpp={selectedOpp}
            setSelectedOpp={setSelectedOpp}
            setInputValue={setInputValue}
          />
        </div>

        <div 
          draggable 
          onDrag={(e) => {
            if (e.clientX === 0) return;
            const newWidth = (e.clientX / window.innerWidth) * 100;
            if (newWidth >= 30 && newWidth <= 70) setLeftWidth(newWidth);
          }}
          onDragStart={(e) => {
            // Required for Firefox to allow dragging without an image/text data
            e.dataTransfer?.setData('text/plain', '');
            // Hide the default drag ghost image
            const img = new Image();
            img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
            e.dataTransfer?.setDragImage(img, 0, 0);
          }}
          className="hidden lg:block w-1.5 bg-[#dadce0] hover:bg-gray-400 cursor-col-resize z-50 flex-shrink-0 transition-colors"
        />

        <div className="w-full lg:flex-1 h-full overflow-hidden">
          <ChatPane
            messages={messages}
            setMessages={setMessages}
            inputValue={inputValue}
            setInputValue={setInputValue}
            isTyping={isTyping}
            handleSendMessage={handleSendMessage}
            renderFormattedText={renderFormattedText}
          />
        </div>
      </div>

      <CitationModal
        activeCitation={activeCitation}
        setActiveCitation={setActiveCitation}
      />

    </div>
  );
}

export default App;
