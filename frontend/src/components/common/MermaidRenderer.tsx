import React, { useEffect, useRef, useState } from 'react';
// @ts-ignore
import mermaid from 'mermaid';

interface MermaidRendererProps {
  chart: string;
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    darkMode: true,
    background: '#161B26',
    primaryColor: '#6366F1',
    secondaryColor: '#8B5CF6',
    tertiaryColor: '#10B981',
    lineColor: '#9CA3AF',
    fontFamily: 'Inter, sans-serif',
  },
  securityLevel: 'loose',
});

export const MermaidRenderer: React.FC<MermaidRendererProps> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [hasError, setHasError] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const renderDiagram = async () => {
      if (!chart || !containerRef.current) return;
      setHasError(false);

      try {
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const cleanChart = chart.trim();
        const { svg } = await mermaid.render(id, cleanChart);
        if (isMounted) {
          setSvgContent(svg);
        }
      } catch (err) {
        console.warn('Mermaid rendering warning:', err);
        if (isMounted) {
          setHasError(true);
        }
      }
    };

    renderDiagram();
    return () => {
      isMounted = false;
    };
  }, [chart]);

  if (hasError) {
    return (
      <div className="my-4 p-4 rounded-xl bg-[#161B26] border border-[#232D3F] text-xs text-[#9CA3AF]">
        <span className="font-semibold text-[#F59E0B]">Process Diagram Structure</span>
        <pre className="mt-2 p-2 bg-[#0B0F17] rounded-lg font-mono text-[#F9FAFB] overflow-x-auto">
          {chart}
        </pre>
      </div>
    );
  }

  return (
    <div className="my-4 p-4 rounded-xl bg-[#161B26] border border-[#232D3F] overflow-x-auto flex justify-center items-center shadow-lg">
      <div
        ref={containerRef}
        dangerouslySetInnerHTML={{ __html: svgContent }}
        className="mermaid-svg-wrapper w-full flex justify-center"
      />
    </div>
  );
};
