# Rexab — web frontend

Next.js (App Router) + TypeScript + Tailwind v4 client for the Rexab API ([../README.md](../README.md), [../api](../api)). Talks to the FastAPI backend only over HTTP — no business logic lives here.

## Running locally

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL, defaults to http://localhost:8000
npm run dev
```

The backend must be running and reachable at `NEXT_PUBLIC_API_URL`, with `CORS_ORIGINS` in its own `.env` including this app's origin (`http://localhost:3000` by default).

## Structure

```text
app/
├── login/, register/        public routes
└── (app)/                   route group wrapped in AppShell (sidebar/bottom nav),
    ├── dashboard/               redirects to /login if not authenticated
    ├── rooms/[id]/
    └── settings/
components/                  feature components (dialogs, lists) + components/ui (primitives)
lib/
├── api.ts                   typed fetch client, one function per backend endpoint
├── auth-context.tsx         JWT stored in localStorage, exposes useAuth()
└── format.ts                money/date formatting
types/api.ts                 TypeScript mirrors of the backend's Pydantic schemas
hooks/useRoomData.ts         fetches room + members + payments + settlements + dashboard together
```

Auth is a bearer JWT kept in `localStorage`, not cookies — pages that need a session are Client Components (`useAuth()`), since `localStorage` isn't available during server rendering.

## Known simplifications

- No global "all payments" / "all settlements" pages — the backend only exposes these scoped to a room (`GET /api/rooms/{id}/payments`, `.../settlements`), so the sidebar only links to Dashboard (which lists rooms) and Settings.
- "Add member" opens the invite-code/QR sharing dialog rather than a raw add-by-user-id form — see the `members` router's commit message for why a force-add capability wasn't built.
- Settings only shows the profile and a logout button; there's no profile-edit endpoint on the backend yet.
