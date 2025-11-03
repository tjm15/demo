# Interactive Session System

## Overview

The Planner's Assistant now supports **bidirectional interactive communication** during active reasoning sessions. The kernel can pause mid-reasoning to ask users for clarification, confirmation, or additional input while simultaneously gathering context from the database, proxy, and other sources.

## Architecture

### Backend Components

#### 1. Session Management (`apps/kernel/modules/sessions.py`)

**`InteractiveSession`** dataclass:
- `session_id`: Unique identifier
- `event_queue`: asyncio.Queue for SSE streaming
- `is_waiting`: Flag indicating if waiting for user response
- `response_ready`: asyncio.Event for synchronization
- `user_response`: Stores the user's response
- `last_activity`: Timestamp for cleanup
- `created_at`: Session creation time

**`SessionManager`** singleton:
- `create_session()`: Initialize new interactive session
- `get_session(session_id)`: Retrieve active session
- `wait_for_user_response(session_id, prompt, timeout)`: Emit prompt_user event and block until response
- `submit_user_response(session_id, response)`: Accept user input and resume reasoning
- `cleanup_expired_sessions()`: Background task removes sessions inactive >30min

#### 2. Interactive Helpers (`apps/kernel/modules/interactive.py`)

High-level wrapper functions for common prompt patterns:

- **`prompt_user(context, question, input_type, options, default, timeout)`**: Generic prompt with configurable input type
- **`confirm_action(context, action)`**: Yes/no confirmation dialog
- **`select_option(context, question, options, default)`**: Single-choice selector (radio buttons)
- **`get_text_input(context, question, default)`**: Free-text input field

All functions check for `context.session` and gracefully return `None` if no interactive session is attached.

#### 3. Backend Endpoints

**`POST /reason`** (SSE stream):
- Creates `InteractiveSession` at start
- Passes session to `execute_playbook()`
- Attaches `session_id` to context
- Cleans up session in finally block
- Streams: token, intent, patch, **prompt_user**, final, error events

**`POST /reason/session/{session_id}/respond`**:
- Accepts `UserResponseRequest` with response payload
- Calls `SessionManager.submit_user_response()`
- Triggers `response_ready` event to resume reasoning

### Frontend Components

#### 1. Reasoning Hook (`website/hooks/useReasoningStreamV2.ts`)

**New State**:
- `currentPrompt`: Holds prompt_user event data (question, input_type, options, etc.)
- `currentSessionIdRef`: Tracks active session for response submission

**SSE Event Handling**:
```typescript
else if (lastEventType === 'prompt_user') {
  const promptData = parsed;
  currentSessionIdRef.current = promptData.session_id || sessionIdRef.current;
  setCurrentPrompt(promptData);
}
```

**Response Submission**:
```typescript
const submitPromptResponse = useCallback(async (response: any) => {
  const sessionId = currentSessionIdRef.current;
  const res = await fetch(`${KERNEL_URL}/reason/session/${sessionId}/respond`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ response }),
  });
  setCurrentPrompt(null);
}, []);
```

**Return Values**: Now includes `currentPrompt` and `submitPromptResponse`

#### 2. User Prompt Modal (`website/components/app/UserPrompt.tsx`)

Full-featured modal overlay supporting 5 input types:

- **`text`**: Free-text input with Enter key submit
- **`number`**: Numeric input field
- **`select`**: Radio button list (single choice)
- **`multiselect`**: Checkbox list (multiple choices)
- **`confirm`**: Yes/No buttons

**Props**:
- `promptId`: Unique prompt identifier
- `question`: Question text to display
- `inputType`: One of the 5 types above
- `options`: Array of `{value, label}` for select/multiselect
- `defaultValue`: Pre-populated value
- `onSubmit`: Callback with `{value: ...}` payload
- `onCancel`: Callback for cancel action

**Styling**: Fixed overlay with backdrop blur, teal accent colors, smooth transitions

#### 3. Integration (`website/components/app/AppWorkspace.tsx`)

**Hook Usage**:
```tsx
const { 
  currentPrompt,
  submitPromptResponse,
  // ...other hook values
} = useReasoningStream({ onStateChange: handleStateChange });
```

**Conditional Rendering**:
```tsx
{currentPrompt && (
  <UserPrompt
    promptId={currentPrompt.prompt_id}
    question={currentPrompt.question}
    inputType={currentPrompt.input_type}
    options={currentPrompt.options}
    defaultValue={currentPrompt.default}
    onSubmit={submitPromptResponse}
    onCancel={() => submitPromptResponse(null)}
  />
)}
```

## Example Usage in Modules

### Evidence Module Authority Disambiguation

```python
# If multiple authorities detected, ask which one to focus on
if len(authorities) > 1 and context.session:
    from modules.interactive import select_option
    
    response = await select_option(
        context,
        "Which authority would you like to focus on?",
        options=[{"value": auth, "label": auth} for auth in authorities],
        default=authorities[0]
    )
    
    if response and response.get("value"):
        selected_auth = response["value"]
        authorities = [selected_auth]
        # Continue with focused search...
```

### Evidence Module Web Fetch Confirmation

```python
# If local results are sparse, offer to search external sources
if len(items) < 5 and context.session and context.allow_web_fetch:
    from modules.interactive import confirm_action
    
    should_fetch = await confirm_action(
        context,
        f"Found only {len(items)} items in local database. Would you like to search external sources?"
    )
    
    if should_fetch and should_fetch.get("value"):
        # Proceed with proxy search...
```

## Event Flow

1. **User starts reasoning** → Frontend calls `POST /reason`
2. **Kernel creates session** → `InteractiveSession` initialized with event queue
3. **Module needs clarification** → Calls `prompt_user()` or helper function
4. **Session manager emits event** → `prompt_user` event pushed to queue
5. **Frontend receives event** → `currentPrompt` state updated
6. **UserPrompt modal appears** → User sees question and input controls
7. **User submits response** → `submitPromptResponse()` POSTs to `/respond` endpoint
8. **Backend receives response** → `submit_user_response()` sets event and stores data
9. **Kernel resumes** → `wait_for_user_response()` returns with user's input
10. **Reasoning continues** → Module uses response to refine query/action

## Timeout Behavior

- Default timeout: **300 seconds (5 minutes)**
- If user doesn't respond within timeout:
  - `wait_for_user_response()` returns `None`
  - Module should use `default` value or gracefully skip the clarification
  - Session marked as `is_waiting = False`
  - Error logged: `"User response timeout"`

## Session Cleanup

- Background task runs every **60 seconds**
- Sessions inactive for >**30 minutes** are removed
- Cleanup prevents memory leaks from abandoned sessions
- Active waiting sessions are never cleaned up

## Security & Validation

- Session IDs are UUIDs (non-guessable)
- Only active sessions can receive responses
- Responses to non-waiting sessions are rejected
- No cross-session data leakage
- Timeout prevents indefinite blocking

## Testing Scenarios

### Scenario 1: Authority Disambiguation
**Prompt**: "housing evidence for westminster and camden"
**Expected**:
1. Modal appears: "Which authority would you like to focus on?"
2. Radio buttons: Westminster, Camden
3. User selects "Westminster"
4. Reasoning continues with filtered results for Westminster only

### Scenario 2: Web Fetch Confirmation
**Prompt**: "obscure policy topic with few local results"
**Expected**:
1. Search returns 2 items from local DB
2. Modal appears: "Found only 2 items. Search external sources?"
3. Yes/No buttons
4. User clicks "Yes"
5. Reasoning proceeds to fetch from proxy (post-demo feature)

### Scenario 3: Timeout Handling
**Prompt**: Any prompt triggering interactive question
**Expected**:
1. Modal appears
2. User ignores it for 5+ minutes
3. Kernel times out and uses default value
4. Reasoning continues with fallback behavior
5. Trace shows: `"User response timeout"`

## Future Enhancements

- **Multi-step wizards**: Chain multiple prompts for complex data gathering
- **Validation**: Client-side input validation before submission
- **Streaming updates**: Show progress while waiting for user input
- **History**: Log all user responses for audit trail
- **Conditional prompts**: More sophisticated decision trees based on prior responses
- **Rich media**: Support for image/file upload in prompts
- **Collaborative mode**: Multi-user session with voting/consensus mechanisms

## Files Modified

**Backend**:
- `apps/kernel/modules/sessions.py` (NEW)
- `apps/kernel/modules/interactive.py` (NEW)
- `apps/kernel/main.py` (modified)
- `apps/kernel/modules/playbook.py` (modified)
- `apps/kernel/modules/context.py` (modified)
- `apps/kernel/modules/evidence_module.py` (modified)

**Frontend**:
- `website/components/app/UserPrompt.tsx` (NEW)
- `website/hooks/useReasoningStreamV2.ts` (modified)
- `website/components/app/AppWorkspace.tsx` (modified)

## Performance Considerations

- Sessions held in memory (acceptable for demo scale)
- For production: consider Redis/database-backed session store
- Event queues are bounded (default: asyncio.Queue with no limit)
- Consider adding queue size limits for high-traffic scenarios
- Background cleanup runs at fixed interval (tunable via env var)

## Debugging

**Check active sessions**:
```python
from modules.sessions import get_session_manager
mgr = get_session_manager()
print(f"Active sessions: {len(mgr.sessions)}")
```

**Trace logs**:
All interactive prompts/responses logged to `/var/log/tpa/traces/{session_id}.jsonl`:
```json
{"t":"2025-11-02T22:15:30Z","step":"user_selected_authority","output":{"selected":"Westminster"}}
```

**Frontend console**:
- `currentPrompt` state changes logged automatically
- Network tab shows POST requests to `/respond` endpoint
- Check for 404/500 errors if responses not working

---

**Status**: ✅ Complete and ready for testing
**Next Step**: End-to-end testing with real user interaction scenarios
