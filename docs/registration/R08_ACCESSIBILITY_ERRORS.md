# R08 — خطاها، دسترس‌پذیری و حالت‌های نمایش

تاریخ: 2026-10-21  
ورودی: `Gradian-R06.zip`  
وضعیت: **IN_PROGRESS — FUNCTIONAL HARDENED / BLOCKED_DESIGN / PENDING_BROWSER_LIVE**

## محدوده اجراشده

این مرحله فقط خطاها، semantics دسترس‌پذیری، focus، متن‌های وضعیت و ایمنی نمایش در مسیر احراز هویت/ثبت‌نام را سخت‌گیری کرد. معماری PKCE، endpointها، نقش‌ها، داشبوردها و CTA لندینگ بازطراحی نشدند. R02 هنوز مرجع بصری ثبت‌نام/CTA ندارد؛ بنابراین تطابق تصویری نهایی یا ادعای pixel-match انجام نشده است.

## تغییرهای React

- `LoginPage` دیگر پیام‌های فارسی را hard-code نمی‌کند و وضعیت انتقال، خطای اتصال و retry از namespace واقعی `auth` در هر دو locale `fa/en` خوانده می‌شوند.
- `LoginPage`، `RegisterPage` و `AuthCallbackPage` برای حالت انتظار `role=status` + `aria-live=polite` + `aria-atomic=true` دارند.
- خطاها `role=alert` دارند و پس از وقوع با یک target برنامه‌ای `tabIndex=-1` focus می‌گیرند تا کاربر keyboard/screen-reader بدون جست‌وجو به علت شکست برسد.
- دکمه‌های retry در حالت اقدام `disabled` و `aria-disabled` دارند؛ promise rejection همچنان handle می‌شود و موفقیت جعلی نمایش داده نمی‌شود.
- `RegisterPage` پیام «برگشت از تلاش ناتمام» را success معرفی نمی‌کند؛ فقط امکان شروع PKCE تازه می‌دهد.
- `AuthCallbackPage` تا وقتی token exchange + `/me` + session validation واقعی موفق نشده‌اند هیچ پیام موفقیت ثبت‌نام نشان نمی‌دهد و مستقیماً session معتبر را به panel می‌برد.
- auth cardها از `text-align:start` و variableهای theme استفاده می‌کنند تا RTL فارسی و LTR انگلیسی خراب نشوند. dark theme موجود React برای auth card/error نیز پوشش گرفته است.
- narrow guard برای 360px، `overflow-wrap:anywhere` و جلوگیری از horizontal overflow به auth UI افزوده شد.

## تغییرهای Keycloak theme

- خطای هر فیلد با `aria-invalid`، `aria-describedby` و `aria-errormessage` به input متصل است و `role=alert`/`aria-live=assertive` دارد.
- بعد از submit نامعتبر، اولین فیلد واقعاً نامعتبر focus می‌گیرد؛ focus keyboard موجود برای input/button/link حفظ شده است.
- mobile و email در صفحه فارسی `dir=ltr` هستند و CSS با `unicode-bidi: plaintext` از خوانایی داده دوجهته محافظت می‌کند.
- password و password-confirm همچنان هیچ `value` بازتابی ندارند؛ داده حساس پس از خطا repopulate نمی‌شود.
- پیام عمومی error با `role=alert`/assertive و پیام non-error با `role=status`/polite نمایش داده می‌شود؛ محتوا همچنان با `kcSanitize` عبور می‌کند.
- پیام فارسی قابل‌فهم برای duplicate mobile/username، duplicate email، email نامعتبر، فیلد الزامی، mismatch password و حداقل طول رمز اضافه شد. این‌ها جای policy واقعی Keycloak را نمی‌گیرند؛ فقط presentation پیام‌های شناخته‌شده را بهبود می‌دهند.
- theme صریحاً `locales=fa` دارد. پشتیبانی Keycloak انگلیسی/dark در این مرحله ادعا نمی‌شود؛ R02 هنوز چنین مرجعی را تأیید نکرده است.
- CSS در 620px و 360px padding/width امن، wrap متن بلند و جلوگیری از horizontal overflow دارد.

## جدول سناریوهای R08

| سناریو | رفتار کد فعلی | شواهد این مرحله | وضعیت پذیرش |
| --- | --- | --- | --- |
| موبایل تکراری | Keycloak خطای username duplicate را روی فرم نگه می‌دارد؛ متن فارسی actionable تعریف شده | contract theme | نیازمند submit زنده |
| ایمیل تکراری | Keycloak خطای email duplicate؛ متن فارسی actionable | contract theme | نیازمند submit زنده |
| mismatch رمز | خطای provider به password-confirm متصل می‌شود؛ passwordها repopulate نمی‌شوند | R05 + R08 contract | نیازمند submit زنده |
| رمز کمتر از ۸ | policy `length(8)` از R03؛ متن presentation فارسی اضافه شد | R03 static + R08 theme | نیازمند realm زنده |
| فیلد خالی/نامعتبر | server-side field error + focus اولین invalid + aria | R08 theme test | نیازمند FreeMarker زنده |
| config/Core در دسترس نیست | `/login` و `/register` خطای قابل‌فهم + retry دارند | R08 React contract | نیازمند browser smoke |
| callback/provider outage | state provider/failed با retry تازه و focus خطا | R07 + R08 contract | نیازمند browser/live |
| Keycloak پس از redirect خاموش شود | خود مرورگر ممکن است صفحه network error نشان دهد؛ با Back، `/register` تلاش ناتمام را success نمی‌نامد و continuation تازه می‌دهد | R06/R08 source | network-browser smoke لازم |
| viewport کوچک | card max-width، wrap، media 620/360 و no horizontal overflow guard | R08 CSS contract | screenshot/browser لازم |
| فارسی RTL / موبایل و ایمیل LTR | document/theme RTL؛ fields حساس به جهت LTR + plaintext | R08 theme contract | browser لازم |
| React fa/en + light/dark | copy login/registration/callback در هر دو locale؛ auth card variable-based | R08 React contract | browser matrix لازم |
| Keycloak locale/theme | فقط fa در scope تأییدشده theme | `theme.properties` | طراحی R02 برای ادعای بیشتر لازم |

## تست‌های اجراشده

از ریشه پروژه:

```text
node frontend/tests/r08-auth-accessibility.cjs
=> R08 React accessibility/display contract: 28 checks passed.

python3 backend/scripts/tests/test_r08_theme_accessibility.py
=> Ran 7 tests ... OK

node frontend/tests/r04-auth-flow.cjs
=> 7 scenario groups passed.

node frontend/tests/r06-public-registration.cjs
=> 17 checks passed.

node frontend/tests/r07-callback.cjs
=> 6 scenario groups passed.

python3 backend/scripts/tests/test_r07_identity_contract.py
=> 5 tests ... OK

python3 backend/scripts/tests/test_r05_theme_contract.py
=> 6 tests ... OK

python3 backend/scripts/tests/test_registration_identity_rules.py
=> 4 tests ... OK
```

`frontend/node_modules` در archive حاضر نبود، بنابراین `npm run build`/`npm run lint` در این محیط اجرا و موفق اعلام نشده‌اند. تست‌های بالا source/contract هستند و جای browser/Keycloak زنده را نمی‌گیرند.

## مواردی که عمداً DONE اعلام نشدند

- R02 هنوز `BLOCKED_DESIGN` است؛ بنابراین شواهد تصویری «مطابق مرجع ثبت‌نام» وجود ندارد.
- FreeMarker روی Keycloak واقعی render/submit نشده است.
- duplicate mobile/email، mismatch و password policy در realm زنده مشاهده نشده‌اند.
- ماتریس browser برای 320/390/desktop، keyboard-only، fa/en و light/dark React اجرا نشده است.
- خاموش‌کردن واقعی Core/Keycloak و مشاهده مسیر recovery در مرورگر اجرا نشده است.

به همین علت R08 **DONE نیست**. بخش قابل‌پیاده‌سازی و contract hardening انجام شده؛ بستن R08 نیازمند R02 + browser/live evidence است.

## فایل‌های محصول تغییرکرده در R08

- `frontend/src/features/auth/pages/LoginPage.tsx`
- `frontend/src/features/auth/pages/RegisterPage.tsx`
- `frontend/src/features/auth/pages/AuthCallbackPage.tsx`
- `frontend/src/locales/fa/auth.json`
- `frontend/src/locales/en/auth.json`
- `frontend/src/shared/styles/globals.css`
- `backend/keycloak/themes/gradian/login/register.ftl`
- `backend/keycloak/themes/gradian/login/template.ftl`
- `backend/keycloak/themes/gradian/login/theme.properties`
- `backend/keycloak/themes/gradian/login/resources/css/gradian.css`
- `backend/keycloak/themes/gradian/login/messages/messages_fa.properties`

## فایل‌های تست/سند افزوده یا به‌روزشده

- `frontend/tests/r08-auth-accessibility.cjs`
- `backend/scripts/tests/test_r08_theme_accessibility.py`
- `docs/registration/R08_ACCESSIBILITY_ERRORS.md`
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`
