# R07 — callback، نقش دانشجو و نشست پس از ثبت‌نام

تاریخ: 2026-10-21

## وضعیت

**IN_PROGRESS — IMPLEMENTED / PENDING_LIVE**

بخش کد و تست‌های مستقل R07 روی خروجی R05 پیاده شد. این سشن Keycloak/Django زنده را اجرا نکرد، بنابراین معیارهایی که به realm واقعی، grant واقعی role و صدور token تازه بعد از ورود مجدد وابسته‌اند هنوز پذیرش زنده می‌خواهند و R07 به‌صورت رسمی DONE اعلام نمی‌شود.

## مسئله‌ای که R07 بست

در baseline، کاربر بدون panel role در `gradian_auth.roles.resolve_panel` به‌صورت student تفسیر می‌شد. Core در اولین مشاهده Profile تلاش می‌کرد role `student` را در Keycloak grant کند، اما اگر Admin API همان بار شکست می‌خورد فقط log ثبت می‌شد. چون Profile دیگر وجود داشت، درخواست بعدی grant را retry نمی‌کرد و role واقعی می‌توانست برای همیشه از Keycloak جا بماند؛ در حالی که Core ظاهراً student را نمایش می‌داد.

هم‌زمان callback فرانت state/verifier را فقط بعد از token exchange موفق پاک می‌کرد، نوع flow آغازشده را نگه نمی‌داشت و retry خطا صرفاً کاربر را به `/login` می‌فرستاد. این برای registration، callback مصرف‌شده، state نامعتبر و خطاهای 409/502 قرارداد کافی نداشت.

## تغییرات frontend

### flow metadata و callback یک‌بارمصرف

`frontend/src/features/auth/api/authFlow.ts` اکنون علاوه بر verifier و state، نوع flow را در `gradian.auth.oidc_flow` با مقدار `login` یا `registration` ثبت می‌کند. این مقدار secret نیست و فقط برای recovery صحیح استفاده می‌شود.

فایل جدید `frontend/src/features/auth/api/authCallback.ts` قرارداد callback را متمرکز می‌کند:

- state برگشتی باید با state ذخیره‌شده یکسان باشد؛ این بررسی حتی برای `error=...` ارائه‌دهنده هم انجام می‌شود؛
- `access_denied` به حالت cancellation مشخص تبدیل می‌شود؛
- code یا verifier گمشده callback نامعتبر است؛
- 400، 401، 403، 409 و 502/503/504 به failureهای مشخص تبدیل می‌شوند؛
- flow اصلی همراه failure نگه داشته می‌شود تا retry همان registration/login را از نو شروع کند؛
- state، verifier و flow در تمام پایان‌های callback پاک می‌شوند تا code/state مصرف‌شده دوباره استفاده نشوند.

### ترتیب ساخت نشست

`authApi.finishLogin()` همچنان همان callback مشترک login/registration است، اما ترتیب را صریح نگه می‌دارد:

1. اعتبارسنجی callback state/code/verifier؛
2. config واقعی و token endpoint؛
3. Authorization Code exchange؛
4. اعتبارسنجی حداقلی token response؛
5. `GET /api/v1/me` با access token؛
6. role mapping معتبر؛
7. `isUsableSession`؛
8. تحویل session به `AuthProvider` برای persist.

قبل از این مراحل session تازه ذخیره نمی‌شود. 401/403/409/provider outage و token/callback نامعتبر هیچ session جعلی نمی‌سازند.

### جلوگیری از نمایش کاربر قبلی

`AuthCallbackPage` در شروع callback `setSession(null)` می‌زند. طبق قرارداد موجود `AuthProvider`، این کار query و mutation cache خصوصی React Query را cancel/clear می‌کند. پس در حین callback کاربر تازه، session/cache کاربر قبلی باقی نمی‌ماند.

Retry دیگر callback مصرف‌شده را دوباره اجرا نمی‌کند؛ `authApi.retryCallback(retryFlow)` یک PKCE flow تازه از همان نوع قبلی شروع می‌کند.

## تغییرات backend

### retry-safe student grant

`backend/core/accounts/authentication.py` دیگر grant student را به `Profile` تازه‌ساخته‌شده محدود نمی‌کند. هر token انسانی که هیچ panel role ندارد، بعد از sync Profile و کنترل فعال‌بودن حساب باید default role واقعی را ensure کند.

`backend/packages/gradian-keycloak/.../admin_client.py` متد `ensure_role` دارد:

- role mapping فعلی کاربر را می‌خواند؛
- اگر role وجود دارد no-op است؛
- اگر وجود ندارد از `grant_role` موجود استفاده می‌کند.

این رفتار باعث می‌شود token اولیه roleless بتواند چند بار `/me` بزند بدون grant تکراری، و اگر اولین Admin API call شکست خورد درخواست بعدی دوباره تلاش کند.

### provider failure دیگر موفقیت نمایشی نیست

`accounts.profiles.grant_default_role` در failure Admin API اکنون `IdentityProviderUnavailableError` می‌دهد. نتیجه HTTP در Core برابر 502 است و `/me` موفق نمی‌شود. Profile ممکن است قبلاً ساخته شده باشد، اما retry بعدی همچنان role را ensure می‌کند؛ بنابراین وجود cache محلی مانع recovery نیست.

## نقش token اولیه و token تازه

توکنی که بلافاصله از self-registration برمی‌گردد ممکن است قبل از grant role صادر شده باشد و claim `student` نداشته باشد. Core آن را طبق قرارداد roleless=student تفسیر می‌کند، اما از R07 فقط وقتی `/me` موفق می‌شود که role durable در Keycloak ensure شده باشد.

این توکن جاری خودبه‌خود بازنویسی نمی‌شود. برای سرویس‌های دیگری که role را مستقیماً از access token می‌خوانند، باید بعد از ورود مجدد/صدور token تازه claim `student` دیده شود. R07 عمداً refresh خودکار، silent SSO یا قرارداد تازه بین سرویس‌ها اضافه نکرده است.

## هویت و field_of_study

Profile همچنان از claims معتبر `sub`، `preferred_username`، `email`، `given_name` و `family_name` ساخته/به‌روز می‌شود. conflict یکتایی cache همان 409 موجود را می‌دهد. `field_of_study` خالی است و خالی‌بودن آن مانع `/me` یا پنل دانشجو نیست؛ test صریح برای این رفتار اضافه شد.

## فایل‌های تغییرکرده

- `frontend/src/features/auth/api/authFlow.ts`
- `frontend/src/features/auth/api/authCallback.ts` — جدید
- `frontend/src/features/auth/api/authApi.ts`
- `frontend/src/features/auth/pages/AuthCallbackPage.tsx`
- `frontend/src/locales/fa/auth.json`
- `frontend/src/locales/en/auth.json`
- `frontend/tests/r07-callback.cjs` — جدید
- `backend/core/accounts/authentication.py`
- `backend/core/accounts/profiles.py`
- `backend/core/accounts/tests/test_authentication.py`
- `backend/core/accounts/tests/test_me.py`
- `backend/packages/gradian-keycloak/src/gradian_keycloak/admin_client.py`
- `backend/packages/gradian-keycloak/src/gradian_keycloak/tests/test_admin_client.py`
- `backend/packages/gradian-testing/src/gradian_testing/fakes.py`
- `backend/packages/gradian-testing/src/gradian_testing/tests/test_tokens.py`
- `backend/scripts/tests/test_r07_identity_contract.py` — جدید
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`
- `docs/registration/R07_IDENTITY.md`

## تست‌های اجراشده در این سشن

### frontend R07

```bash
cd frontend
node tests/r07-callback.cjs
```

نتیجه:

```text
R07 callback tests: 6 scenario groups passed.
```

سناریوهای اصلی: registration callback معتبر، state mismatch، cancellation ارائه‌دهنده، callback ناقص، نگاشت statusهای 400/401/403/409/502 و قرارداد cleanup/retry/no-old-session.

### regression R04

```bash
node tests/r04-auth-flow.cjs
```

نتیجه:

```text
R04 auth-flow tests: 6 scenario groups passed.
```

پس ذخیره flow metadata قرارداد PKCE R04 را نشکسته است.

### backend contract

```bash
cd backend
python3 -m unittest scripts.tests.test_r07_identity_contract -v
```

نتیجه:

```text
Ran 5 tests
OK
```

همچنین `py_compile` روی فایل‌های Python تغییرکرده و parse هر دو JSON Keycloak موفق بود. فایل‌های fast Django test نیز با سناریوهای failure→retry، Profile موجود+token roleless، token تازه student و field_of_study خالی توسعه داده شدند.

## محدودیت محیط و پذیرش زنده باقی‌مانده

در محیط ساخت این artifact، dependencyهای Django/DRF نصب نبودند و stack Docker/Keycloak واقعی اجرا نشد. بنابراین test suite کامل Django و موارد زیر موفق اعلام نمی‌شوند:

1. self-registration واقعی و callback با token roleless؛
2. مشاهده `student` در Admin API/realm بعد از `/me`؛
3. شبیه‌سازی outage Admin API و مشاهده 502 سپس recovery واقعی بدون حذف Profile؛
4. login مجدد و مشاهده claim `student` در access token تازه؛
5. تأیید اینکه group service با token تازه نقش student را می‌بیند؛
6. regression مرورگری کامل با Keycloak واقعی.

برای بستن R07 به DONE، این موارد باید روی stack موجود و بدون `make reset` یا حذف volume اجرا شوند.
