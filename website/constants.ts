
// Role-based theme tokens (easier to tune than brand colors directly)
export const theme = {
  surface: "#F7F8FB", // page background (very light neutral)
  panel:   "#FFFFFF", // cards & panels
  edge:    "#D9DCE8", // borders/dividers
  ink:     "#27324A", // headings (deep slate/navy)
  muted:   "#5B6475", // body text
  accent:  "#329c85", // soft teal for highlights/focus
  brand:   "#f5c315", // yellow reserved for tiny accents only
};

// Minimal demo set of Local Planning Authorities (codes approximate; adaptable to DB)
export const LOCAL_AUTHORITIES: { code: string; name: string }[] = [
  { code: 'E09000033', name: 'Westminster City Council' },
  { code: 'E09000007', name: 'Camden Council' },
  { code: 'E09000019', name: 'Islington Council' },
  { code: 'E09000001', name: 'City of London Corporation' },
  { code: 'E06000023', name: 'Bristol City Council' },
];
