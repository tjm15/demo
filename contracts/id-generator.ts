/**
 * Deterministic ID generation for panels
 * Replaces timestamp-based IDs with stable, content-based identifiers
 */

/**
 * Simple string hash (djb2 algorithm)
 */
function hashString(str: string): string {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = (hash * 33) ^ str.charCodeAt(i);
  }
  return Math.abs(hash).toString(36).substring(0, 8);
}

/**
 * Generate a stable panel ID from type and content
 * 
 * @param panelType - The panel type (e.g., "applicable_policies")
 * @param contentKey - Optional content key for differentiation (e.g., policy IDs, query hash)
 * @param index - Optional index for multiple instances of same content
 * @returns Deterministic panel ID
 * 
 * @example
 * generatePanelId("applicable_policies") 
 * // => "applicable_policies"
 * 
 * generatePanelId("precedents", "appeal_case_123")
 * // => "precedents_3k7m9p2q"
 * 
 * generatePanelId("doc_viewer", "LP_2024", 1)
 * // => "doc_viewer_5a8b3c2d_1"
 */
export function generatePanelId(
  panelType: string,
  contentKey?: string,
  index?: number
): string {
  // For single-instance panels without content differentiation, use just the type
  if (!contentKey && index === undefined) {
    return panelType;
  }
  
  // For panels with content key, hash it for stable suffix
  if (contentKey) {
    const hash = hashString(contentKey);
    const base = `${panelType}_${hash}`;
    return index !== undefined ? `${base}_${index}` : base;
  }
  
  // For indexed panels without content key
  return `${panelType}_${index}`;
}

/**
 * Extract content key from panel data for ID generation
 * This function inspects panel data to find a stable identifier
 */
export function extractContentKey(panelType: string, data: any): string | undefined {
  if (!data || typeof data !== 'object') {
    return undefined;
  }
  
  switch (panelType) {
    case 'applicable_policies':
      // Hash the policy IDs
      if (Array.isArray(data.policies) && data.policies.length > 0) {
        const ids = data.policies.map((p: any) => p.id).filter(Boolean).sort();
        return ids.length > 0 ? ids.join(',') : undefined;
      }
      break;
      
    case 'precedents':
      // Hash the case refs
      if (Array.isArray(data.cases) && data.cases.length > 0) {
        const refs = data.cases.map((c: any) => c.ref).filter(Boolean).sort();
        return refs.length > 0 ? refs.join(',') : undefined;
      }
      break;
      
    case 'doc_viewer':
      // Use doc_id directly
      return data.doc_id;
      
    case 'policy_editor':
      // Use policy_id
      return data.policy_id;
      
    case 'scenario_compare':
      // Hash scenario IDs
      if (Array.isArray(data.scenarios) && data.scenarios.length > 0) {
        const ids = data.scenarios.map((s: any) => s.id).filter(Boolean).sort();
        return ids.length > 0 ? ids.join('_vs_') : undefined;
      }
      break;
      
    case 'map':
      // Use center coordinates as key
      if (data.center && typeof data.center.lat === 'number' && typeof data.center.lng === 'number') {
        return `${data.center.lat.toFixed(4)},${data.center.lng.toFixed(4)}`;
      }
      break;
      
    case 'evidence_snapshot':
      // Use site location if available
      if (data.site?.lat && data.site?.lng) {
        return `${data.site.lat.toFixed(4)},${data.site.lng.toFixed(4)}`;
      }
      break;
      
    default:
      // For other panels, no automatic key extraction
      return undefined;
  }
  
  return undefined;
}

/**
 * Generate panel ID with automatic content key extraction
 */
export function generatePanelIdFromData(
  panelType: string,
  data: any,
  index?: number
): string {
  const contentKey = extractContentKey(panelType, data);
  return generatePanelId(panelType, contentKey, index);
}

/**
 * Check if a panel ID matches a type and optional content
 */
export function matchesPanelId(
  id: string,
  panelType: string,
  contentKey?: string
): boolean {
  const expectedId = generatePanelId(panelType, contentKey);
  return id === expectedId || id.startsWith(`${expectedId}_`);
}

/**
 * Parse panel type from ID
 */
export function getPanelTypeFromId(id: string): string {
  // ID format: "type" or "type_hash" or "type_hash_index"
  const parts = id.split('_');
  
  // Handle compound types like "key_issues_matrix"
  if (parts.length >= 2) {
    // Try to find the longest matching type
    for (let i = parts.length - 1; i > 0; i--) {
      const candidate = parts.slice(0, i).join('_');
      // This would need access to registry, so return best guess
      return candidate;
    }
  }
  
  return parts[0];
}
