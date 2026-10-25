# R04 — شروع ثبت‌نام با PKCE در لایه Auth

تاریخ: 2026-10-21

## محدوده

این سشن فقط R04 را اجرا کرد. هدف اضافه‌کردن شروع self-registration روی همان Authorization Code + PKCE موجود بود، بدون ساخت فرم رمزدار موازی در React، بدون endpoint ساخت حساب در Core و بدون کتابخانه احراز هویت تازه. مسیر عمومی `/register` و CTAها متعلق به R06 هستند و قالب واقعی Keycloak متعلق به R05 است.

## تغییرات محصول

### helper مشترک Auth

فایل `frontend/src/features/auth/api/authFlow.ts` اضافه شد. این helper اکنون منطق مشترک login و registration را مالک است:

- تولید verifier تصادفی ۴۸ بایتی و state تصادفی ۲۴ بایتی؛
- SHA-256 و Base64URL برای `code_challenge`؛
- پارامترهای مشترک `client_id`، `response_type=code`، `scope=openid`، `redirect_uri`، `code_challenge_method=S256` و `state`؛
- ذخیره verifier/state در کلیدهای sessionStorage موجود؛
- lock مشترک شروع جریان.

`authApi.ts` از این helper استفاده می‌کند و `authApi.beginRegistration()` را صادر می‌کند. `beginLogin()` نیز از همان builder مشترک استفاده می‌کند و endpoint authorization قبلی را حفظ می‌کند.

### endpoint ثبت‌نام از config

R04 هیچ URL ثبت‌نام ثابتی تولید نمی‌کند. `registration_endpoint` از `GET /api/v1/auth/config` گرفته می‌شود. قبل از redirect این موارد بررسی می‌شوند:

- issuer و registration endpoint فقط HTTP(S) مطلق باشند؛
- username/password در URL وجود نداشته باشد؛
- query/hash از قبل تزریق نشده باشد؛
- registration endpoint با issuer هم-origin باشد؛
- path دقیقاً `${issuerPath}/protocol/openid-connect/registrations` باشد.

در config نامعتبر، هیچ verifier/state ذخیره نمی‌شود و مرورگر redirect نمی‌شود.

### رفتار همزمانی و retry

یک lock مشترک برای login/registration وجود دارد. وقتی یک شروع در حال گرفتن config یا ساخت challenge است، شروع دوم `false` برمی‌گرداند و جفت PKCE را overwrite نمی‌کند. این رفتار double click و اجرای دوباره effect در StrictMode را پوشش می‌دهد.

اگر config request، validation یا ساخت جریان شکست بخورد، lock آزاد می‌شود و retry می‌تواند با state/verifier تازه شروع شود. پس از redirect موفق lock عمداً تا ترک صفحه آزاد نمی‌شود.

### امنیت

- `code_verifier` در query string قرار نمی‌گیرد.
- verifier فقط در sessionStorage موجود نگه داشته می‌شود تا callback/token exchange فعلی مصرفش کند.
- client secret، password یا token جدیدی در این flow تولید/ثبت/log نمی‌شود.
- callback، token exchange، `/me`، role mapping و session persistence بازطراحی نشدند.

## فایل‌های تغییرکرده

- `frontend/src/features/auth/api/authFlow.ts` — جدید
- `frontend/src/features/auth/api/authApi.ts`
- `frontend/tests/r04-auth-flow.cjs` — جدید
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`
- `docs/registration/R04_PKCE_START.md` — این گزارش

## تست اجراشده

فرمان:

```bash
cd frontend
node tests/r04-auth-flow.cjs
```

نتیجه:

```text
R04 auth-flow tests: 6 scenario groups passed.
```

سناریوها:

1. registration endpoint واقعی config + تمام پارامترهای Authorization Code + PKCE S256؛
2. state و verifier تازه در تلاش مستقل؛
3. dedupe شروع همزمان و فقط یک config call/redirect؛
4. آزادشدن lock بعد از config failure و موفقیت retry؛
5. رد endpoint ناسازگار با issuer پیش از storage/redirect؛
6. regression ورود عادی و ادامه استفاده از `/protocol/openid-connect/auth`.

تست مستقیماً source واقعی `authFlow.ts` را با TypeScript transpile می‌کند؛ منطق موازی کپی‌شده برای نتیجه‌سازی استفاده نشده است. همچنین transpile syntax برای `authFlow.ts` و `authApi.ts` بدون خطای syntax انجام شد.

## محدودیت بررسی محیط

`npm ci` در این محیط به timeout شبکه خورد و dependency install کامل نشد، بنابراین build کامل Vite/React و regression مرورگری T04 در این سشن موفق اعلام نمی‌شود. تست R04 به Node + TypeScript سیستم وابسته بود و واقعاً اجرا شد.

Keycloak زنده نیز در این محیط اجرا نشد؛ بنابراین R04 اثبات نمی‌کند فرم registration واقعی رندر شده یا حساب ساخته شده است. آن پذیرش در R05/R07/R09 و پذیرش live R03 قرار دارد.

## وضعیت و قدم بعد

R04 معیارهای مستقل خودش را پوشش داده و **DONE** است. R03 همچنان از نظر runtime **PENDING_LIVE** است و R02 همچنان **BLOCKED_DESIGN**. بدون مرجع بصری، R05/R06 نباید با سلیقه عامل نهایی شوند.
