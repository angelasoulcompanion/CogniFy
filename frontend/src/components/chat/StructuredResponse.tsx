/**
 * CogniFy Structured Response Renderer
 * Renders structured JSON response from RAG in a beautiful UI
 *
 * Created with love by Angela & David - 2 January 2026
 */

import type { StructuredResponse, StructuredSection, StructuredContentItem } from '@/types'

interface StructuredResponseProps {
  data: StructuredResponse
  className?: string
}

// Render a single content item
function ContentItem({ item }: { item: StructuredContentItem }) {
  switch (item.type) {
    case 'text':
      return (
        <p className="text-gray-300 leading-relaxed mb-2">
          {item.text}
        </p>
      )

    case 'fact':
      return (
        <div className="flex items-start gap-2 py-1.5 border-b border-gray-700/50 last:border-0">
          <span className="text-gray-400 font-medium min-w-[120px] shrink-0">
            {item.label}:
          </span>
          <span className="text-white font-semibold">
            {item.value}
          </span>
        </div>
      )

    case 'list_item':
      return (
        <li className="flex items-start gap-2 text-gray-300">
          <span className="text-purple-400 mt-1">•</span>
          <span>{item.text}</span>
        </li>
      )

    default:
      return null
  }
}

// Render a section with heading and items
function Section({ section, isFirst }: { section: StructuredSection; isFirst: boolean }) {
  // Group items by type for better rendering
  const facts = section.items.filter(i => i.type === 'fact')
  const listItems = section.items.filter(i => i.type === 'list_item')
  const textItems = section.items.filter(i => i.type === 'text')

  return (
    <div className={`${isFirst ? '' : 'mt-4 pt-4 border-t border-gray-700/50'}`}>
      {/* Section heading */}
      <h3 className="text-lg font-semibold text-purple-300 mb-3">
        {section.heading}
      </h3>

      {/* Text paragraphs */}
      {textItems.length > 0 && (
        <div className="mb-3">
          {textItems.map((item, idx) => (
            <ContentItem key={`text-${idx}`} item={item} />
          ))}
        </div>
      )}

      {/* Facts as a nice card */}
      {facts.length > 0 && (
        <div className="bg-gray-800/50 rounded-lg p-3 mb-3">
          {facts.map((item, idx) => (
            <ContentItem key={`fact-${idx}`} item={item} />
          ))}
        </div>
      )}

      {/* List items */}
      {listItems.length > 0 && (
        <ul className="space-y-1.5 ml-1">
          {listItems.map((item, idx) => (
            <ContentItem key={`list-${idx}`} item={item} />
          ))}
        </ul>
      )}
    </div>
  )
}

// Main component
export function StructuredResponseRenderer({ data, className = '' }: StructuredResponseProps) {
  if (!data || !data.sections || data.sections.length === 0) {
    // Fallback to raw text if available
    if (data?.raw_text) {
      return <p className="text-gray-300 whitespace-pre-wrap">{data.raw_text}</p>
    }
    return null
  }

  return (
    <div className={`structured-response ${className}`}>
      {/* Main title */}
      {data.title && (
        <h2 className="text-xl font-bold text-white mb-4 pb-2 border-b border-purple-500/30">
          {data.title}
        </h2>
      )}

      {/* Sections */}
      {data.sections.map((section, idx) => (
        <Section key={idx} section={section} isFirst={idx === 0 && !data.title} />
      ))}

      {/* Sources indicator */}
      {data.sources_used && data.sources_used.length > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-700/50">
          <span className="text-xs text-gray-500">
            Sources: {data.sources_used.map(s => `[${s}]`).join(' ')}
          </span>
        </div>
      )}
    </div>
  )
}

// Helper to check if content is structured JSON
export function isStructuredResponse(content: string): StructuredResponse | null {
  try {
    const data = JSON.parse(content)
    if (data.title && data.sections && Array.isArray(data.sections)) {
      return data as StructuredResponse
    }
  } catch {
    // Not JSON
  }
  return null
}

export default StructuredResponseRenderer
