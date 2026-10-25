# R03 — سازگاری قواعد Keycloak و هویت Core

تاریخ: 2026-10-21

## تصمیم محصول

کاربر صریحاً تأیید کرد که حداقل طول رمز عبور ثبت‌نام عمومی باید **۸ کاراکتر** باشد. این تصمیم در R03 به سیاست رسمی Keycloak تبدیل شد؛ قانون پیچیده‌تری برای حروف بزرگ/عدد/نماد اختراع نشد.

## تغییرات انجام‌شده

### 1. سیاست رمز واقعی Keycloak

در `backend/keycloak/realm-template.json` مقدار زیر اضافه شد:

```json
"passwordPolicy": "length(8)"
```

در نتیجه realm تازه‌ای که از template وارد شود، رمز کوتاه‌تر از ۸ کاراکتر را در سطح Identity Provider رد می‌کند. این قاعده فقط HTML نیست و مالک آن Keycloak است.

### 2. هم‌ترازی قواعد نام با Core

الگوی `firstName` و `lastName` در `backend/keycloak/user-profile.json` از حالتی که مقدار فقط فاصله/نیم‌فاصله را می‌پذیرفت به الگویی تغییر کرد که:

- حداقل یک Unicode letter/mark می‌خواهد؛
- حروف، combining mark، فاصله و ZWNJ را مجاز می‌گذارد؛
- طول همچنان ۱ تا ۱۰۰ است؛
- نام فارسی و نیم‌فاصله معتبر باقی می‌مانند.

الگوی اجرایی:

```text
^(?=.*[\p{L}\p{M}])[\p{L}\p{M}\u200c ]+$
```

برای دفاع عمقی، `gradian_auth.claims.is_valid_name()` نیز اکنون وجود حداقل یک Unicode letter/mark را الزام می‌کند. بنابراین مقدار فقط فاصله یا فقط ZWNJ در Keycloak و Core هر دو نامعتبر است.

### 3. قواعد هویت موجود حفظ شدند

- username عمومی همچنان دقیقاً `^09\d{9}$` است؛ normalization شکل‌های `+98`/`0098`/ارقام فارسی در Core به معنی پذیرش آن‌ها در فرم ثبت‌نام نیست.
- `duplicateEmailsAllowed=false` حفظ شد؛ ایمیل الزامی و با email validator است.
- `mobile` attribute و `consultant_type` برای user قابل edit نیستند؛ ثبت‌نام عمومی نمی‌تواند role/subtype مدیریتی بسازد.
- mapping نقش‌ها، principal builder، endpointها، PKCE و session تغییر نکردند.

## فایل‌های محصول تغییرکرده

- `backend/keycloak/realm-template.json`
- `backend/keycloak/user-profile.json`
- `backend/packages/gradian-auth/src/gradian_auth/claims.py`

## تست‌ها

تست‌های زیر افزوده/تکمیل شدند:

- `backend/scripts/tests/test_registration_identity_rules.py`
  - policy رمز دقیقاً `length(8)`؛
  - username canonical؛
  - ایمیل required و duplicate غیرفعال؛
  - name pattern جدید؛
  - عدم قابلیت ویرایش عمومی `mobile` و `consultant_type`.
- `backend/packages/gradian-auth/src/gradian_auth/tests/test_claims.py`
  - ورودی فقط فاصله و فقط ZWNJ به موارد نامعتبر اضافه شد.
- `backend/scripts/tests/test_scripts_production_guard.py`
  - قرارداد R03 روی template/profile در مجموعه تست renderer تثبیت شد.

در این محیط واقعاً اجرا شد:

```text
python3 -m unittest scripts.tests.test_registration_identity_rules -v
4 tests ... OK
```

همچنین JSON هر دو فایل Keycloak parse شد، فایل‌های Python تغییرکرده compile شدند و sanity check مستقیم `is_valid_name()` برای نام فارسی/نیم‌فاصله و ورودی‌های نامعتبر موفق بود.

مجموعه کامل تست پروژه در این محیط اجرا نشد، چون dependencyهای توسعه مانند Django نصب نبودند. این محدودیت به معنی موفق اعلام‌کردن تست‌های اجرا نشده نیست.

## template در برابر realm زنده

این تغییرات مستقیماً **template** را اصلاح می‌کنند. Keycloak هنگام `--import-realm` realm موجود را به‌طور امن overwrite نمی‌کند؛ بنابراین ویرایش template به‌تنهایی تضمین نمی‌کند realm دارای volume فعلی تغییر کرده باشد.

`make reset` برای اعمال R03 پیشنهاد نمی‌شود، چون volume و داده کاربر را پاک می‌کند.

### اعمال غیرمخرب روی realm موجود

از `backend/`، با Keycloak در حال اجرا و یک admin معتبر:

1. ابتدا backup بگیر:

```bash
docker compose exec keycloak sh -lc '\
  /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD"'

docker compose exec -T keycloak \
  /opt/keycloak/bin/kcadm.sh get realms/gradian \
  > build/r03-realm-before.json

docker compose exec -T keycloak \
  /opt/keycloak/bin/kcadm.sh get users/profile -r gradian \
  > build/r03-user-profile-before.json
```

2. policy رمز را اعمال کن:

```bash
docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh update realms/gradian \
  -s 'passwordPolicy=length(8)'
```

3. user profile جدید را بدون حذف کاربرها اعمال کن:

```bash
docker cp keycloak/user-profile.json \
  "$(docker compose ps -q keycloak)":/tmp/gradian-user-profile.json

docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh update users/profile -r gradian \
  -f /tmp/gradian-user-profile.json
```

این روش volume، realm، کاربران و PostgreSQL را حذف نمی‌کند.

اگر bootstrap admin در محیط جاری معتبر نیست، همین تغییرات باید با یک حساب admin واقعی از Admin REST/Admin Console انجام شود؛ credential تازه یا reset داده برای دور زدن این موضوع ساخته نشود.

### بازگشت غیرمخرب

فایل‌های backup بالا را نگه دار. برای user profile:

```bash
docker cp build/r03-user-profile-before.json \
  "$(docker compose ps -q keycloak)":/tmp/r03-user-profile-before.json

docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh update users/profile -r gradian \
  -f /tmp/r03-user-profile-before.json
```

برای password policy، مقدار `passwordPolicy` موجود در `build/r03-realm-before.json` را دوباره روی realm اعمال کن. اگر قبل از R03 policy خالی بوده است:

```bash
docker compose exec keycloak \
  /opt/keycloak/bin/kcadm.sh update realms/gradian \
  -s 'passwordPolicy='
```

هیچ rollbackای نباید با `docker compose down -v` یا `make reset` انجام شود.

## پذیرش زنده باقی‌مانده

در این سشن Keycloak واقعی اجرا نشد؛ بنابراین موارد زیر **زنده تأیید نشده‌اند**:

- ثبت‌نام با رمز ۷ کاراکتری واقعاً با پیام Keycloak رد شود؛
- نام فقط فاصله واقعاً روی فرم Keycloak رد شود؛
- موبایل یا ایمیل تکراری روی فرم واقعی پیام conflict بدهد؛
- claims حساب تازه شامل `given_name`، `family_name`، `email` و username معتبر باشند.

پس وضعیت R03 از نظر کد/config و تست استاتیک **IMPLEMENTED** است، ولی پذیرش runtime آن **PENDING_LIVE** می‌ماند تا روی realm موجود با backup و بدون حذف داده اجرا شود.

## قدم بعد

R04 از نظر وابستگی قابل شروع است و مانع طراحی R02 جلوی آن را نمی‌گیرد. R05 همچنان به R02 و تکمیل پذیرش R03 وابسته است.
