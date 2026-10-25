# R01 — ممیزی و تثبیت قرارداد ثبت‌نام گرادیان

تاریخ بررسی: 2026-10-21  
ورودی: `Gradian-main (2).zip`  
وضعیت: **DONE برای ممیزی/خط مبنا**؛ هیچ کد محصول، realm یا داده زنده تغییر نکرد.

## 1. دامنه این سشن

فقط R01 انجام شد. فایل‌های auth فرانت، router و Landing، قالب‌های Keycloak، realm/user-profile، اسکریپت render realm، مدل/serializerهای هویت، claims، نقش‌ها و sync profile خوانده شدند. هیچ R02 تا R10 اجرا نشد و هیچ endpoint یا رفتار تازه‌ای ساخته نشد.

این گزارش بین سه چیز فرق می‌گذارد:

1. **قرارداد موجود در کد/فایل**: چیزی که در checkout حاضر است.
2. **وضعیت realm اجراشده**: در این سشن مشاهده نشده و نباید از template استنتاج شود.
3. **تصمیم محصول**: چیزی که برای ادامه باید صریح تثبیت شود و از روی README یا حدس به‌عنوان رفتار زنده اعلام نمی‌شود.

## 2. منابع بررسی‌شده

### فرانت‌اند

- `frontend/src/features/auth/api/authApi.ts`
- `frontend/src/features/auth/pages/LoginPage.tsx`
- `frontend/src/features/auth/pages/AuthCallbackPage.tsx`
- `frontend/src/app/router/AppRouter.tsx`
- `frontend/src/features/landing/pages/LandingPage.tsx`
- `frontend/src/app/providers/AuthProvider.tsx`
- `frontend/src/shared/auth/session.ts`
- `frontend/src/shared/types/auth.ts`
- `frontend/src/locales/fa/auth.json`
- `frontend/src/locales/en/auth.json`
- `frontend/package.json`

### Core / shared auth

- `backend/core/accounts/views.py`
- `backend/core/accounts/urls.py`
- `backend/core/accounts/authentication.py`
- `backend/core/accounts/profiles.py`
- `backend/core/accounts/models.py`
- `backend/core/accounts/serializers.py`
- `backend/core/accounts/user_views.py`
- `backend/packages/gradian-auth/src/gradian_auth/claims.py`
- `backend/packages/gradian-auth/src/gradian_auth/mobile.py`
- `backend/packages/gradian-auth/src/gradian_auth/roles.py`
- `backend/packages/gradian-auth/src/gradian_auth/principals.py`
- `backend/packages/gradian-keycloak/src/gradian_keycloak/roles.py`

### Keycloak / اجرا

- `backend/keycloak/realm-template.json`
- `backend/keycloak/user-profile.json`
- `backend/keycloak/themes/gradian/login/login.ftl`
- `backend/keycloak/themes/gradian/login/register.ftl`
- `backend/keycloak/themes/gradian/login/template.ftl`
- `backend/keycloak/themes/gradian/login/theme.properties`
- `backend/keycloak/themes/gradian/README.md`
- `backend/scripts/render_realm.py`
- `backend/docker-compose.yml`
- `backend/Makefile`
- `backend/README.md`

## 3. قرارداد واقعی جریان احراز هویت موجود

### 3.1 تنظیمات عمومی

Core فقط یک endpoint عمومی برای شروع auth دارد:

- `GET /api/v1/auth/config`

پاسخ آن شامل این فیلدهاست:

- `issuer`
- `registration_endpoint`
- `realm`
- `client_id`
- `end_session_url`
- `landing_url`

`registration_endpoint` در Core از issuer ساخته می‌شود:

`{issuer}/protocol/openid-connect/registrations`

در `accounts/urls.py` endpoint عمومی برای ساخت مستقیم کاربر وجود ندارد. ساخت کاربر از API Core فقط در مسیر مدیریتی `POST /api/v1/admin/users` و با مجوز ادمین وجود دارد؛ این endpoint قرارداد self-registration نیست.

### 3.2 ورود فعلی فرانت

`authApi.ts` ورود را مستقیم و بدون کتابخانه OIDC خارجی پیاده می‌کند:

1. دریافت `/auth/config`.
2. ساخت `code_verifier` تصادفی و `state` تصادفی.
3. ساخت `code_challenge` با SHA-256 و Base64URL.
4. ذخیره verifier/state در `sessionStorage`.
5. انتقال به authorization endpoint معمول Keycloak با `response_type=code`، `scope=openid`، callback جاری و `code_challenge_method=S256`.
6. callback با تطبیق state و verifier، exchange کد در token endpoint.
7. `GET /api/v1/me` با Bearer token.
8. ساخت نشست فرانت فقط بعد از پاسخ معتبر `/me`.

`registration_endpoint` همین حالا در type پیکربندی فرانت وجود دارد، ولی `authApi.ts` هیچ تابع شروع ثبت‌نام ندارد و از آن استفاده نمی‌کند.

`oidc-client-ts` در `frontend/package.json` وجود ندارد؛ معماری فعال auth همین پیاده‌سازی مستقیم PKCE است.

### 3.3 مسیرها و ورودی عمومی

- `/login` وجود دارد و `LoginPage` بلافاصله `beginLogin()` را شروع می‌کند.
- `/auth/callback` وجود دارد.
- `/register` وجود ندارد.
- دو CTA فعال Landing فعلی هر دو به `/login` می‌روند.
- بنابراین از React فعلی ورودی مستقلی برای self-registration وجود ندارد.

### 3.4 نشست فرانت

- کل نشست با کلید `gradian.auth.session` در `localStorage` نگه‌داری می‌شود.
- `code_verifier` و `state` فقط در `sessionStorage` نگه‌داری می‌شوند.
- `expiresAt` اجباری است و نشست منقضی با validator رد می‌شود.
- `AuthProvider` روی logout/تغییر هویت query cache را cancel و clear می‌کند.
- انقضا با timer/focus/visibility کنترل می‌شود و storage event برای همگام‌سازی تب‌ها وجود دارد.
- `refresh_token` ممکن است در نشست ذخیره شود، ولی در جریان فعلی refresh-token flow استفاده نمی‌شود.

این رفتارها بخشی از baseline هستند و ثبت‌نام نباید آن‌ها را با معماری موازی جایگزین کند.

## 4. قرارداد فایل‌های Keycloak

### 4.1 realm template

`realm-template.json` در checkout این وضعیت را تعریف می‌کند:

| تنظیم | مقدار فایل |
| --- | --- |
| `registrationAllowed` | `true` |
| `registrationEmailAsUsername` | `false` |
| `loginWithEmailAllowed` | `false` |
| `duplicateEmailsAllowed` | `false` |
| `editUsernameAllowed` | `false` |
| `verifyEmail` | `false` |
| `resetPasswordAllowed` | `false` |
| `rememberMe` | `true` |
| locale پشتیبانی‌شده | فقط `fa` |
| access token lifespan | 600 ثانیه |
| PKCE client | `gradian-web`, public client, S256 |
| redirect URI | `${FRONTEND_URL}/auth/callback` |

نقش‌های realm: `student`، `consultant`، `professor`، `admin` و `service`.

**مهم:** در `realm-template.json` هیچ `passwordPolicy` وجود ندارد. بنابراین ادعای «حداقل ۸ کاراکتر» از این فایل قابل اثبات نیست.

### 4.2 user profile

قرارداد فایل `user-profile.json`:

| فیلد | وضعیت فایل |
| --- | --- |
| `username` | pattern برابر `^09\\d{9}$`؛ self-edit مجاز |
| `email` | الزامی برای user/admin، email validator، حداکثر 254 |
| `firstName` | الزامی، 1..100، حروف/mark/space/ZWNJ |
| `lastName` | الزامی، 1..100، حروف/mark/space/ZWNJ |
| `mobile` | برای admin الزامی؛ user فقط view و حق edit ندارد |
| `consultant_type` | فقط admin حق edit؛ گزینه‌های consultant/top_ranker |

در self-registration شماره ورود همان `username` است، نه attribute جداگانه `mobile`. Core هم `preferred_username` توکن را به mobile تبدیل می‌کند.

### 4.3 قالب‌ها

`register.ftl` شش فیلد پایه را دارد:

- firstName
- lastName
- username با عنوان شماره موبایل
- email
- password
- password-confirm

فرم به `url.registrationAction` ارسال می‌شود و لینک برگشت به `url.loginUrl` دارد.

`login.ftl` فرم موبایل/رمز/remember-me را دارد، اما در نسخه فعلی **لینک ثبت‌نام ندارد** و layout با `displayInfo=false` فراخوانی شده است. این با توضیح README قالب که می‌گوید صفحه ورود به ثبت‌نام لینک دارد، هم‌خوان نیست.

## 5. قواعد هویت Core و سازگاری با فرم

### 5.1 موبایل

Core در `normalize_mobile()` این ورودی‌ها را به فرم canonical `09XXXXXXXXX` تبدیل می‌کند:

- ارقام فارسی و عربی → انگلیسی
- `+98...` → `0...`
- `0098...` → `0...`

اما user-profile Keycloak برای `username` فقط pattern فایل `^09\\d{9}$` را دارد و خود قالب هیچ normalization جاوااسکریپتی انجام نمی‌دهد. بنابراین تحمل Core برای شکل‌های دیگر به معنی پشتیبانی self-registration از آن شکل‌ها نیست.

برای R01، قرارداد موجود self-registration را **شماره canonical با شروع 09** در نظر می‌گیریم؛ پشتیبانی +98/0098 یا ارقام غیرانگلیسی قابلیت انجام‌شده اعلام نمی‌شود. README قالب نیز صریحاً ورودی انگلیسی را ذکر می‌کند.

### 5.2 نام‌ها

Core قبل از اعتبارسنجی claim متن را `strip()` می‌کند و نام باید بعد از trim حداقل یک کاراکتر معتبر داشته باشد.

در `user-profile.json` pattern فعلی space را مجاز می‌داند و length حداقل 1 است. در نتیجه یک مقدار فقط شامل فاصله می‌تواند از قواعد فایل Keycloak عبور کند، ولی در Core پس از strip خالی شود و `/me` را با `incomplete_identity` نامعتبر کند.

این یک ناسازگاری واقعی بین فایل Keycloak و قرارداد Core است و باید در R03 حل شود؛ در R01 فقط ثبت می‌شود.

### 5.3 ایمیل

- user-profile: email الزامی، email validator، max 254.
- realm template: `duplicateEmailsAllowed=false`.
- Core claim: ایمیل را lowercase می‌کند و وجود `@` را برای هویت توکن بررسی می‌کند.
- `Profile.email` در DB نیز unique است.

ثبت‌نام تکراری/تعارض باید از ارائه‌دهنده یا Core به‌صورت خطای واقعی دیده شود؛ R01 آن را موفق فرض نمی‌کند.

### 5.4 رمز

سه منبع با هم یک قرارداد اجرایی قطعی نمی‌سازند:

- `backend/README.md` و README قالب می‌گویند حداقل ۸ کاراکتر.
- `UserCreateSerializer` ادمین `min_length=8` دارد، اما آن مسیر self-registration نیست.
- `realm-template.json` هیچ `passwordPolicy` ندارد.
- `register.ftl` هم `minlength` تعیین نکرده است.

پس در baseline فعلی **سیاست حداقل ۸ برای self-registration از کد Keycloak قابل اثبات نیست** و نباید DONE اعلام شود.

### 5.5 بازتاب رمز در فرم

macro فعلی `register.ftl` برای همه inputها از جمله password و password-confirm مقدار زیر را تولید می‌کند:

`value="${(register.formData[name]!'')}"`

در نتیجه ساختار فعلی امکان بازپرکردن رمز در HTML پس از خطا را ایجاد می‌کند. این برخلاف قرارداد امنیتی خود برنامه ثبت‌نام است و برای R05 ثبت می‌شود؛ در R01 کد قالب تغییر نکرد.

## 6. نقش و profile پس از ثبت‌نام

`resolve_panel()` چنین رفتار می‌کند:

- بدون هیچ panel role → `student`
- دقیقاً یک panel role → همان نقش
- بیش از یک panel role → `AmbiguousRoleError`

در Core:

1. principal از token ساخته می‌شود؛ کاربر تازه بدون نقش پنل از نگاه Core دانشجو است.
2. `sync_profile()` در اولین درخواست profile را می‌سازد.
3. اگر token هیچ panel role نداشته باشد و profile قبلاً وجود نداشته باشد، `grant_default_role()` تلاش می‌کند نقش `student` را از Admin API به Keycloak بدهد.
4. شکست grant فقط log می‌شود و درخواست Core fatal نمی‌شود.

### شکاف قابل پیگیری R07

اگر grant اولیه نقش student شکست بخورد، profile از قبل ساخته شده است. در درخواست بعدی با token بدون panel role، شرط `registered_just_now` دیگر برقرار نیست؛ بنابراین همین مسیر فعلی grant را retry نمی‌کند. Core همچنان کاربر را student resolve می‌کند، ولی role واقعی Keycloak ممکن است جا بماند و token/serviceهای دیگر آن را نبینند.

این مورد در R01 فقط ثبت شد و هیچ اصلاحی انجام نشد.

همچنین token اولیه‌ای که پیش از grant صادر شده، با grant نقش درجا تغییر نمی‌کند. بررسی نقش در token تازه/ورود مجدد جزو R07/R09 است.

## 7. رشته تحصیلی و نقش‌های عمومی

- `field_of_study` در `Profile` می‌تواند خالی باشد.
- `PATCH /api/v1/me` امکان تغییر آن را دارد.
- registration form فعلی فیلد رشته ندارد.
- role و `consultant_type` در self-registration عمومی وجود ندارند و نباید به فرم عمومی اضافه شوند.
- API ادمین می‌تواند حساب هر نقش را بسازد؛ این مسیر مدیریتی است و جایگزین self-registration نیست.

## 8. اختلاف مستندات با کد اجرایی

| موضوع | مستند | کد/فایل فعلی | نتیجه R01 |
| --- | --- | --- | --- |
| لینک ثبت‌نام در login | README قالب: وجود دارد | `login.ftl`: وجود ندارد | مستند عقب‌تر/ناسازگار؛ R05 |
| حداقل رمز 8 | READMEها: بله | realm: بدون `passwordPolicy` | هنوز قرارداد اجرایی تأییدشده نیست؛ R03 |
| route ثبت‌نام React | README جریان را توضیح می‌دهد | router: `/register` ندارد | هنوز پیاده‌سازی نشده؛ R06 |
| شروع registration PKCE | README نمونه می‌دهد | authApi فقط beginLogin | هنوز پیاده‌سازی نشده؛ R04 |
| موبایل +98/فارسی | Core normalize می‌کند | Keycloak username rule canonical | تحمل Core ≠ قرارداد فرم؛ canonical فعلی |
| نام فقط فاصله | Core بعد از trim رد می‌کند | user-profile می‌تواند آن را بپذیرد | ناسازگاری واقعی؛ R03 |
| رمز در rerender | قرارداد امنیتی می‌خواهد خالی باشد | macro value را برای password هم می‌گذارد | نقص قالب؛ R05 |

## 9. وضعیت template در برابر realm زنده

در archive فعلی:

- `backend/build/realm-gradian.json` وجود ندارد.
- `frontend/node_modules` وجود ندارد.
- Docker/Keycloak زنده در این سشن اجرا نشده‌اند.

`render_realm.py` از `realm-template.json` کپی می‌گیرد، user-profile را embed می‌کند، seed user/service clientها را می‌افزاید و در non-production client تست می‌سازد. خروجی پیش‌فرض `backend/build/realm-gradian.json` است.

Compose همان فایل renderشده را به import Keycloak mount می‌کند و theme را جداگانه mount می‌کند. `make reset` طبق Makefile volumeها و داده را پاک می‌کند؛ بنابراین **برای اعمال تغییرات R03 روی محیط کاربر نباید reset به‌عنوان روش پیش‌فرض پیشنهاد شود**. روش اعمال غیرمخرب باید در R03 مشخص شود.

هیچ نتیجه‌ای در این گزارش وضعیت realm موجود کاربر را تأیید نمی‌کند.

## 10. بررسی‌های انجام‌شده در این سشن

موارد زیر واقعاً اجرا شدند:

- خواندن منابع فهرست‌شده در بخش 2.
- parse شدن `backend/keycloak/realm-template.json` با `python3 -m json.tool`: موفق.
- parse شدن `backend/keycloak/user-profile.json` با `python3 -m json.tool`: موفق.
- بررسی وجود artifactها: `backend/build/realm-gradian.json` در zip حاضر نیست؛ `frontend/node_modules` نیز حاضر نیست.

موارد زیر اجرا نشدند و موفق اعلام نمی‌شوند:

- build/lint فرانت؛ dependency نصب‌شده در archive وجود ندارد.
- تست Docker/Keycloak/Core زنده.
- self-registration واقعی.
- بررسی realm موجود در محیط کاربر.
- آزمون سیاست واقعی password در Keycloak اجراشده.

R01 تسک ممیزی است و تغییر محصول ندارد؛ نبود تست زنده مانع ثبت baseline است، ولی هر ادعای runtime در R03/R07/R09 باید جدا تأیید شود.

## 11. تصمیم‌های باز و قدم بعد

### تصمیم لازم برای R03

تنها تصمیم محصولی که پیش از اعمال قواعد R03 باید صریح تثبیت شود:

**آیا «حداقل ۸ کاراکتر» باید سیاست رسمی و قابل‌اجرای self-registration در Keycloak باشد؟**

اسناد پروژه این را قصد کرده‌اند، اما realm template فعلی آن را enforce نمی‌کند. R01 این فاصله را ثبت کرده و خودش سیاست تازه اعمال نکرده است.

### مواردی که تصمیم تازه نمی‌خواهند

- self-registration عمومی فقط student است.
- شماره فرم فعلاً canonical `09XXXXXXXXX` است؛ normalization وسیع Core وعده UI نیست.
- role، consultant_type و field_of_study به فرم عمومی پایه اضافه نمی‌شوند.
- نام فقط فاصله باید با قرارداد Core ناسازگار نباشد؛ R03 باید validator ارائه‌دهنده را هماهنگ کند.
- رمز پس از خطای فرم نباید بازتاب داده شود؛ R05.

### تسک بعدی قابل اجرا

- `R02` همچنان **BLOCKED_DESIGN** تا مرجع مستقل ثبت‌نام یا تأیید صریح طرح.
- `R03` از نظر کد بعد از R01 قابل شروع است، اما اعمال password policy به پاسخ تصمیم ۸ کاراکتر نیاز دارد.
- `R04` نیز مستقل از مانع طراحی قابل شروع است و تصمیم password policy برای منطق PKCE آن لازم نیست.

با توجه به اولویت P0، قدم بعد پیشنهادی **R03 پس از تأیید سیاست رمز** است. طبق قرارداد پروژه، این گزارش R03 را شروع نکرده است.
