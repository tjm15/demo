# Interactive Session Testing Guide

## Quick Start

### 1. Start All Services

```bash
# Terminal 1: Kernel
cd apps/kernel
source ../../.venv/bin/activate
uvicorn main:app --port 8081 --reload

# Terminal 2: Frontend
cd website
pnpm run dev
```

### 2. Navigate to Evidence Module

Open browser to `http://localhost:5173` and select "Evidence Base" module.

## Test Case 1: Authority Disambiguation

### Setup
**Prompt**: "housing evidence for westminster and camden"

### Expected Behavior
1. Reasoning starts streaming
2. You see: "Multiple authorities detected: Westminster, Camden"
3. **Modal appears** with:
   - Title: "Please provide input"
   - Question: "Which authority would you like to focus on?"
   - Radio buttons for Westminster and Camden
   - Submit and Cancel buttons
4. Select "Westminster" and click Submit
5. Modal closes
6. Reasoning continues: "✓ Focusing on **Westminster**"
7. Evidence browser shows results filtered to Westminster only

### Success Criteria
- ✅ Modal appears during active reasoning (not after completion)
- ✅ Radio buttons render correctly with both options
- ✅ Clicking Submit closes modal and resumes reasoning
- ✅ Final results reflect selected authority
- ✅ Trace log shows: `{"step":"user_selected_authority","output":{"selected":"Westminster"}}`

### Failure Scenarios
- ❌ Modal doesn't appear → Check browser console for errors
- ❌ Modal appears but Submit does nothing → Check Network tab for POST request to `/respond`
- ❌ Kernel hangs after modal → Check kernel logs for timeout errors
- ❌ Results don't reflect selection → Check if authority filter applied to search request

## Test Case 2: Web Fetch Confirmation

### Setup
**Prompt**: "flood risk assessment for rural parish"
(This should return few results, triggering the confirmation prompt)

### Expected Behavior
1. Reasoning starts streaming
2. Search executes: "Found 2 items in local database"
3. **Modal appears** with:
   - Question: "Found only 2 items in local database. Would you like to search external sources (GOV.UK, planning portals)?"
   - Yes and No buttons
4. Click "Yes"
5. Modal closes
6. Reasoning continues: "🌐 **Searching external sources...**"
7. Note appears: "(Web fetch functionality will be implemented post-demo)"

### Success Criteria
- ✅ Confirmation modal only appears when <5 results found
- ✅ Yes/No buttons both work correctly
- ✅ Clicking "Yes" resumes with external search message
- ✅ Clicking "No" continues with local results only
- ✅ Trace log shows: `{"step":"user_confirmed_web_fetch","output":{"confirmed":true}}`

## Test Case 3: Timeout Handling

### Setup
**Prompt**: "housing evidence for westminster and camden"
**Action**: DO NOT interact with modal

### Expected Behavior
1. Modal appears with authority selection
2. Wait for 5+ minutes (or modify timeout in code for faster testing)
3. Modal automatically closes
4. Reasoning continues: "⏱️ No selection made, defaulting to **Westminster**"
5. Search proceeds with first authority

### Success Criteria
- ✅ Reasoning doesn't hang indefinitely
- ✅ Default value is used after timeout
- ✅ Evidence browser shows results with default authority
- ✅ Trace log shows timeout warning

### Fast Testing (Modify Timeout)
Edit `apps/kernel/modules/evidence_module.py`:
```python
response = await select_option(
    context,
    "Which authority would you like to focus on?",
    options=[{"value": auth, "label": auth} for auth in authorities],
    default=authorities[0],
    timeout_seconds=10  # Add this parameter
)
```

## Test Case 4: Cancel Behavior

### Setup
**Prompt**: Any that triggers interactive prompt

### Expected Behavior
1. Modal appears
2. Click "Cancel" button
3. Modal closes
4. Reasoning continues with default/null value
5. No errors in console

### Success Criteria
- ✅ Cancel button closes modal
- ✅ Response is sent as `null` to kernel
- ✅ Kernel handles null response gracefully
- ✅ Reasoning completes successfully

## Test Case 5: Multiple Prompts in Sequence

### Setup
Modify evidence module to add another prompt after authority selection:
```python
# After authority selection
if context.session:
    should_show_stale = await confirm_action(
        context,
        "Include evidence items older than 5 years?"
    )
```

### Expected Behavior
1. First modal: authority selection
2. Submit response
3. Second modal: stale items confirmation
4. Submit response
5. Reasoning completes with both inputs applied

### Success Criteria
- ✅ Both modals appear in sequence
- ✅ Each response is processed correctly
- ✅ No modal overlap or z-index issues
- ✅ Final results reflect both user choices

## Debugging Tips

### Modal Doesn't Appear
**Check**:
1. Browser console for errors
2. `currentPrompt` state in React DevTools
3. SSE event stream in Network tab (look for `prompt_user` event)
4. Kernel logs for session creation

**Common Issues**:
- `context.session` is `None` → Session not created in `/reason` endpoint
- SSE connection dropped → Check CORS, network proxies
- React component not rendering → Check conditional in AppWorkspace

### Submit Does Nothing
**Check**:
1. Network tab for POST to `/reason/session/{id}/respond`
2. Response status (should be 200)
3. Kernel logs for response processing
4. `currentSessionIdRef.current` value in browser console

**Common Issues**:
- Session ID is null → Check SSE event includes `session_id`
- 404 on POST → Session expired or invalid ID
- 500 error → Check kernel logs for exception in `submit_user_response()`

### Reasoning Hangs After Submit
**Check**:
1. Kernel logs for `wait_for_user_response()` timeout
2. Session `response_ready` event was set
3. `user_response` field populated

**Common Issues**:
- Response event never set → Check `submit_user_response()` logic
- Response payload malformed → Validate JSON structure
- Asyncio deadlock → Check for blocking calls in response handler

### Wrong Data in Results
**Check**:
1. Trace logs for user response value
2. Module logic for applying user input
3. Service calls to ensure filters applied

**Common Issues**:
- Response value extracted incorrectly → Check `response.get("value")`
- Filters not passed to search → Verify `EvidenceSearchRequest` parameters
- Default used instead of user input → Check timeout or null handling

## Performance Testing

### Load Test: Many Concurrent Sessions
```bash
# Terminal 1: Start kernel with logging
uvicorn main:app --port 8081 --log-level debug

# Terminal 2: Run multiple concurrent requests
for i in {1..10}; do
  curl -N http://localhost:8081/reason \
    -H "Content-Type: application/json" \
    -d '{"context":{"prompt":"housing evidence for multiple authorities","module":"evidence"}}' &
done
```

**Expected**:
- All sessions created successfully
- No session ID collisions
- Cleanup task removes expired sessions
- Memory usage stable

### Session Cleanup Test
```python
# In Python shell
from apps.kernel.modules.sessions import get_session_manager
import asyncio

mgr = get_session_manager()

# Create test session
session = mgr.create_session()
print(f"Created session: {session.session_id}")

# Wait 31 minutes (or modify timeout for faster testing)
await asyncio.sleep(31 * 60)

# Check if cleaned up
print(f"Sessions remaining: {len(mgr.sessions)}")  # Should be 0
```

## Integration Testing

### Test with Other Modules
1. Policy module: prompt for policy type when ambiguous
2. DM module: confirm fetching additional constraints
3. Strategy module: select which scenario to compare

### Test with Proxy (Post-Demo)
Once proxy integration complete:
1. Trigger web fetch confirmation
2. Verify proxy called with correct parameters
3. Check provenance recorded for fetched items

## Regression Testing

After any changes to session system, re-run:
- ✅ All 5 test cases above
- ✅ Non-interactive reasoning (ensure sessions don't break existing flows)
- ✅ Multiple module switches during active session
- ✅ Browser refresh during active prompt (modal should disappear, session cleaned up)

## Success Metrics

**User Experience**:
- Modal appears within 500ms of prompt_user event
- Submit/Cancel actions feel instant (<100ms)
- No flicker or layout shift when modal appears
- Reasoning flow feels natural, not disruptive

**Reliability**:
- 100% of interactive prompts receive responses (or timeout gracefully)
- Zero session leaks after 1000+ runs
- No kernel crashes due to malformed responses
- All user inputs logged in trace files

**Performance**:
- Session creation: <1ms
- Response submission: <10ms
- Cleanup task: <100ms per run
- Memory overhead: <1KB per session

---

**Ready to Test?** Start with Test Case 1 (Authority Disambiguation) as it's the most straightforward interactive flow.
