# R06 — مسیر عمومی و ورودی‌های ثبت‌نام

تاریخ: 2026-10-21

## وضعیت

**IN_PROGRESS — FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_BROWSER**

R06 بعد از R07 انجام شد چون R06 پیش‌نیاز R08 است و قبلاً به‌خاطر R02 عقب افتاده بود. بخش مستقل از طراحی اکنون پیاده شده است؛ CTA نهایی لندینگ هنوز عمداً اضافه نشده، چون R02 محل، متن و ظاهر آن را تثبیت نکرده است.

## تغییرات انجام‌شده

### 1. مسیر عمومی `/register`

- `RegisterPage` به PublicLayout اضافه شد و refresh مستقیم `/register` اکنون route معتبر دارد.
- صفحه از همان `authApi.beginRegistration()` پیاده‌شده در R04 استفاده می‌کند؛ URL ثبت‌نام یا endpoint ساخت حساب دیگری ساخته نشده است.
- `/login` و جریان `beginLogin()` بدون تغییر رفتاری باقی مانده‌اند.

### 2. رفتار نشست

- فقط `isUsableSession(session)` می‌تواند کاربر را از `/register` به خانه نقش خودش هدایت کند.
- نشست منقضی/نامعتبر به‌عنوان نشست معتبر پذیرفته نمی‌شود؛ AuthProvider موجود نیز آن را از storage پاک می‌کند.
- مقصد از `session.user.primaryRole` معتبر می‌آید و query parameter دلخواه مسیر نقش را تعیین نمی‌کند.

### 3. loading / error / retry

- شروع اولیه registration rejected promise بدون handler ندارد.
- failure شروع سرویس به حالت خطا می‌رود و retry قابل‌دسترسی دارد.
- retry نتیجه `beginRegistration()` را await می‌کند؛ اگر starter به دلیل همزمانی start نکرد، UI به حالت قابل‌تلاش برمی‌گردد.
- پیام loading `role=status` و `aria-live=polite` دارد؛ خطای شروع `role=alert` دارد.
- رشته‌های React برای fa و en اضافه شدند تا localeهای فعلی ناقص نشوند.

### 4. Back از Keycloak و PKCE رهاشده

بازگشت با Back می‌تواند همان document را از bfcache بازیابی کند یا `/register` را دوباره mount کند. در هر دو حالت نباید کاربر فوراً در loop انتقال قرار گیرد یا retry به lock قبلی گیر کند.

برای همین:

- اگر `gradian.auth.oidc_flow=registration` به‌همراه state و verifier هنوز موجود باشد، `/register` آن را به‌عنوان تلاش ناتمام تشخیص می‌دهد و به‌جای auto-redirect پیام «ثبت‌نام تکمیل نشده» و دکمه ادامه نشان می‌دهد.
- manual retry ابتدا material یک‌بارمصرف قبلی را پاک می‌کند و سپس PKCE تازه می‌سازد.
- lock داخلی `createAuthFlowStarter` بعد از تکمیل `assign()` آزاد می‌شود؛ lock فقط start در حال اجرا را dedupe می‌کند، نه صفحه‌ای را که بعداً از bfcache برگشته است.

### 5. CTA لندینگ

هیچ `to="/register"` به LandingPage اضافه نشد. این تصمیم عمدی است، نه فراموشی پیاده‌سازی. R02 هنوز `BLOCKED_DESIGN` است و طبق قرارداد پروژه محل و متن CTA نباید حدس زده شود. وقتی R02 تأیید شود، همین route آماده به CTA تأییدشده متصل می‌شود.

## فایل‌های تغییرکرده

- `frontend/src/app/router/AppRouter.tsx`
- `frontend/src/features/auth/pages/RegisterPage.tsx` — جدید
- `frontend/src/features/auth/api/authFlow.ts`
- `frontend/src/locales/fa/auth.json`
- `frontend/src/locales/en/auth.json`
- `frontend/tests/r04-auth-flow.cjs`
- `frontend/tests/r06-public-registration.cjs` — جدید
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`
- `docs/registration/R06_PUBLIC_ENTRY.md`

## تست‌های اجراشده

در این محیط واقعاً اجرا شد:

```text
R06 public registration contract: 17 checks passed.
R04 auth-flow tests: 7 scenario groups passed.
R07 callback tests: 6 scenario groups passed.
```

R06 contract مسیر `/register`، حفظ `/login`، استفاده از R04، session guard، Back/retry cleanup، semantics دسترس‌پذیری، localeهای fa/en و عدم اختراع CTA لندینگ را قفل می‌کند.

R04 regression نیز یک سناریوی تازه دارد که ثابت می‌کند بعد از start تکمیل‌شده، همان starter می‌تواند attempt تازه با state جدید آغاز کند؛ dedupe startهای همزمان همچنان برقرار است.

## مواردی که هنوز زنده تأیید نشده‌اند

در این محیط مرورگر واقعی/Keycloak واقعی اجرا نشد، پس موارد زیر PENDING_BROWSER هستند:

1. direct navigation و hard refresh روی `/register` در Vite/nginx deployment واقعی؛
2. Back واقعی از صفحه Keycloak با و بدون bfcache؛
3. خاموش بودن Core/Keycloak و retry بعد از روشن‌شدن سرویس؛
4. history/back behavior در Chrome/Firefox واقعی؛
5. CTA لندینگ پس از تأیید R02؛
6. مقایسه تصویری با مرجع تأییدشده ثبت‌نام.

## قدم بعد

R08 به R05/R06/R07 وابسته است. از نظر کد functional سه بخش موجودند، اما R05 و R06 هنوز به R02 و smoke زنده وابسته‌اند و R07 پذیرش live role/token ندارد. بنابراین R08 می‌تواند فقط به‌صورت **independent hardening** شروع شود و نباید پذیرش نهایی سفر کامل یا شواهد تصویری موفق ادعا کند تا این موانع بسته شوند.
