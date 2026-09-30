# SkillBridge Student Workspace

The student frontend is a React single-page app built with Vite. It calls the existing Flask API; all scores, assessment results, role matches, skill gaps, and recommendations are returned by the backend.

## Run locally

1. Start the Flask backend using the setup in `../backend/README.md` (default `http://localhost:5001`).
2. Install Node.js 20 or later.
3. From this directory, run `npm install` and `npm run dev`.
4. Open `http://localhost:5173` and create a student account or sign in.

Vite proxies `/api` to `http://127.0.0.1:5001` by default, following `PORT` in the root/backend `.env`. Set `API_PROXY_TARGET` for a custom proxy target. Restart both servers after changing ports. To use a different API origin, copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.

## Build and tests

```sh
npm run build
npm test
```

JWTs are stored in browser local storage and attached by the centralized API client. A 401 response clears the local session. Resume and AI suggestions remain visibly unverified and are not written to student skills by the frontend.
