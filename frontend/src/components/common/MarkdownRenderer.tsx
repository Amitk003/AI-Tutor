import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import { MermaidRenderer } from './MermaidRenderer';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <div className="prose prose-invert max-w-none text-sm leading-relaxed text-[#F9FAFB]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const codeText = String(children).replace(/\n$/, '');

            if (language === 'mermaid') {
              return <MermaidRenderer chart={codeText} />;
            }

            if (language) {
              return (
                <div className="my-3 rounded-xl bg-[#0B0F17] border border-[#232D3F] overflow-hidden">
                  <div className="px-4 py-1.5 bg-[#161B26] border-b border-[#232D3F] text-xs font-mono text-[#9CA3AF] flex justify-between items-center">
                    <span>{language}</span>
                  </div>
                  <pre className="p-4 font-mono text-xs text-[#F9FAFB] overflow-x-auto">
                    <code>{codeText}</code>
                  </pre>
                </div>
              );
            }

            return (
              <code className="px-1.5 py-0.5 rounded bg-[#161B26] border border-[#232D3F] font-mono text-xs text-[#8B5CF6]" {...props}>
                {children}
              </code>
            );
          },
          table({ children }) {
            return (
              <div className="my-4 overflow-x-auto rounded-xl border border-[#232D3F]">
                <table className="min-w-full divide-y divide-[#232D3F] bg-[#161B26] text-xs">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-[#0B0F17] text-[#9CA3AF] font-semibold">{children}</thead>;
          },
          th({ children }) {
            return <th className="px-4 py-3 text-left tracking-wider">{children}</th>;
          },
          td({ children }) {
            return <td className="px-4 py-3 whitespace-normal border-t border-[#232D3F]">{children}</td>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
