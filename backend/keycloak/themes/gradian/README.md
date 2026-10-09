# Gradian sign-in and registration pages (for the frontend team)

The login and registration pages are not part of the React app. Keycloak renders them, and this
folder is the theme that styles them. Today it is a basic design written by the backend team; you
will replace its look with the design system. You do not need to change any logic to do that.

## What a user sees, and what your app does

1. The landing page has two buttons, **ورود** and **ثبت‌نام**.
2. **ورود** starts the normal sign-in (Authorization Code with PKCE, client `gradian-web`) at
   Keycloak's authorization endpoint. Keycloak shows the *login page*.
3. **ثبت‌نام** starts the same request but at the *registration endpoint*. Keycloak shows the
   *registration page*. The login page also links to it, and the registration page links back.
4. After a successful registration Keycloak signs the person in and returns to your callback
   `${FRONTEND_URL}/auth/callback?code=...` exactly as after a login. Nothing else to do.
5. Your app exchanges the code for tokens, calls `GET /api/v1/me`, and routes to `home_path`.
   A new registrant is always a **student** (`/student`). They have no `field_of_study` yet; collect
   it with `PATCH /api/v1/me` in a short first-visit step if the design needs it.

`GET /api/v1/auth/config` gives you everything:

```json
{
  "issuer": "http://localhost:8080/realms/gradian",
  "realm": "gradian",
  "client_id": "gradian-web",
  "registration_endpoint": "http://localhost:8080/realms/gradian/protocol/openid-connect/registrations",
  "end_session_url": "http://localhost:8080/realms/gradian/protocol/openid-connect/logout",
  "landing_url": "http://localhost:5173/"
}
```

With `oidc-client-ts`, keep one `UserManager` for sign-in. For sign-up, create a second one with the
same settings but `metadata: { ...metadata, authorization_endpoint: registration_endpoint }` and
call `signinRedirect()` on it. The redirect URI, scopes and PKCE settings must be identical.
(Keycloak 26.0.8 ignores `prompt=create`, so do not rely on it.)

Redirect URI: `${FRONTEND_URL}/auth/callback`. Post-logout URI: `${FRONTEND_URL}/`. If you change
`FRONTEND_URL` run `make reset`, because Keycloak reads it only when it first imports the realm.

## Rules the pages enforce (do not duplicate them in the app)

| Field | Rule |
| --- | --- |
| First name, last name | 1 to 100 characters: letters, spaces, zero-width non-joiner |
| Mobile number (the username) | `09` followed by 9 digits, English digits, not already registered |
| Email | A valid address, not already registered |
| Password | At least 8 characters, and the confirmation must match |

Errors come from Keycloak in Persian and appear under the field. Wrong sign-in details give one
message for every kind of failure, and five wrong passwords lock the account for a while.
There is no password recovery. Mobile numbers are not verified.

## What is in this folder

```
login/
  theme.properties         parent=base, and the list of stylesheets
  template.ftl             the page frame: brand, title, message box, footer
  login.ftl                the login form
  register.ftl             the registration form
  resources/
    css/gradian.css        every colour, size and font: start here
    fonts/  img/           put the design system's fonts and images here
```

- **Restyling.** Edit `resources/css/gradian.css`. Colours, radius and font are CSS variables at the
  top. Load a font by adding an `@font-face` that points at `../fonts/<file>` and putting its name
  first in `--font`. Do not load fonts from a CDN: the pages must work offline.
- **Layout and wording.** Edit the `.ftl` files. They are plain HTML with a few Keycloak
  placeholders. Keep these as they are, or the forms stop working:
  `action="${url.loginAction}"` and `action="${url.registrationAction}"`; the field names
  `username`, `password`, `rememberMe`, `firstName`, `lastName`, `email`, `password-confirm`;
  `${url.registrationUrl}` and `${url.loginUrl}` for the links between the pages; the error lines
  that print `messagesPerField.get(...)`; and `${kcSanitize(message.summary)?no_esc}`.
- **Other pages.** Keycloak also shows an error page and an info page. They reuse `template.ftl`, so
  they take on your look automatically.
- **Direction and language.** The pages are Persian and right-to-left (`dir="rtl"` in `template.ftl`).

## Trying your changes

`make start` mounts this folder into Keycloak, and in development Keycloak does not cache themes:
edit a file, refresh the browser. You do not need the React app running to test either page.

**Open each page on its own.** Paste one of these into the browser. The `code_challenge` is a fixed
test value (its verifier is below), and the redirect URI must be `${FRONTEND_URL}/auth/callback`,
which is `http://localhost:5173/auth/callback` by default.

Login page:

    http://localhost:8080/realms/gradian/protocol/openid-connect/auth?client_id=gradian-web&response_type=code&scope=openid&redirect_uri=http://localhost:5173/auth/callback&code_challenge=oGWBphORiNZ_XxKnaA2dubEoOHkFKtBUsJysFnPwjso&code_challenge_method=S256

Registration page:

    http://localhost:8080/realms/gradian/protocol/openid-connect/registrations?client_id=gradian-web&response_type=code&scope=openid&redirect_uri=http://localhost:5173/auth/callback&code_challenge=oGWBphORiNZ_XxKnaA2dubEoOHkFKtBUsJysFnPwjso&code_challenge_method=S256

The login page links to the registration page and back, and shows Keycloak's Persian error for a
wrong password. Seeded users are listed in `build/credentials/users.csv` (made by `make users`).

**Finish a sign-in without the frontend.** After a successful login or registration the browser is
sent to `http://localhost:5173/auth/callback?...&code=<CODE>`. If nothing is running on port 5173 the
browser shows "can't connect", which is fine: copy the `code` value from the address bar and
exchange it within a minute:

    curl -s -d grant_type=authorization_code -d client_id=gradian-web \
      -d redirect_uri=http://localhost:5173/auth/callback -d code=<CODE> \
      -d code_verifier=gradian-local-test-verifier-0123456789-ABCDEFGHIJKLMNOP \
      http://localhost:8080/realms/gradian/protocol/openid-connect/token

The answer holds an `access_token`; use it as `Authorization: Bearer ...` on
`http://localhost:8000/api/v1/me`. (The `code_challenge` above is the S256 hash of that verifier;
a real app generates a new pair for every sign-in.) Each URL gives a code only once, so open the
page again for another try.

Other entry points are not these pages: `/realms/gradian/account` is Keycloak's own account
console, and `prompt=create` does not open registration in Keycloak 26.0.8.

Create a real account to test with, then delete it in the console (http://localhost:8080,
`KEYCLOAK_ADMIN_USER`) under Users. Seeded users can sign in with the password in `.env`.

## Delivering a finished design

Replace the contents of `login/` (keeping the file names and the placeholders above) and open a
pull request. For a deployed environment the folder is copied into the Keycloak image at
`/opt/keycloak/themes/gradian`, and production caches themes, so Keycloak must be restarted after a
change.
