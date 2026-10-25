# Frontend team applications

Each `teamN/` directory is an independent frontend application. A team may use React, Angular, Vue, Svelte, or plain HTML/CSS/JavaScript. It owns its build, dependencies, UI and API integration.

The central application in `../src` is the Gradian shell. It owns the landing page, authentication entry points, role panels, navigation and service registry. Team applications are opened from the shell by redirecting to the URL returned by the Core Service.

## Required integration contract

1. Use Authorization Code + PKCE against the `gradian` Keycloak realm.
2. Never put an access token in a URL or query string.
3. Send `Authorization: Bearer <access_token>` to the team backend.
4. Use the stable service key from the backend registry, for example `student.simulated-exam`.
5. Provide a health page or endpoint and document local start/build commands.
6. Use the same role and error semantics described in `../../backend/docs/06-integration-guide.md`.

Redirect is the default integration mode. iframe embedding is optional and should be enabled only after CORS, CSP, cookie and postMessage behavior have been reviewed.

The files in each team directory are a small framework-neutral starter. Replace them with the chosen framework when implementation begins.
