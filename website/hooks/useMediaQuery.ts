import React from 'react';

// A custom hook to check for a media query match
export function useMediaQuery(query: string) {
  const [matches, setMatches] = React.useState(false);

  React.useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }

    const listener = () => {
      setMatches(media.matches);
    };

    // Add listener
    try {
      media.addEventListener('change', listener);
    } catch (e) {
      // For older browsers
      media.addListener(listener);
    }
    
    // Cleanup on unmount
    return () => {
      try {
        media.removeEventListener('change', listener);
      } catch (e) {
        media.removeListener(listener);
      }
    };
  }, [matches, query]);

  return matches;
}
