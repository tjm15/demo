# Security Architecture

## Overview
The Planner's Assistant implements multiple layers of security to protect against injection attacks, abuse, and unauthorized access.

## Security Layers

### 1. Input Validation & Sanitization
**Location:** `apps/kernel/modules/security.py`

All user inputs are validated and sanitized before processing:
- **Length limits:** Prompts max 5000 chars, addresses max 500 chars
- **Pattern blocking:** Blocks `<script>`, `javascript:`, SQL injection patterns, path traversal
- **Type validation:** Numeric bounds checking, lat/lng validation
- **Control character stripping:** Removes dangerous control characters

### 2. Rate Limiting
**Per-session limits:**
- 20 requests per 60-second window
- Enforced at reasoning endpoint
- Returns HTTP 429 on limit exceeded
- Logs all rate limit violations

**Production TODO:** Move to Redis-backed distributed rate limiting

### 3. SQL Injection Protection
**All database queries use parameterized statements:**
```python
cur.execute("SELECT * FROM policy WHERE id = %s", (policy_id,))  # ✅ Safe
# NEVER: f"SELECT * FROM policy WHERE id = '{policy_id}'"  # ❌ Dangerous
```

### 4. Domain Allow-Listing (Web Retrieval)
**Location:** `apps/proxy/allowed_sources.yml`

**Only permitted domains:**
- gov.uk, london.gov.uk, planninginspectorate.gov.uk
- planningportal.co.uk
- Module-specific restrictions in `ALLOWED_BY_MODULE`

**Enforcement:**
- Proxy checks domain before download
- Kernel suppresses citations from non-allowed domains
- All blocked attempts logged to audit trail

### 5. LLM Output Validation
**Location:** `modules/security.py::validate_llm_output()`

- Token limits enforced (max 4000 tokens)
- Output scanned for injection patterns
- Truncation rather than failure for overlength
- Structured output validation via Pydantic schemas

### 6. Module Isolation
**Allowed modules:** evidence, policy, strategy, vision, feedback, dm

Invalid module names rejected at input validation.

### 7. Audit Logging
**All security events logged:**
- Rate limit violations
- Input validation failures
- Citation suppressions
- Module access
- LLM API calls

**Log location:** `/tmp/tpa/traces/*.jsonl` (development)
**Production TODO:** Forward to SIEM system

### 8. CORS Policy
**Kernel allows:**
```python
allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+"
```
Development only - localhost ports. Production should use specific origins.

### 9. Proxy Security
**Internal only - no public exposure:**
- Requires `PROXY_INTERNAL_TOKEN` header
- No CORS headers (not accessible from browsers)
- Should run on internal network only

**Content validation:**
- MIME type checking
- Size limits (configurable per domain)
- robots.txt respect
- PDF: text extraction only, no JS execution

## Security Checklist

### Current Implementation ✅
- [x] Input sanitization
- [x] Rate limiting (basic)
- [x] SQL parameterization
- [x] Domain allow-listing
- [x] LLM output validation
- [x] Module validation
- [x] Audit logging
- [x] CORS restrictions

### Production Hardening TODO
- [ ] Redis-backed rate limiting
- [ ] User authentication & authorization
- [ ] JWT token validation
- [ ] HTTPS enforcement
- [ ] CSP headers
- [ ] Database connection pooling with limits
- [ ] Secret management (Vault/AWS Secrets Manager)
- [ ] Container security scanning
- [ ] Network egress firewall (proxy whitelist IPs only)
- [ ] SIEM integration
- [ ] Automated security testing (OWASP ZAP, Burp Suite)

## Threat Model

### Mitigated Threats ✅
1. **SQL Injection** - Parameterized queries
2. **XSS** - Input sanitization, output encoding
3. **Command Injection** - Pattern blocking
4. **Path Traversal** - Input validation
5. **SSRF** - Domain allow-listing
6. **Rate Limit Abuse** - Per-session limits
7. **Prompt Injection** - LLM output validation

### Residual Risks ⚠️
1. **Advanced prompt injection** - LLM manipulation attempts (monitor & refine)
2. **Distributed rate limit bypass** - Needs Redis in production
3. **Data exfiltration** - Requires proper access controls (TODO)
4. **Model poisoning** - External model dependency (use trusted providers)

## Incident Response

**If attack detected:**
1. Check `/tmp/tpa/traces/` for session logs
2. Grep for `[SECURITY WARNING]` or `[SECURITY ERROR]`
3. Review rate limit violations
4. Check proxy logs for domain bypass attempts
5. Ban offending IPs/sessions

**Example:**
```bash
grep "SECURITY" /tmp/tpa/traces/*.jsonl
grep "rate_limit_exceeded" /tmp/tpa/kernel.log
```

## Security Contact
For security issues, do not create public GitHub issues. Contact: [security contact TBD] Policy

We take security seriously and appreciate responsible disclosure.

## Supported Versions

This repository is a demo-quality, production-style app. Security updates are provided on a best-effort basis.

## Reporting a Vulnerability

- Do not open public issues for security vulnerabilities.
- Use GitHub Security Advisories (Private vulnerability reporting) if enabled for this repo.
- Alternatively, open a new issue with the "Security" label and minimal, non-exploit details, and we will follow up privately.

Please include:
- Affected component (proxy, kernel, website)
- Version/commit hash
- Reproduction steps (minimal)
- Impact assessment (confidentiality/integrity/availability)

## Scope and Guidance

- The proxy allow-list (`apps/proxy/allowed_sources.yml`) and guard checks are security-sensitive.
- The kernel’s module-aware citation policy should never allow non-approved domains in citations.
- Avoid storing secrets in the repo or logs; use `.env` and configure `LOG_DIR` appropriately.

Thank you for helping keep The Planner’s Assistant safe.