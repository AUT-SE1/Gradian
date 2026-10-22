# برنامه مرحله‌ای ثبت‌نام گرادیان

تاریخ: 2026-10-21 — نسخه 1.8 — مرور نهایی R10 انجام شد؛ release candidate آماده است ولی پذیرش نهایی به R02/build/browser/live وابسته و هنوز باز است.

## دستور اصلی برای سشن جدید

این سند برای تکمیل ثبت‌نام در پروژه موجود است. هر بار فقط تسک R انتخاب‌شده را انجام بده؛ پروژه، احراز هویت و داشبوردها را از صفر نساز. ابتدا همین سند، `GRADIAN_SESSION_CONTEXT.md` و آخرین کد را بخوان. `GRADIAN_DASHBOARD_TASKS.md` فقط سابقه و مرز کار داشبوردهاست؛ شناسه‌های R مستقل از T هستند.

اگر تنها این فایل موجود است، درباره مشاهده کد یا طرح ادعا نکن. برای اجرا، آخرین zip/checkout لازم است. شواهد baseline اولیه از `Gradian(20261020-125433).zip` تهیه شده بودند؛ R01 با ورودی تازه `Gradian-main (2).zip` دوباره روی کد جاری ممیزی شد و کد تازه بر گزارش قبلی مقدم است.

وضعیت‌ها: TODO، IN_PROGRESS، BLOCKED_DESIGN، BLOCKED_API و DONE. مانع محیط زنده را جدا در گزارش ذکر کن؛ شبیه‌سازی موفق جای پذیرش زنده نیست. تسک فقط با تکمیل معیار پذیرش DONE می‌شود. وابستگی‌ها به معنی اجرای خودکار چند تسک در یک سشن نیستند.

## هدف و دامنه

بازدیدکننده بتواند از ورودی تأییدشده ثبت‌نام وارد فرم Keycloak شود، حساب دانشجو بسازد و پس از callback معتبر وارد پنل دانشجو شود. ورود فعلی چهار نقش، خروج، کنترل دسترسی و داشبوردها حفظ شوند.

ثبت‌نام عمومی برای دانشجوست. انتخاب نقش استاد، مشاور، رتبه برتر یا ادمین در فرم عمومی اضافه نشود؛ مدیریت این نقش‌ها مسیر مجاز مدیریتی موجود را دارد و خارج از این برنامه است. OTP، پیامک، احراز مالکیت موبایل، بازیابی رمز، ورود اجتماعی، پرداخت و تأیید دستی حساب در دامنه نیستند. فرم رمزدار موازی در React یا endpoint عمومی تازه برای ساخت حساب، بدون تصمیم معماری صریح، ایجاد نشود.

## زمینه فنی کافی برای شروع

- فرانت: React 19، TypeScript، Vite، React Router، React Query و i18next؛ npm و CSS اختصاصی. کتابخانه احراز هویت جدید صرفاً برای ثبت‌نام اضافه نکن.
- بک‌اند: Django/DRF، PostgreSQL و Keycloak؛ Compose فعلی تصویر `keycloak/keycloak:26.0` دارد. نسخه اجرایی دقیق در محیط بعد بررسی شود.
- مسیر واقعی ورود: `GET /api/v1/auth/config` → درخواست Authorization Code با PKCE S256 و state → `/auth/callback` → token endpoint در Keycloak → `GET /api/v1/me` → نشست معتبر و پنل.
- `authApi.ts` فعلی جریان را مستقیم پیاده کرده است؛ `oidc-client-ts` در package.json نیست. مثال این کتابخانه در README مجوز جایگزینی معماری جاری نیست.
- نقش بک‌اند `student/consultant/professor/admin` به فرانت `student/counsellor/instructor/admin` نگاشت می‌شود. مقصد نهایی از هویت معتبر تعیین شود، نه پارامتر دلخواه URL.
- نشست فعلی زیر `gradian.auth.session`، verifier و state در sessionStorage هستند. validator، انقضا، پاک‌سازی cache و منطق T04 حفظ شوند؛ بازطراحی ذخیره نشست خارج از دامنه است.

## یافته‌های تأییدشده در کد ورودی

| موضوع | وضعیت فعلی و منبع |
| --- | --- |
| مسیر React | `frontend/src/app/router/AppRouter.tsx` مسیرهای `/login` و `/auth/callback` دارد؛ `/register` ندارد. |
| ورودی لندینگ | `frontend/src/features/landing/pages/LandingPage.tsx` دکمه‌های شروع/پورتال را به `/login` می‌فرستد؛ ورودی مستقل ثبت‌نام ندارد. |
| شروع ورود | `frontend/src/features/auth/api/authApi.ts` فقط `getConfig`، `beginLogin`، `finishLogin` و `logout` صادر می‌کند؛ `registration_endpoint` در type هست ولی استفاده نمی‌شود. |
| پیکربندی عمومی | `backend/core/accounts/views.py`، `AuthConfigView`، آدرس `registration_endpoint` را از issuer می‌سازد؛ `accounts/urls.py` endpoint عمومی ساخت کاربر ندارد. |
| فرم موجود | `backend/keycloak/themes/gradian/login/register.ftl` شامل نام، نام خانوادگی، username با برچسب موبایل، ایمیل، رمز و تکرار رمز و لینک برگشت به ورود است. |
| لینک ورود به ثبت‌نام | برخلاف توضیح README، `login.ftl` فعلی چنین لینکی ندارد و `displayInfo=false` است. |
| realm | `backend/keycloak/realm-template.json`: ثبت‌نام فعال، ایمیل به‌عنوان username غیرفعال، ایمیل تکراری ممنوع، تغییر username غیرفعال، تأیید ایمیل و بازیابی رمز غیرفعال. این‌ها وضعیت فایل‌اند؛ وضعیت realm زنده بررسی نشده است. |
| نقش تازه‌وارد | `gradian_auth/roles.py`: بدون نقش پنل → student؛ بیش از یک نقش پنل → خطا. `accounts/authentication.py` در اولین هویت جدید بدون نقش، profile را sync و اعطای student را درخواست می‌کند. |
| اعطای نقش | `accounts/profiles.py`: شکست grant نقش فقط log می‌شود. وجود profile یا موفقیت `/me` به‌تنهایی اثبات ثبت نقش در Keycloak/توکن نیست. |
| رشته | `Profile.field_of_study` می‌تواند خالی باشد؛ `PATCH /api/v1/me` برای ویرایش آن موجود است. onboarding رشته خودکار جزو دامنه نیست. |
| طرح | مرجع مستقل و تأییدشده ثبت‌نام در منابع بررسی‌شده این برنامه مشخص نشده است؛ تصاویر داشبورد جای مرجع فرم ثبت‌نام نیستند. |

### اختلاف‌های مهم مستندات و اجرا

1. R01 نشان داد README قالب حداقل رمز ۸ کاراکتر را می‌گوید ولی template آن را enforce نمی‌کرد. در R03 و پس از تأیید صریح کاربر، `passwordPolicy=length(8)` به `realm-template.json` اضافه شد. اعمال روی realm زنده موجود هنوز باید بدون حذف volume تأیید شود.
2. `user-profile.json` برای username الگوی `^09\d{9}$` دارد؛ نرمال‌سازی ارقام فارسی/عربی و پیشوند +98/0098 در `gradian_auth/mobile.py` برای بک‌اند وجود دارد، اما این به معنی پشتیبانی فرم Keycloak از همان ورودی‌ها نیست. رفتار فرم باید صریح تعیین و آزمایش شود؛ در حالت فعلی راهنمای شماره استاندارد با ارقام انگلیسی لازم است.
3. macro مشترک `register.ftl` مقدار `register.formData[name]` را برای همه فیلدها، حتی نوع password، به input می‌دهد. R05 باید بازپرکردن رمز و تکرار رمز را حذف کند؛ رمز در HTML پاسخ، log یا storage بازتاب داده نشود.
4. اعطای student بعد از صدور توکن اولیه رخ می‌دهد؛ توکن موجود خودکار تغییر نمی‌کند. سازگاری با سرویس‌های دیگر نیازمند آزمون مستقل R07 است؛ موفقیت داشبورد Core معادل SSO همه سرویس‌ها نیست.

## قرارداد جریان مطلوب

1. ورود ثبت‌نام از محل تأییدشده، و مسیر عمومی پیشنهادی `/register`؛ این مسیر جدیدِ برنامه است، نه قابلیت موجود. رفتار کاربر دارای نشست معتبر: انتقال به خانه نقش خودش، بدون ساخت حساب تازه.
2. گرفتن config واقعی، استفاده از `registration_endpoint` برگشتی و تولید verifier/state تصادفی تازه برای هر تلاش. پارامترها: `client_id`، `response_type=code`، `scope=openid`، `redirect_uri` همان callback، `code_challenge`، `code_challenge_method=S256` و `state`.
3. انتقال کامل مرورگر به Keycloak؛ رمز فقط در فرم Keycloak به `url.registrationAction` ارسال شود. استفاده از `prompt=create` یا URL ثابت localhost جای قرارداد موجود نباشد.
4. موفقیت ثبت‌نام به همان callback ورود برگردد؛ بررسی state، exchange و دریافت `/me` پیش از ذخیره نشست الزامی‌اند. پیام موفقیت ساختگی یا هدایت پیش از هویت معتبر ممنوع است.
5. خطای config، قطع شبکه، لغو، state نامعتبر، code منقضی/مصرف‌شده و شکست `/me` مسیر روشن بازیابی داشته باشند؛ retry باید جریان مناسب و امن تازه آغاز کند، نه مصرف دوباره code نامعتبر.

### فیلدها و مالک اعتبارسنجی

| فیلد فرم Keycloak | مرجع | انتظار |
| --- | --- | --- |
| firstName و lastName | `keycloak/user-profile.json` و قواعد نام در claims | الزامی، ۱ تا ۱۰۰، حروف Unicode/علامت ترکیبی/فاصله/نیم‌فاصله؛ از R03 حداقل یک letter/mark لازم است و فقط فاصله/ZWNJ رد می‌شود. |
| username | `user-profile.json` | موبایل استاندارد `09` و ۹ رقم بعد؛ یکتا. پذیرش شکل‌های دیگر فقط پس از تعیین رفتار R01. |
| email | user profile و تنظیم duplicateEmailsAllowed | الزامی، آدرس معتبر، حداکثر ۲۵۴ و یکتا؛ پیام خطای واقعی ارائه‌دهنده نمایش یابد. |
| password | سیاست اجرایی Keycloak | الزامی؛ از R03 template دارای `passwordPolicy=length(8)` است. قواعد اضافی پیچیده اختراع نشود؛ پذیرش live realm جداگانه باقی است. |
| password-confirm | جریان ثبت‌نام Keycloak | برابر رمز؛ پس از خطا خالی و بدون value بازتاب‌شده. |
| role و consultant_type | مدیریت هویت | در ثبت‌نام عمومی قابل انتخاب/اعطای دلخواه نباشند. |
| field_of_study | `PATCH /me` در Core | جزء فرم پایه نیست؛ افزودن فقط با تصمیم/طرح و تسک مستقل. |

## ترتیب و وضعیت تسک‌ها

| شناسه | عنوان | اولویت | وابستگی | وضعیت جاری |
| --- | --- | --- | --- | --- |
| R01 | ممیزی و تثبیت قرارداد ثبت‌نام | P0 | آخرین کد | DONE |
| R02 | تثبیت مرجع بصری و حالت‌های UX | P0 | R01 | BLOCKED_DESIGN |
| R03 | سازگاری قواعد Keycloak و هویت Core | P0 | R01 | IN_PROGRESS (IMPLEMENTED / PENDING_LIVE) |
| R04 | شروع ثبت‌نام با PKCE در لایه Auth | P1 | R01 | DONE |
| R05 | تکمیل فرم و قالب واقعی Keycloak | P1 | R02، R03 | IN_PROGRESS (FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_LIVE) |
| R06 | مسیر عمومی و ورودی‌های ثبت‌نام | P1 | R02، R04 | IN_PROGRESS (FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_BROWSER) |
| R07 | callback، نقش دانشجو و نشست پس از ثبت‌نام | P0 | R03، R04 | IN_PROGRESS (IMPLEMENTED / PENDING_LIVE) |
| R08 | خطاها، دسترس‌پذیری و حالت‌های نمایش | P1 | R05، R06، R07 | IN_PROGRESS (FUNCTIONAL HARDENED / BLOCKED_DESIGN / PENDING_BROWSER_LIVE) |
| R09 | آزمون یکپارچه و regression | P1 | R08 | IN_PROGRESS (STATIC/CONTRACT PRECHECK COMPLETE / BLOCKED_BY_R08 / PENDING_BUILD_BROWSER_LIVE) |
| R10 | پذیرش نهایی و تحویل مرحله ثبت‌نام | P1 | R09 و همه معیارهای مستقل | IN_PROGRESS (RELEASE-CANDIDATE REVIEW COMPLETE / FINAL ACCEPTANCE BLOCKED) |

مانع طراحی، R01/R03/R04 و بخش مستقل R07 را متوقف نمی‌کند. تسک وابسته پیش از آمادگی پیش‌نیاز انتخاب نشود. R05/R06 بدون مرجع با سلیقه عامل نهایی نشوند.

## R01 — ممیزی و تثبیت قرارداد ثبت‌نام

- وضعیت: **DONE** در 2026-10-21 برای ورودی `Gradian-main (2).zip`.
- نتیجه: authApi/router/Landing، قالب‌ها و پیکربندی Keycloak، realm/user-profile/render، claims/mobile/roles و sync profile ممیزی شدند؛ کد محصول تغییر نکرد. گزارش کامل: `docs/registration/R01_BASELINE.md`.
- یافته‌های کلیدی R01 (تاریخی، پیش از R03): `/register` و شروع registration در React هنوز وجود ندارند؛ `registration_endpoint` فقط در config حاضر است؛ login.ftl برخلاف README لینک ثبت‌نام ندارد؛ در baseline آن زمان realm template `passwordPolicy` نداشت و نام فقط فاصله با Core ناسازگار بود؛ register.ftl مقدار password را مثل سایر فیلدها بازتاب می‌داد؛ grant اولیه student در صورت شکست مسیر retry تضمین‌شده نداشت. دو مورد policy رمز و نام در R03 در سطح کد/config اصلاح شدند و پذیرش live باقی است.
- وضعیت محیط: JSONهای realm/user-profile parse شدند؛ realm زنده، build/lint و self-registration زنده اجرا نشدند و موفق اعلام نمی‌شوند.
- تصمیم سیاست رمز در 2026-10-21 بسته شد: حداقل ۸ کاراکتر سیاست رسمی self-registration است. R03 آن را در template پیاده‌سازی کرده است.
- قدم بعد پیشنهادی: پذیرش زنده R03 روی realm موجود با روش غیرمخرب و/یا تأمین مرجع R02. R04 انجام شده است؛ R05/R06 بدون مرجع R02 نهایی نشوند.

- محدوده: آخرین authApi، router، Landing، قالب‌ها، realm، user profile، render_realm، مدل/serializer، claims، نقش و sync profile خوانده شوند. کد محصول تغییر نکند.
- کار: endpointها و خطاهای واقعی، سیاست رمز، فرمت موبایل، مقدارهای الزامی و رفتار نشست موجود ثبت شوند. اختلاف README و کد را با اولویت کد روشن کن. تنظیمات فایل، realm اجراشده و تصمیم محصول را جدا ثبت کن.
- معیار پذیرش: گزارش `docs/registration/R01_BASELINE.md` با مسیر منابع، جدول قرارداد، محدودیت‌ها و تصمیم‌های باز تحویل شود؛ معلوم باشد چه چیز موجود است و چه چیز باید تکمیل شود. ابهام سیاست رمز/نرمال‌سازی به قابلیت انجام‌شده تبدیل نشود. چنانچه تصمیم تازه ضروری است، فقط همان تصمیم از کاربر گرفته شود.
- خروجی: گزارش و به‌روزرسانی این سند؛ تسک بعدی قابل اجرا تعیین شود.

## R02 — تثبیت مرجع بصری و حالت‌های UX

- وضعیت: BLOCKED_DESIGN تا دریافت مرجع یا تأیید صریح طرح پیشنهادی. مرجع داشبوردها کافی نیست.
- کار: طرح ثبت‌نام دسکتاپ، جای CTA لندینگ و لینک ورود/ثبت‌نام، متن‌ها، خطای فیلد/عمومی، انتظار، حالت غیرفعال و رفتار موبایل مشخص شوند. تم/زبان Keycloak جدا از تنظیمات React بررسی شود.
- معیار پذیرش: منبع دقیق طرح، ابعاد مرجع، دارایی‌ها و رفتارهای تأییدشده در `docs/registration/R02_DESIGN.md` ثبت باشند. اگر موبایل یا dark/English مرجع ندارد، پذیرش responsive کاربردی را از تطابق پیکسلی جدا کن. توسعه dark/English در Keycloak تنها در صورت دامنه تأییدشده انجام شود؛ realm فعلی فقط fa دارد.
- خروجی: مرجع قابل استفاده در سشن بعد و چک‌لیست مقایسه. در این تسک کد فرم ساخته نشود.

## R03 — سازگاری قواعد Keycloak و هویت Core

- وضعیت: **IN_PROGRESS (IMPLEMENTED / PENDING_LIVE)** در 2026-10-21. تصمیم محصول حداقل رمز ۸ کاراکتر تأیید و در `realm-template.json` با `passwordPolicy=length(8)` اعمال شد. name pattern در user-profile و validator Core هم‌تراز شدند تا ورودی فقط فاصله/ZWNJ رد شود. تست استاتیک جدید ۴ مورد موفق است. گزارش: `docs/registration/R03_IDENTITY_RULES.md`. Keycloak زنده در این محیط اجرا نشد؛ بنابراین تا رد واقعی رمز کوتاه/نام نامعتبر/تکرار موبایل و ایمیل روی realm موجود مشاهده نشود، R03 DONE نیست.
- کار: قواعد نام/موبایل/ایمیل، الزامی‌بودن فیلدها و سیاست رمز واقعی با قرارداد R01 تطبیق داده شوند. اعتبارسنجی باید سمت ارائه‌دهنده انجام شود، نه صرفاً HTML. شماره معتبر فرم باید هویت قابل قبول Core بسازد.
- مسیرهای محتمل: `backend/keycloak/user-profile.json`، `realm-template.json`، `scripts/render_realm.py` و تست مرتبط. فقط فایل واقعاً لازم تغییر کند؛ بازنویسی principal/مجوزها پیش‌فرض نیست.
- معیار پذیرش: نام معتبر فارسی و نیم‌فاصله قبول؛ خالی/فقط فاصله و مقدار نامعتبر رد؛ شماره/ایمیل تکراری و رمز خلاف سیاست با خطای واقعی رد شوند. ایمیل و نام‌های ثبت‌شده در claims مورد نیاز Core حاضر باشند؛ role/subtype با ورودی عمومی قابل ارتقا نباشد.
- اعمال تنظیم: تفاوت template و realm موجود توضیح داده شود؛ اصلاح template تضمین مهاجرت realm موجود نیست. روش غیرمخرب اعمال/بازگشت ثبت شود؛ برای تست، volume یا داده کاربر پاک نشود.
- خروجی: تغییر محدود، تست قواعد و راهنمای اعمال؛ اگر realm زنده اجرا نشده، نتیجه زنده تأیید نشود.

## R04 — شروع ثبت‌نام با PKCE در لایه Auth

- وضعیت: **DONE** در 2026-10-21 روی خروجی R03. گزارش: `docs/registration/R04_PKCE_START.md`.
- نتیجه: `authApi.beginRegistration()` اضافه شد و ورود/ثبت‌نام هر دو از helper مشترک `authFlow.ts` برای تولید verifier/state، S256 و پارامترهای Authorization Code استفاده می‌کنند. endpoint ثبت‌نام فقط از `registration_endpoint` config گرفته می‌شود و قبل از ذخیره PKCE/redirect با issuer از نظر protocol/origin/path سازگار می‌شود.
- همزمانی: یک lock مشترک شروع login/registration مانع overwrite شدن verifier/state در double click یا اجرای دوباره effect می‌شود؛ در شکست config یا URL نامعتبر lock آزاد می‌شود و retry تازه مجاز است. در موفقیت تا navigation قفل باز نمی‌شود.
- امنیت: verifier فقط در `sessionStorage` می‌ماند و در URL نیست؛ secret/password/token تازه‌ای وارد این flow نشده و logging حساس اضافه نشده است. callback موجود و token exchange حفظ شدند.
- آزمون اجراشده: `frontend/tests/r04-auth-flow.cjs` با source واقعی `authFlow.ts`، شش گروه سناریو را پوشش داد و موفق شد: URL/challenge، state/verifier تازه، شروع همزمان، retry پس از config failure، endpoint ناسازگار، و regression ورود عادی. این تست اثبات رندر فرم زنده Keycloak نیست.
- خارج از R04: `/register` و CTA عمومی هنوز در R06 هستند؛ template فرم در R05 است؛ ساخت حساب در backend اضافه نشد و dependency جدیدی نصب نشد.

- کار: در authApi موجود، شروع ثبت‌نام افزوده شود؛ منطق مشترک تولید verifier/state و پارامترهای OIDC با ورود بازاستفاده شود. endpoint از config بیاید و سازگاری URL/issuer پیش از انتقال بررسی شود.
- کار: double click و اجرای effect در StrictMode درخواست‌های موازی متناقض نسازد؛ شکست شروع، قفل جریان را آزاد و retry را ممکن کند. URL، client secret، رمز و توکن در log افشا نشوند.
- معیار پذیرش: درخواست به endpoint واقعی registration با S256 و state تازه ساخته شود؛ redirect_uri با callback ثبت‌شده برابر باشد؛ verifier در URL نباشد. شکست config/URL نامعتبر قابل بازیابی باشد. ورود عادی همچنان authorization endpoint را مصرف کند؛ بدون نصب کتابخانه جدید یا backend ساخت حساب تازه.
- آزمون: config کنترل‌شده، صحت URL و challenge، تلاش مجدد و شروع تکراری؛ این آزمون اثبات نمایش فرم زنده نیست.

## R05 — تکمیل فرم و قالب واقعی Keycloak

- وضعیت: **IN_PROGRESS (FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_LIVE)** در 2026-10-21 روی خروجی R04. گزارش: `docs/registration/R05_KEYCLOAK_FORM.md`.
- انجام‌شده: قرارداد `url.registrationAction`/نام فیلدها حفظ شد؛ retry فقط داده‌های غیرحساس را repopulate می‌کند و هر دو password بدون `value` و با `autocomplete=new-password` هستند؛ خطاهای field/general sanitize و به input مرتبط شدند؛ label/required/focus-visible/autocomplete/inputmode و responsive پایه تکمیل شد.
- انجام‌شده: لینک Login→Registration فقط با `realm.password && realm.registrationAllowed && !registrationDisabled??` نمایش داده می‌شود و از `${url.registrationUrl}` استفاده می‌کند؛ Registration→Login از `${url.loginUrl}` استفاده می‌کند. URL ثابت ساخته نشد.
- عمداً انجام‌نشده: password toggle تازه یا بازطراحی بصری فرم ثبت‌نام؛ چون R02 هنوز مرجع تأییدشده ندارد.
- باقی‌مانده برای DONE: رندر و submit واقعی FreeMarker در Keycloak زنده، acceptance زنده R03، retry/conflict/registrationDisabled/keyboard/mobile smoke و مقایسه تصویری با مرجع R02. تست source به‌تنهایی جای این پذیرش‌ها نیست.
- معیار اصلی تسک همچنان برقرار است: `register.ftl`، `login.ftl`، `template.ftl` و CSS قالب موجود طبق R02 نهایی شوند؛ شش فیلد با ارسال واقعی و خطای قابل مشاهده کار کنند؛ رمز پس از خطا خالی بماند و لینک نامعتبر در registration disabled دیده نشود.

## R06 — مسیر عمومی و ورودی‌های ثبت‌نام

- وضعیت: **IN_PROGRESS — FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_BROWSER** در 2026-10-21 روی خروجی R07. گزارش: `docs/registration/R06_PUBLIC_ENTRY.md`.
- انجام‌شده: مسیر مستقیم `/register` در PublicLayout و صفحه انتقال به `beginRegistration()` اضافه شد؛ نشست معتبر به خانه نقش خودش برمی‌گردد، نشست منقضی توسط validator فعلی معتبر محسوب نمی‌شود، loading/error/retry promiseها مدیریت می‌شوند و Back از Keycloak با PKCE رهاشده وارد loop انتقال خودکار نمی‌شود. `/login` دست‌نخورده مانده است.
- مانع: CTA لندینگ عمداً اضافه/تغییر نکرد، چون R02 هنوز `BLOCKED_DESIGN` است و محل/متن ورودی ثبت‌نام تأیید نشده. بنابراین R06 هنوز DONE نیست.
- کار: مسیر پیشنهادی `/register` در PublicLayout و صفحه انتقال مناسب با لایه R04 اضافه شود؛ CTA و متن مطابق R02 به آن وصل شوند. ورود `/login` حفظ شود.
- معیار پذیرش: مسیر مستقیم، refresh، back و CTAها کار کنند؛ loading/error/retry نمایش داده شود؛ retry خطای تازه را هم مدیریت کند و rejected promise بی‌رسیدگی نماند. نشست معتبر به پنل خودش برود؛ نشست منقضی ورود به ثبت‌نام را اشتباهاً مسدود نکند. لینک ثبت‌نام Keycloak نیز همان جریان معتبر را نگه دارد.
- خروجی: تغییر محدود router/page/CTA و کلیدهای ترجمه React؛ بازطراحی کل لندینگ یا منوها خارج از این تسک است.

## R07 — callback، نقش دانشجو و نشست پس از ثبت‌نام

- وضعیت: **IN_PROGRESS (IMPLEMENTED / PENDING_LIVE)** در 2026-10-21. گزارش: `docs/registration/R07_IDENTITY.md`.
- callback اکنون state را حتی برای خطای provider بررسی می‌کند، flow آغازشده (`login`/`registration`) را نگه می‌دارد، در همه خروجی‌های نهایی verifier/state/flow را پاک می‌کند و retry را با PKCE تازه از همان نوع flow شروع می‌کند.
- نشست قبلی و cache خصوصی قبل از تکمیل callback پاک می‌شوند. نشست تازه فقط پس از token exchange موفق، `/me` موفق، role mapping معتبر و `isUsableSession` ساخته/ذخیره می‌شود. 400/401/403/409 و outage ارائه‌دهنده پیام/حالت مجزا دارند.
- backend برای token بدون panel role دیگر grant دانشجو را فقط به «اولین مشاهده profile» وابسته نمی‌کند. نقش `student` به‌صورت idempotent در Keycloak ensure می‌شود؛ شکست provider به 502 تبدیل می‌شود تا درخواست بعدی بتواند retry کند و profile موجود باعث جاافتادن دائمی role نشود.
- تست‌های مستقل R07 پاس شدند؛ تست کامل Django/Keycloak و اثبات role در realm زنده + توکن تازه بعد از ورود مجدد در این محیط اجرا نشد، بنابراین DONE اعلام نمی‌شود. refresh خودکار یا SSO جدید اضافه نشده است.

- کار: callback فعلی برای ثبت‌نام بازاستفاده و خطاهای آن کامل شوند. تنها پس از token exchange، `/me` موفق و validator نشست، ذخیره و انتقال انجام شود. برای 401/403/409/اختلال ارائه‌دهنده پاسخ واقعی و راه بازیابی روشن باشد.
- کار: ایجاد profile در اولین درخواست، grant نقش student، شکست grant و توکن اولیه بدون نقش با کد واقعی بررسی شوند. اگر ایراد retry فعلی در grant باعث جاافتادن دائمی نقش می‌شود، اصلاح محدود و قابل تکرار پیشنهاد/اجرا شود؛ موفقیت نمایشی کافی نیست.
- معیار پذیرش: کاربر تازه بدون انتخاب نقش، student شود؛ mobile/name/email/sub مطابق ثبت‌نام باشد؛ رشته خالی مانع پنل نشود. نقش در Keycloak و توکن جدید پس از ورود مجدد بررسی شود. اگر برای سرویس‌ها توکن تازه لازم است، راه‌حل در قرارداد موجود مستند و تست شود؛ refresh flow خودکار و SSO همه سرویس‌ها بدون قرارداد به دامنه اضافه نشوند.
- آزمون: state گمشده/متفاوت، لغو، code منقضی/مصرف‌شده، callback تکراری، هویت ناقص و خرابی `/me` نشست معتبر جعلی نسازند؛ بازگشت از خطا جریان تازه امن آغاز کند. کاربر قبلی/cache قبلی نمایش داده نشود.
- خروجی: گزارش `docs/registration/R07_IDENTITY.md` و تغییر محدود لازم؛ نبود محیط زنده صریح ثبت شود.

## R08 — خطاها، دسترس‌پذیری و حالت‌های نمایش

- وضعیت: **IN_PROGRESS (FUNCTIONAL HARDENED / BLOCKED_DESIGN / PENDING_BROWSER_LIVE)** در 2026-10-21 روی خروجی R06. گزارش: `docs/registration/R08_ACCESSIBILITY_ERRORS.md`.
- React: Login/Register/Callback وضعیت انتظار را با live region، خطا را با alert و focus برنامه‌ای، retry را با disabled/aria-disabled و copy کامل fa/en نمایش می‌دهند. auth cardها برای RTL/LTR و light/dark از direction/theme موجود تبعیت می‌کنند و guard عرض 360px/overflow دارند.
- Keycloak theme: خطاهای field با aria-invalid/describedby/errormessage و focus اولین invalid متصل‌اند؛ mobile/email در صفحه فارسی LTR باقی می‌مانند؛ passwordها بعد از خطا repopulate نمی‌شوند؛ پیام‌های عمومی error/status semantics جدا دارند. پیام فارسی قابل‌فهم برای duplicate username/mobile، duplicate email، mismatch/short password و required/invalid value اضافه شده است.
- scope: `theme.properties` فقط `locales=fa` را اعلام می‌کند؛ انگلیسی/dark Keycloak بدون R02 ادعا نمی‌شود. CTA لندینگ و pixel-match ثبت‌نام همچنان به R02 وابسته‌اند.
- آزمون source/contract جدید: React R08 = 28 check موفق؛ Keycloak theme R08 = 7 تست موفق. regressionهای R04/R05/R06/R07/R03 نیز پاس شدند. `node_modules` در archive نبود، پس build/lint کامل و browser/Keycloak live اجرا نشده‌اند.

- کار: کل سفر لندینگ → انتقال → فرم → خطا/موفقیت → پنل با کیبورد، برچسب‌ها، focus و پیام‌های قابل فهم بررسی شود. پیام فنی خام یا موفقیت ثبت‌نام پیش از موفقیت واقعی نشان داده نشود.
- معیار پذیرش: شماره/ایمیل تکراری، رمز نامنطبق، فیلد خالی، قطع شبکه و سرویس خاموش راه اصلاح/تلاش مجدد روشن داشته باشند؛ متن/فرم در عرض کوچک سرریز نکند. موبایل و ایمیل LTR در صفحه فارسی RTL خوانا باشند. locale/themeهای پشتیبانی‌شده React خراب نشوند؛ پشتیبانی Keycloak فقط مطابق R02 ادعا شود.
- خروجی: جدول سناریو و شواهد تصویری مطابق مرجع؛ اصلاح محدود مشکلات یافت‌شده و ثبت محدودیت‌های طرح.

## R09 — آزمون یکپارچه و regression

- کار: تست‌های هدفمند و قابل تکرار برای تغییر واقعی افزوده شوند؛ ثبت‌نام واقعی با حساب آزمایشی جدا در Keycloak + Core اجرا شود. fixtureها داده غیرواقعی داشته باشند؛ رمز/توکن واقعی وارد گزارش یا artifact نشود.
- ماتریس پذیرش:
  - ثبت‌نام موفق، بازگشت معتبر، ایجاد profile، پنل دانشجو، logout و ورود مجدد همان حساب.
  - نقش student در ارائه‌دهنده و توکن تازه؛ نبود ارتقای نقش با پارامتر/فیلد دست‌کاری‌شده.
  - فیلد نامعتبر/تکراری، mismatch رمز، خطاهای callback و قطع config/Keycloak/Core.
  - دسترسی مستقیم و refresh `/register`، نشست موجود/منقضی، چند کلیک و چند تب.
  - ورود و خروج چهار نقش، 401/403 و پاک‌سازی cache؛ مسیرهای فعلی داشبورد و خدمات پسرفت نکنند.
- فرمان‌های فرانت از `frontend/`: `npm run build`، `npm run lint` و در صورت نیاز `npm run typecheck`؛ build فعلی خودش `tsc -b` دارد. تست‌های `frontend/tests/t04-auth.cjs` و regression مرتبط با تغییر، طبق harness/راهنمای خودشان اجرا شوند؛ فرمان خیالی npm test نساز.
- بک‌اند: فرمان تست و پیش‌نیازها از Makefile/README و تست واقعی همان نسخه خوانده شوند. بررسی استاتیک یا mock به‌عنوان end-to-end زنده گزارش نشود.
- خروجی: `docs/registration/R09_VERIFICATION.md` با فرمان‌ها، نتیجه، محیط، روش پاک‌سازی فقط حساب‌های آزمایشی مشخص و موارد اجرا‌نشده. نبود اجرای زنده مانع تأیید معیار زنده است.

## R10 — پذیرش نهایی و تحویل مرحله ثبت‌نام

- کار: شواهد R01 تا R09، تطبیق طرح، ثبت‌نام زنده و regression را مرور کن؛ تنظیمات لازم برای محیط موجود و روش غیرمخرب انتشار/بازگشت را ثبت کن.
- معیار پذیرش: build موفق، خطای جدید lint باقی نماند، تمام معیارهای ضروری اجرا و نتیجه ثبت شده باشد؛ مرجع مفقود یا آزمون زنده اجرا‌نشده با DONE پنهان نشود. فرض‌های حذف‌شده و محدودیت‌های مانده روشن باشند.
- خروجی: آخرین کد قابل استفاده یا patch، این سند و زمینه به‌روز، گزارش نهایی، فهرست دقیق فایل‌های تغییرکرده و قدم بعد. محیط کاربر یا داده‌ها بدون درخواست تغییر نکنند.

## قرارداد تحویل هر سشن

1. فقط تسک R خواسته‌شده و تغییر ضروری محدود آن انجام شود؛ پیش‌نیاز مستقلِ ناتمام به‌طور پنهانی اجرا نشود.
2. شناسه، وضعیت، تغییر، معیارهای بررسی‌شده، فرمان و نتیجه واقعی، مانع و قدم بعد در دفتر پیشرفت ثبت شوند.
3. همین سند و `GRADIAN_SESSION_CONTEXT.md` مطابق وضعیت تازه به‌روز شوند؛ سند داشبورد فقط در صورت تغییر واقعی مرتبط نیاز به ویرایش دارد و وضعیت Tها خودسرانه تغییر نکند.
4. کد، دو سند جاری و گزارش/تست لازم در تحویل قرار بگیرند؛ مسیرهای موقت سشن قبلی وابستگی تحویل نباشند.
5. دارایی/فونت موجود بازاستفاده شود. مقدار localhost، پورت، سیاست رمز، endpoint تازه یا طرح با حدس وارد محصول نشود.
6. فقط با اجازه صریح، تسک بعدی شروع شود؛ پیشنهاد قدم بعد به معنی اجرای آن نیست.

## دفتر پیشرفت

- 2026-10-20: آخرین zip، اسناد داشبورد و زمینه و کد مرتبط ثبت‌نام بررسی شدند؛ فقط این برنامه تهیه شد. هیچ کد، realm یا سند قبلی تغییر نکرد؛ build/test و ثبت‌نام زنده اجرا نشده‌اند. R01 تا R10 پیاده‌سازی نشده بودند؛ R02 منتظر مرجع است.
- 2026-10-21 / R01: DONE برای `Gradian-main (2).zip`؛ ممیزی قرارداد ثبت‌نام بدون تغییر محصول انجام شد. گزارش `docs/registration/R01_BASELINE.md`. realm زنده و self-registration اجرا نشدند. اختلاف policy رمز، نام فقط فاصله، لینک مفقود login→register، بازتاب password در register.ftl و شکاف retry نقش student ثبت شدند.
- 2026-10-21 / R04: DONE روی `Gradian-R03.zip`؛ شروع registration با endpoint واقعی config و PKCE مشترک login پیاده شد. تست `frontend/tests/r04-auth-flow.cjs` شش گروه سناریو را موفق کرد. گزارش `docs/registration/R04_PKCE_START.md`. `/register` و UI/CTA شروع نشدند.
- 2026-10-21 / R08: روی `Gradian-R06.zip` بخش functional/accessibility سخت‌گیری شد. React status/error/focus/retry و fa/en/light/dark auth states، Keycloak field/general error semantics، LTR mobile/email، narrow viewport و پیام‌های فارسی خطا پوشش گرفتند. `frontend/tests/r08-auth-accessibility.cjs` = 28 check و `backend/scripts/tests/test_r08_theme_accessibility.py` = 7 تست موفق؛ regressionهای R03/R04/R05/R06/R07 نیز پاس شدند. R08 به‌علت R02/BLOCKED_DESIGN و نبود browser/Keycloak live همچنان IN_PROGRESS است. گزارش: `docs/registration/R08_ACCESSIBILITY_ERRORS.md`.
- 2026-10-21 / R09: به‌علت ناتمام‌بودن R08، فقط precheck غیرزنده و تکرارپذیر اجرا شد. تست جدید frontend = 22 check، backend R09 = 5 تست و کل `backend/scripts/tests` = 125 تست موفق؛ runner `scripts/r09-registration-preflight.sh` اضافه شد. npm registry در محیط DNS نداشت، Playwright نصب نبود و Docker موجود نبود؛ بنابراین build/lint/typecheck، browser matrix و self-registration زنده موفق اعلام نمی‌شوند. R09 = IN_PROGRESS و گزارش `docs/registration/R09_VERIFICATION.md` است.
- 2026-10-21 / R10: مرور نهایی release candidate روی `Gradian-R09.zip` انجام شد. `./scripts/r09-registration-preflight.sh` دوباره موفق بود و 125 تست backend script پاس شد. `npm ping` timeout شد و `npm ci` کامل نشد؛ Playwright نصب نیست و Docker executable موجود نیست، بنابراین build/lint/typecheck، browser matrix و live registration همچنان پذیرش نشده‌اند. R02 نیز BLOCKED_DESIGN است. هیچ کد محصول در R10 تغییر نکرد؛ گزارش `docs/registration/R10_FINAL_ACCEPTANCE.md` و manifest `R10_CHANGED_FILES.txt` اضافه شد. R10 = IN_PROGRESS و FINAL ACCEPTANCE BLOCKED.
- قدم بعد پیشنهادی: R11 تعریف نشده است. ابتدا R02 و پذیرش live/browser/build باز بسته شوند، سپس R09 به DONE برسد و R10 دوباره برای پذیرش نهایی اجرا شود.

## متن آماده شروع سشن بعد

```text
این آخرین نسخه کد گرادیان و اسناد آن است.
ابتدا GRADIAN_SESSION_CONTEXT.md و GRADIAN_REGISTRATION_TASKS.md و گزارش‌های `docs/registration/R01_BASELINE.md` تا `R10_FINAL_ACCEPTANCE.md` را بخوان.
R10 مرور نهایی release candidate را انجام داده ولی DONE نیست؛ R02 BLOCKED_DESIGN و R03/R05/R06/R07/R08/R09 پذیرش‌های live/browser/build/design باز دارند. برای این برنامه R11 تعریف نشده است.
کد موجود و جریان Keycloak را مبنا بگیر؛ endpoint، سیاست اعتبارسنجی یا جزئیات طرح را حدس نزن.
معیار پذیرش همان تسک را بررسی کن و خروجی آن و هر دو سند به‌روز را تحویل بده.
اگر ورودی لازم موجود نیست، مانع را دقیق ثبت کن و نتیجه انجام‌نشده را موفق اعلام نکن.
```

برای سشن‌های بعد شناسه تسک داخل متن را با R خواسته‌شده جایگزین کن و آخرین کد/دو سند و مرجع لازم را همراهش بده.


## تحویل جاری R03 — 2026-10-21

- تصمیم کاربر: حداقل رمز ۸ کاراکتر، policy رسمی self-registration.
- `realm-template.json`: `passwordPolicy=length(8)`. `user-profile.json`: نام/نام خانوادگی باید حداقل یک Unicode letter/mark داشته باشند و فقط حروف/mark/فاصله/ZWNJ مجاز است. `gradian_auth.claims.is_valid_name` نیز همین شرط پایه را enforce می‌کند.
- تست استاتیک مستقل `backend/scripts/tests/test_registration_identity_rules.py`: چهار تست موفق. JSONها parse، Pythonها compile و sanity check نام موفق. مجموعه کامل Django/Keycloak در این محیط اجرا نشد.
- گزارش و apply/rollback غیرمخرب: `docs/registration/R03_IDENTITY_RULES.md`. `make reset` و حذف volume برای اعمال/rollback ممنوع است.
- وضعیت R03: IN_PROGRESS (IMPLEMENTED / PENDING_LIVE). پذیرش زنده realm موجود هنوز لازم است. R04 قابل شروع است؛ R02 همچنان BLOCKED_DESIGN.


## تحویل جاری R09 — 2026-10-21

- ورودی: `Gradian-R08.zip`. چون R08 هنوز DONE نیست، R09 فقط در حد precheck غیرزنده و قابل‌تکرار اجرا شد و پذیرش نهایی یکپارچه ادعا نمی‌شود.
- کد محصول، endpoint، dependency، realm data و حساب کاربر تغییر نکردند. تست‌های جدید `frontend/tests/r09-registration-contract.cjs` و `backend/scripts/tests/test_r09_registration_contract.py` و runner `scripts/r09-registration-preflight.sh` اضافه شدند.
- نتیجه runner: R04=7 گروه، R06=17 check، R07=6 گروه، R08=28 check، R09 frontend=22 check؛ R03=4، R05=6، R07 backend=5، R08 backend=7، R09 backend=5 و کل `backend/scripts/tests`=125 تست موفق. JSON parse، py_compile و node syntax check نیز موفق.
- `npm ci` به‌علت DNS `EAI_AGAIN registry.npmjs.org` کامل نشد؛ build/lint/typecheck به‌علت dependency نصب‌نشده قابل پذیرش نیستند. Playwright در محیط موجود نبود و Docker executable نیز موجود نبود؛ browser/live matrix اجرا نشد.
- وضعیت: R09 = IN_PROGRESS (STATIC/CONTRACT PRECHECK COMPLETE / BLOCKED_BY_R08 / PENDING_BUILD_BROWSER_LIVE). گزارش: `docs/registration/R09_VERIFICATION.md`.


## تحویل جاری R10 — 2026-10-21

- ورودی: `Gradian-R09.zip`. فقط final acceptance review و handoff انجام شد؛ کد محصول، endpoint، dependency، realm data و داده کاربر تغییر نکردند.
- `./scripts/r09-registration-preflight.sh` دوباره موفق شد: frontend contractهای R04/R06/R07/R08/R09 و backend contractهای R03/R05/R07/R08/R09 پاس شدند؛ کل `backend/scripts/tests` = 125 تست موفق.
- `npm ping` پس از ۲۰ ثانیه timeout شد و `npm ci` کامل نشد؛ build/lint/typecheck معتبر اجرا نشدند. Chromium موجود است ولی Playwright نصب نیست؛ Docker executable نیز موجود نیست. بنابراین browser/live acceptance همچنان باز است.
- R02 هنوز `BLOCKED_DESIGN` است؛ CTA لندینگ و pixel acceptance فرم ثبت‌نام حدس زده نشدند. R08 و R09 DONE نیستند، پس R10 نیز DONE نیست.
- گزارش نهایی: `docs/registration/R10_FINAL_ACCEPTANCE.md`. فهرست تجمعی دقیق تغییرات نسبت به baseline: `docs/registration/R10_CHANGED_FILES.txt`.
- وضعیت: `IN_PROGRESS — RELEASE-CANDIDATE REVIEW COMPLETE / FINAL ACCEPTANCE BLOCKED`. R11 تعریف نشده؛ قدم بعد بستن blockerهای R02/build/browser/live و سپس rerun R09 و R10 است.
