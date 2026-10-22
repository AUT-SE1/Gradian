# R09 — آزمون یکپارچه و Regression ثبت‌نام

تاریخ: 2026-10-21

## وضعیت

**IN_PROGRESS — STATIC/CONTRACT PRECHECK COMPLETE / BLOCKED_BY_R08 / PENDING_BUILD_BROWSER_LIVE**

R09 طبق قرارداد پروژه به R08 وابسته است. R08 هنوز به‌علت نبود مرجع R02 و اجرای browser/live در وضعیت `IN_PROGRESS` است؛ بنابراین این سشن فقط بخش تکرارپذیر و غیرزنده R09 را انجام داده و پذیرش یکپارچه نهایی یا موفقیت ثبت‌نام زنده ادعا نمی‌شود.

## دامنه این سشن

- هیچ کد محصول، endpoint، dependency، realm data یا حساب کاربری تغییر نکرد.
- دو قرارداد تست جدید برای مرزهای integration ثبت‌نام افزوده شد:
  - `frontend/tests/r09-registration-contract.cjs`
  - `backend/scripts/tests/test_r09_registration_contract.py`
- runner تکرارپذیر non-live افزوده شد:
  - `scripts/r09-registration-preflight.sh`
- regressionهای R03/R04/R05/R06/R07/R08 و کل suite مستقل `backend/scripts/tests` اجرا شدند.
- build/lint/typecheck، Playwright/Chromium و Keycloak/Core زنده نیز تلاش/بررسی شدند، اما محدودیت محیط مانع اجرای معتبر کامل شد؛ این موارد موفق گزارش نمی‌شوند.

## نتیجه تست‌های قابل اجرا

فرمان اصلی:

```bash
./scripts/r09-registration-preflight.sh
```

نتیجه واقعی این سشن:

- R04 auth-flow: **7** گروه سناریو موفق.
- R06 public registration: **17** check موفق.
- R07 callback: **6** گروه سناریو موفق.
- R08 React accessibility/display: **28** check موفق.
- R09 frontend integration contract: **22** check موفق.
- R03 identity rules: **4** تست موفق.
- R05 Keycloak theme contract: **6** تست موفق.
- R07 backend identity contract: **5** تست موفق.
- R08 Keycloak accessibility contract: **7** تست موفق.
- R09 backend registration contract: **5** تست موفق.
- کل `backend/scripts/tests` با `PYTHONPATH` صحیح: **125** تست موفق.
- parse دو JSON اصلی Keycloak: موفق.
- `py_compile` فایل‌های هویت تغییرکرده: موفق.
- `node --check` تست جدید R09: موفق.

قرارداد R09 در این تست‌ها این موارد را نگه می‌دارد: `/register` و `/login` و callback مشترک، registration endpoint از config واقعی، PKCE S256/state، نرفتن verifier داخل URL، ساخت session فقط بعد از `/me` معتبر، پاک‌سازی transient auth هنگام logout، نبود password/role selection در React، استفاده از فرم provider-owned Keycloak، نبود public Core registration endpoint موازی، `passwordPolicy=length(8)`، duplicate email ممنوع و اعطای durable student پیش از موفقیت `/me` برای token بدون نقش.

## build / lint / typecheck

`frontend/node_modules` در ورودی موجود نبود. تلاش برای نصب dependency انجام شد، اما محیط اجرای این سشن به npm registry دسترسی DNS نداشت:

```text
npm ping https://registry.npmjs.org/
EAI_AGAIN registry.npmjs.org
```

`npm ci --offline` نیز به‌درستی گزارش کرد cache کامل نیست (`zod-validation-error-4.0.2.tgz` موجود نبود). به همین دلیل اجرای فعلی:

```bash
npm run build
npm run lint
npm run typecheck
```

به‌علت dependencyهای نصب‌نشده معتبر نیست و شکست آن به‌عنوان regression محصول ثبت نمی‌شود. خطاهای مشاهده‌شده شامل نبود type/moduleهای Vite/React/Node و نبود binary `eslint` بود. روی محیطی که `npm ci` کامل موفق است این سه فرمان باید دوباره اجرا شوند.

## Browser regression

تست‌های موجود T04 تا T12 نیازمند Playwright/Chromium نصب‌شده در محیط‌اند و dependency محصول نیستند. تلاش مستقیم در این محیط با `MODULE_NOT_FOUND: playwright` متوقف شد. بنابراین موارد زیر هنوز اجرا نشده‌اند:

- direct/refresh `/register` در مرورگر واقعی؛
- نشست موجود و منقضی؛
- double click / چند tab؛
- regression ورود/خروج چهار نقش، 401/403 و cache cleanup در browser harness؛
- matrix موبایل/RTL/LTR/light/dark با browser؛
- screenshot comparison ثبت‌نام که همچنان به R02 وابسته است.

این موارد نباید با تست‌های source-level موفق اشتباه گرفته شوند.

## Live Keycloak/Core

در محیط این سشن executable/daemon Docker موجود نبود؛ بنابراین هیچ stack زنده‌ای بالا نیامد و هیچ حساب آزمایشی ساخته نشد. موارد پذیرش زنده R09 هنوز بازند:

1. self-registration واقعی با یک حساب تست مجزا؛
2. callback معتبر، ساخت Profile و ورود به student panel؛
3. logout و login مجدد همان حساب؛
4. وجود role `student` در Keycloak و token تازه بعد از login مجدد؛
5. رد duplicate mobile/email، password mismatch، password کوتاه و نام نامعتبر؛
6. callback invalid/consumed، قطع config/Keycloak/Core و recovery؛
7. تلاش برای role escalation با دست‌کاری field/parameter؛
8. regression چهار نقش و سرویس‌های فعلی روی stack واقعی.

برای اجرای live از credential واقعی در report/artifact استفاده نشود. حساب‌های تست باید نام و شماره کاملاً ساختگی و قابل شناسایی داشته باشند و فقط همان حساب‌های مشخص پس از آزمون پاک شوند؛ data/volume عمومی حذف نشود.

## وابستگی رسمی

R08 هنوز `IN_PROGRESS (FUNCTIONAL HARDENED / BLOCKED_DESIGN / PENDING_BROWSER_LIVE)` است. در نتیجه R09 در این تحویل فقط precheck شده و `DONE` نیست. برای بستن R09، ابتدا R08 باید معیارهای مستقل خودش را ببندد و سپس build/browser/live matrix همین گزارش اجرا و نتیجه واقعی ثبت شود.

## فایل‌های افزوده/تغییریافته در R09

- `frontend/tests/r09-registration-contract.cjs`
- `backend/scripts/tests/test_r09_registration_contract.py`
- `scripts/r09-registration-preflight.sh`
- `docs/registration/R09_VERIFICATION.md`
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`

کد محصول ثبت‌نام در R09 تغییر نکرد.
