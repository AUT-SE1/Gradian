# R10 — پذیرش نهایی و تحویل مرحله ثبت‌نام

تاریخ: 2026-10-21

## حکم پذیرش

**IN_PROGRESS — RELEASE-CANDIDATE REVIEW COMPLETE / FINAL ACCEPTANCE BLOCKED**

R10 به‌عنوان مرور نهایی و بسته‌بندی release candidate انجام شد، اما طبق قرارداد پروژه **DONE نیست**. دلیل، نقص کد جدید R10 نیست؛ پیش‌نیازهای رسمی هنوز بسته نشده‌اند: R02 مرجع بصری ثبت‌نام/CTA ندارد، R08 و R09 به همین وابستگی و شواهد browser/live باز هستند، build/lint/typecheck در محیط این سشن به‌علت دسترسی نداشتن به npm registry قابل اجرا نبودند و Docker/Keycloak زنده نیز در این محیط وجود نداشت.

در این مرحله هیچ کد محصول، endpoint، dependency، realm data یا داده کاربر تغییر نکرد. R10 فقط شواهد R01 تا R09 را مرور کرد، preflight قابل‌اجرا را دوباره اجرا کرد، موانع را ثبت کرد، روش انتشار/بازگشت غیرمخرب را یک‌جا جمع کرد و manifest تغییرات را تولید کرد.

## شواهدی که در R10 واقعاً اجرا شدند

از ریشه پروژه:

```bash
./scripts/r09-registration-preflight.sh
```

نتیجه واقعی:

- R04 auth-flow: 7 گروه سناریو موفق.
- R06 public registration: 17 check موفق.
- R07 callback: 6 گروه سناریو موفق.
- R08 React accessibility/display: 28 check موفق.
- R09 frontend registration contract: 22 check موفق.
- R03 backend identity rules: 4 تست موفق.
- R05 Keycloak theme contract: 6 تست موفق.
- R07 backend identity contract: 5 تست موفق.
- R08 Keycloak accessibility contract: 7 تست موفق.
- R09 backend registration contract: 5 تست موفق.
- کل `backend/scripts/tests`: 125 تست موفق.
- parse فایل‌های JSON اصلی Keycloak، `py_compile` و `node --check`: موفق.

این runner عمداً build، Playwright، Docker یا self-registration زنده را موفق اعلام نمی‌کند.

## build / lint / typecheck

در R10 دوباره تلاش شد dependencyهای frontend نصب شوند. `npm ping` به `https://registry.npmjs.org/` بعد از ۲۰ ثانیه timeout شد. `npm ci` نیز کامل نشد و برای جلوگیری از باقی‌ماندن process معلق متوقف شد. `node_modules` ناقص از artifact نهایی حذف می‌شود.

بنابراین این سه فرمان در این محیط **موفق اجرا نشده‌اند**:

```bash
cd frontend
npm ci
npm run build
npm run lint
npm run typecheck
```

این مورد acceptance blocker است و نباید با preflight source-level جایگزین تلقی شود.

## Browser و طراحی

- Chromium در محیط R10 موجود بود، اما Playwright نصب نبود و frontend dependencyها نیز کامل نصب نشدند؛ بنابراین browser matrix معتبر اجرا نشد.
- R02 همچنان `BLOCKED_DESIGN` است. مرجع مستقل و تأییدشده برای فرم Registration و محل/متن CTA لندینگ موجود نیست.
- به همین دلیل CTA لندینگ عمداً حدس زده نشده و تطابق تصویری registration موفق اعلام نمی‌شود.
- مسیر مستقیم `/register` و لینک provider-owned در `login.ftl` از مراحل قبلی وجود دارند، ولی پذیرش مرورگری و تصویری نهایی باقی است.

## Live Keycloak/Core

در محیط R10 executable Docker موجود نبود؛ بنابراین Keycloak/Core/PostgreSQL زنده بالا نیامدند و هیچ حساب تستی ساخته یا حذف نشد. موارد زیر همچنان باید روی stack واقعی اجرا شوند:

1. ثبت‌نام موفق با نام، نام خانوادگی، موبایل canonical، ایمیل یکتا و رمز حداقل ۸ کاراکتر.
2. رد رمز ۷ کاراکتری، نام فقط فاصله/ZWNJ، موبایل تکراری، ایمیل تکراری و password mismatch.
3. callback معتبر و ایجاد session فقط پس از `/me` معتبر.
4. ثبت durable نقش `student` در Keycloak برای حساب تازه.
5. logout و login مجدد همان حساب و مشاهده `student` در token تازه.
6. قطع موقت provider/Admin API و recovery واقعی بدون ساخت session موفق کاذب.
7. invalid/consumed code، state اشتباه و retry با PKCE تازه.
8. regression ورود/خروج چهار نقش و guardهای فعلی روی stack واقعی.

## ماتریس نهایی پذیرش

| معیار | وضعیت R10 | شاهد |
| --- | --- | --- |
| قرارداد PKCE و registration endpoint | PASS در source/contract | R04 + preflight |
| route `/register` و session handling | PASS در source/contract | R06 + preflight |
| callback یک‌بارمصرف و session ordering | PASS در source/contract | R07 + preflight |
| policy رمز ۸ و قواعد نام در config/code | PASS در source/contract | R03 + preflight |
| theme و password non-repopulation | PASS در source/contract | R05/R08 + preflight |
| accessibility/error semantics | PASS در source/contract | R08 + preflight |
| backend script regression | PASS | 125 تست |
| `npm ci` + build | **BLOCKED_ENV** | npm registry timeout |
| lint / typecheck | **BLOCKED_ENV** | dependency نصب نشده |
| browser matrix | **BLOCKED_ENV** | Playwright موجود نیست |
| visual acceptance registration/CTA | **BLOCKED_DESIGN** | R02 باز است |
| live self-registration | **PENDING_LIVE** | Docker/Keycloak اجرا نشده |
| durable student role/token fresh | **PENDING_LIVE** | R07 live باز است |
| R08 DONE | **NO** | design/browser/live باز است |
| R09 DONE | **NO** | وابسته به R08 + build/browser/live |
| R10 DONE | **NO** | معیارهای بالا کامل نشده‌اند |

## روش انتشار غیرمخرب روی محیط موجود

این release candidate نباید با `make reset` یا حذف volume اعمال شود.

1. آخرین backup کد و realm را نگه دار و قبل از تغییر runtime از realm و user profile backup بگیر:

```bash
cd backend

docker compose exec keycloak sh -lc '\
  /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD"'

docker compose exec -T keycloak \
  /opt/keycloak/bin/kcadm.sh get realms/gradian \
  > build/r10-realm-before.json

docker compose exec -T keycloak \
  /opt/keycloak/bin/kcadm.sh get users/profile -r gradian \
  > build/r10-user-profile-before.json
```

2. ابتدا frontend را در همان محیطی که npm registry قابل دسترسی است build/lint/typecheck کن. اگر هرکدام fail شد، انتشار متوقف شود.
3. policy رمز realm موجود را بدون reset اعمال کن:

```bash
docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh update realms/gradian \
  -s 'passwordPolicy=length(8)'
```

4. user profile را بدون حذف کاربرها اعمال کن:

```bash
docker cp keycloak/user-profile.json \
  "$(docker compose ps -q keycloak)":/tmp/gradian-user-profile.json

docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh update users/profile -r gradian \
  -f /tmp/gradian-user-profile.json
```

5. سرویس‌ها را با روش معمول همان محیط rebuild/restart کن، بدون `down -v` و بدون حذف DB/realm.
6. یک حساب تست کاملاً ساختگی و قابل شناسایی بساز و matrix live بالا را اجرا کن. credential حساب تست داخل report یا git commit نشود.
7. بعد از smoke، فقط همان حساب‌های تست مشخص حذف شوند؛ داده عمومی یا volume پاک نشود.

اگر bootstrap admin جاری معتبر نیست، از Admin REST/Admin Console با حساب admin واقعی استفاده شود؛ برای دور زدن این مسئله credential جدید یا reset داده ساخته نشود.

## rollback غیرمخرب

- کد را به artifact/commit قبل از registration release برگردان و همان build قبلی را deploy کن.
- `build/r10-user-profile-before.json` را با `kcadm update users/profile` بازگردان.
- مقدار `passwordPolicy` قبلی را از `build/r10-realm-before.json` استخراج و دوباره اعمال کن؛ اگر مقدار قبلی خالی بوده، `passwordPolicy=` اعمال شود.
- هیچ rollbackای با `docker compose down -v`، حذف volume، حذف PostgreSQL یا `make reset` انجام نشود.
- rollback کد به‌تنهایی نباید به حذف حساب‌های واقعی ایجادشده پس از انتشار منجر شود.

## فایل‌های تغییرکرده

فهرست تجمعی دقیق تغییرات نسبت به ورودی baseline `Gradian-main (2).zip` در این فایل ثبت شده است:

```text
docs/registration/R10_CHANGED_FILES.txt
```

تغییرات مخصوص خود R10 فقط این‌ها هستند:

- `docs/registration/R10_FINAL_ACCEPTANCE.md`
- `docs/registration/R10_CHANGED_FILES.txt`
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`

هیچ فایل product code در R10 تغییر نکرد.

## قدم بعد

برای این برنامه R11 تعریف نشده است. قدم بعد، اجرای تسک تازه نیست؛ باید blockerهای موجود بسته شوند:

1. مرجع R02 برای Registration و CTA تأیید شود؛
2. روی محیطی با npm سالم، `npm ci`، build، lint و typecheck اجرا شوند؛
3. browser matrix اجرا شود؛
4. پذیرش live R03/R05/R06/R07/R08 تکمیل شود؛
5. R09 دوباره اجرا و DONE شود؛
6. سپس همین R10 دوباره اجرا شود و فقط اگر همه معیارهای مستقل PASS بودند به `DONE` تغییر کند.
