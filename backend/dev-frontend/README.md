# Sign-in tester

A throwaway page for trying the sign-in flow and the API by hand. It is **not** the real frontend and
is never deployed. It uses the same library (`oidc-client-ts`) and the same steps as
`docs/05-frontend-guide.md`, so what works here works in the React app.

    make dev-frontend        # in backend/; starts the system if needed
    open http://localhost:5173

It is served on port 5173, the origin Keycloak already allows (`FRONTEND_URL`), and `/api/` is
proxied to Core, so the browser sees one origin. Stop it with `make stop`. Do not run it together
with the real frontend: both want port 5173.

What to try, in order:

1. **GET /api/v1/auth/config** shows what Core tells the frontend.
2. **Sign in** sends you to the themed Keycloak page. Use a user from `build/credentials/users.csv`
   (`make users`; the first student is `09001000001`, the first admin `09005000001`, the password
   is `SEED_DEFAULT_PASSWORD`). You come back to `/auth/callback`, and the page shows the panel and
   `home_path` it would route to.
3. **Session** shows the token audience (it must contain `gradian-core` and your group), the realm
   roles, and a countdown. Tokens last 10 minutes and are renewed in the background; **Renew token
   now** does it by hand.
4. **Register** opens the registration page; the new person is a student. Right after registering
   the token has no `student` role yet: renew once and it appears (Core grants it on the first call).
5. **GET /admin/users**, **GET /internal/users** and **GET /me without a token** show the 403 and
   401 answers.
6. **Panel content** has one button per panel endpoint: `/landing` (no token), `/panel`, `/panel/services`, `/student/dashboard` (students only, 403 otherwise) and `/notifications`.
7. The log at the bottom shows every call and every token event. Add `?debug` to the address to
   also print the library's own debug output in the browser console.

Files: `public/index.html`, `public/app.js` (the whole flow, about 100 lines),
`public/oidc-client-ts.min.js` (oidc-client-ts 3.5.0, Apache-2.0, vendored so it works offline),
`nginx.conf`.
