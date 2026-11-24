### Frontend UI/UX Specification for Multi-Choice Extract Toolkit


### Goals
- Build the UI/UX for a system that extracts Questions–Answers (Q&A) from files grouped by collections, aligned with the existing APIs.
- Fully cover: sign-in/sign-up, collection management, file management in a collection (add/delete/reorder), execution and real-time progress (streaming), collection details and Q&A display, re-execution/retry of collections.


### Frontend Architecture
- SPA (React/Vue/Svelte) + client-side router.
- State management: Redux/Zustand/Pinia/Context (choose per stack).
- HTTP client with interceptor to attach Authorization header.
- WebSocket client for streaming progress.
- Store `access_token` in memory; keep `refresh_token` for session longevity (consider secure storage and security implications if persisting).


### Global Config
- API Base URL (example): `http://localhost:3333/api`
- All endpoints return `BaseResponse`:

```json
{
  "message": "Success | Error | ...",
  "status_code": 200,
  "data": any
}
```

- Protected endpoints require header: `Authorization: Bearer <access_token>` (all except `auth/register`, `auth/login`).


### Primary Pages
1) Sign in / Sign up
- Sign-in form: username, password → `POST /auth/login`.
- Sign-up form: username, email, password → `POST /auth/register`.
- Store `access_token` + `refresh_token`. Add interceptor to inject token and handle 401 gracefully.
- UX: clear error messages, show/hide password, optional “Remember me” (with security notice).

2) Collections Dashboard
- Table/cards of all user collections: `GET /collection/get-all`.
- Columns: Name, Status (`PENDING | PROCESSING | COMPLETED | FAILED`), Created At, Updated At, Actions.
- “Create collection” button → modal.
- Quick actions per row:
  - View details
  - Execute (if not PROCESSING)
  - Retry (if `COMPLETED` or `FAILED`)
- Filters by status, search by name.

3) Create Collection Modal
- Field: `name` (required).
- Call `POST /collection/create` with payload `{ name, user_id, processing_status? }`. Note: backend schema includes `user_id`, derive from token/session.
- On success: navigate to collection detail page.

4) Collection Detail Page
- Header: collection name, status badge, created/updated timestamps.
- Tabs:
  - Files: manage files within the collection
  - Q&A: display extracted questions and answers
  - Progress: show live progress bar/log while processing

4.1) Files Tab
- List files via `GET /file/get-all/{collection_id}`.
- Columns: Preview (image if applicable), URL, `page_order`, Created At, Actions (Delete).
- Add new file:
  - API accepts a `url` (no binary upload in current API). UI options:
    - Input a direct URL, or
    - Integrate an uploader to a storage service and use the resulting URL.
  - Call `POST /file/create` with `{ collection_id, url, page_order }`.
- Reorder files:
  - Drag & drop to change `page_order`.
  - On drop: `PUT /collection/update-file-orders/{collection_id}` with:

```json
{
  "file_orders": [
    { "file_id": 123, "new_page_order": 1 },
    { "file_id": 456, "new_page_order": 2 }
  ]
}
```

- Delete file: `DELETE /file/delete/{file_id}` with confirmation.
- UX:
  - If collection is PROCESSING: lock reorder/delete to avoid race conditions.
  - Validate `page_order` as contiguous 1..N before sending.

4.2) Q&A Tab
- Fetch `GET /collection/get-qa/{collection_id}`.
- Display as accordion/list per question:
  - Question fields: `code`, `type`, `html_content`, `reference`, `created_at`.
  - Answers list: `label`, `html_content`, `is_correct` (clearly mark the correct answer).
- Features:
  - Search by `code`, filter by `type`.
  - Optionally link to source page/file with `source_file_id`.
- Empty state: instruct users to “Add files and Execute to generate Q&A”.

4.3) Progress Tab (Streaming)
- On “Execute”, call `POST /collection/execute/{collection_id}` → response `data` contains `task_id`.
- WebSocket streaming:
  - Endpoint: `ws://<host>/api/collection/ws/progress/{session_id}/{collection_id}?token=<JWT_TOKEN>`
  - Note: backend currently publishes on channel `extract_qa_task_{collection_id}`; `session_id` isn’t used in the channel name. Use a fixed `"1"` until API evolves.
  - Each message is a JSON-encoded `ProgressMessage`:

```json
{
  "task_id": "celery-task-id",
  "step": "PREPROCESSING | EXTRACTING | COMPLETED",
  "percent": 0..100,
  "status": "Processing... | Completed | Failed"
}
```

- Show progress bar and live logs. On `COMPLETED`, update UI status to COMPLETED (or refetch).
- Fallback polling if WS fails: `GET /collection/get-result/{task_id}` until done or error.

4.4) Collection Actions
- Execute: `POST /collection/execute/{collection_id}` (enable only if there is at least one file).
- Retry: call Execute again regardless of `COMPLETED`/`FAILED` to create a new task.
- Cancel/Stop: (not provided by API) – keep disabled or propose backend change later.


### API Endpoints and Integration
- Auth
  - `POST /auth/register`: `{ username, email, password }`
  - `POST /auth/login`: `{ username, password }` → returns:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

  - `POST /auth/verify-token` (optional/internal)
  - Logout: client-side token deletion.

- Collections
  - `POST /collection/create`
  - `GET /collection/get-all`
  - `GET /collection/get/{collection_id}`
  - `POST /collection/execute/{collection_id}`
  - `PUT /collection/update-file-orders/{collection_id}`
  - `GET /collection/get-result/{task_id}`
  - `GET /collection/get-qa/{collection_id}`
  - `WS /collection/ws/progress/{session_id}/{collection_id}?token=...`

- Files
  - `POST /file/create`
  - `GET /file/get/{file_id}`
  - `GET /file/get-all/{collection_id}`
  - `DELETE /file/delete/{file_id}`


### Suggested TypeScript Types
```ts
export type ProcessingStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface BaseResponse<T = any> {
  message: string;
  status_code: number;
  data: T;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface Collection {
  id: number;
  name: string;
  user_id: number;
  processing_status: ProcessingStatus;
  created_at: string;
  updated_at: string;
}

export interface FileItem {
  id: number;
  collection_id: number;
  url: string;
  page_order: number;
  created_at: string;
}

export interface Answer {
  id: number;
  html_content: string;
  is_correct: boolean;
  label: string;
  created_at: string;
}

export type QuestionType = 'MULTIPLE_CHOICE' | 'READING_COMPREHENSION' | 'TRUE_FALSE';

export interface QAItem {
  id: number;
  source_file_id: number;
  type: QuestionType;
  html_content: string;
  reference: string;
  code: string;
  created_at: string;
  answers: Answer[];
}

export interface ProgressMessage {
  task_id: string;
  step: string;
  percent: number;
  status: string;
}
```


### Core Flows (Pseudo)
```ts
// Login
const res = await api.post<BaseResponse<AuthTokens>>('/auth/login', { username, password });
saveTokens(res.data.data);

// Get collections
const res = await api.get<BaseResponse<Collection[]>>('/collection/get-all');
setCollections(res.data.data);

// Create collection
await api.post('/collection/create', { name, user_id });

// Add file by URL
await api.post('/file/create', { collection_id, url, page_order });

// Reorder files
await api.put(`/collection/update-file-orders/${collectionId}`, { file_orders });

// Execute collection
const exec = await api.post<BaseResponse<string>>(`/collection/execute/${collectionId}`);
const taskId = exec.data.data;

// Stream progress
const ws = new WebSocket(`${WS_BASE}/api/collection/ws/progress/1/${collectionId}?token=${accessToken}`);
ws.onmessage = (e) => updateProgress(JSON.parse(e.data));

// Fallback polling
const result = await api.get(`/collection/get-result/${taskId}`);

// Fetch QA
const qa = await api.get<BaseResponse<QAItem[]>>(`/collection/get-qa/${collectionId}`);
```


### Auth, Permissions, Security
- Guard protected routes: redirect to sign-in if no `access_token`.
- On 401: redirect to sign-in; consider refresh-token flow (API already returns `refresh_token`; a dedicated refresh endpoint can be added later).
- Hide Execute action if no files exist.
- Lock write actions while `PROCESSING`.
- Warn the user before navigating away during processing.


### UX Enhancements
- Toast notifications for success/failure.
- Skeletons for loading states.
- Helpful empty states with guidance.
- Clear drag-and-drop reorder visuals; confirm when discarding unsaved changes.
- Q&A search/filter by `type` and `code`; keyword highlight.
- Quick copy of question `code`.
- Pagination/virtualized lists for large Q&A sets.
- Client-side export Q&A to CSV/JSON when `COMPLETED`.
- Realtime status badges in collections list with periodic auto-refresh.


### Minimal Happy-Path Tests
- Sign up → sign in → access dashboard.
- Create collection → add ≥1 file → reorder → Execute → see streaming → COMPLETED → view Q&A.
+- Delete a file → reorder → Execute again → COMPLETED.
- FAILED case → retry to success.


### Layout Suggestions
- Header: logo, app name, user menu (sign out).
- Sidebar: Collections, Settings (optional).
- Content:
  - Dashboard: collections table + filter + create button.
  - Detail: Tabs Files / Q&A / Progress. Prominent Execute/Retry actions.


### Technical Notes
- WebSocket requires JWT token in query `?token=<JWT>` (server verifies before accepting).
- Server publishes progress to `extract_qa_task_{collection_id}`; `session_id` is currently not part of the channel. Use `"1"` as temporary client parameter to match backend until updated.
- `POST /file/create` accepts only URL. If upload is needed, add an upload service and use the resulting URL.


### Endpoint Quick Reference
- Auth:
  - POST `/auth/register`
  - POST `/auth/login`
  - POST `/auth/verify-token` (optional)
- Collection:
  - POST `/collection/create`
  - GET `/collection/get-all`
  - GET `/collection/get/{collection_id}
  - GET `/collection/get-qa/{collection_id}`
  - POST `/collection/execute/{collection_id}`
  - GET `/collection/get-result/{task_id}`
  - PUT `/collection/update-file-orders/{collection_id}`
  - WS  `/collection/ws/progress/{session_id}/{collection_id}?token=...`
- File:
  - POST `/file/create`
  - GET `/file/get/{file_id}`
  - GET `/file/get-all/{collection_id}`
  - DELETE `/file/delete/{file_id}`


