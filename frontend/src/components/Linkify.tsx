import React from 'react';

interface LinkifyProps {
  text: string;
}

export function Linkify({ text }: LinkifyProps) {
  // Regex to match URLs
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  
  // Split the text by the regex so we can interleave text and links
  const parts = text.split(urlRegex);

  return (
    <>
      {parts.map((part, i) => {
        if (part.match(urlRegex)) {
          try {
            const url = new URL(part);
            let domain = url.hostname;
            
            // Remove 'www.' prefix if it exists
            if (domain.startsWith('www.')) {
              domain = domain.substring(4);
            }
            
            // Optionally, strip the TLD (like .com) to just show "leetcode", "youtube", etc.
            // But if it's something like onrender.com, maybe just showing the first part is fine.
            const domainParts = domain.split('.');
            let displayText = domainParts[0];
            
            // Capitalize the first letter for a cleaner look
            if (displayText.length > 0) {
              displayText = displayText.charAt(0).toUpperCase() + displayText.slice(1);
            }

            return (
              <a 
                key={i} 
                href={part} 
                target="_blank" 
                rel="noreferrer" 
                style={{ 
                  color: '#0288d1', 
                  textDecoration: 'none', 
                  fontWeight: 500,
                  padding: '2px 6px',
                  background: '#e1f5fe',
                  borderRadius: '4px',
                  marginLeft: '4px',
                  marginRight: '4px'
                }}
                title={part}
              >
                {displayText}
              </a>
            );
          } catch {
            // If URL parsing fails for some reason, just render the text
            return <span key={i}>{part}</span>;
          }
        }
        
        // Return standard text (trimming extra spaces around the URL)
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}
