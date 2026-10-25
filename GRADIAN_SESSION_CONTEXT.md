# زمینه پروژه گرادیان برای سشن جدید

تاریخ: 2026-10-21 — نسخه 1.17 — پس از مرور نهایی R10؛ release candidate آماده است ولی پذیرش نهایی build/browser/live/design باز است

## دستور اصلی به عامل سشن بعد

مرحله جاری پروژه، پذیرش و تحویل ثبت‌نام روی همان معماری موجود است. ابتدا `GRADIAN_REGISTRATION_TASKS.md` و گزارش‌های `docs/registration/R01_BASELINE.md` تا `R10_FINAL_ACCEPTANCE.md` را بخوان؛ پروژه، احراز هویت یا داشبوردها را از صفر نساز. R01 و R04 DONE هستند. R02 همچنان BLOCKED_DESIGN است. R03، R05، R06، R07 و R08 از نظر کد/contract جلو رفته‌اند ولی پذیرش live/browser/design باز دارند. R09 preflight غیرزنده را کامل کرده اما به‌علت R08 و نبود build/browser/live هنوز IN_PROGRESS است. R10 release-candidate review را انجام داده ولی FINAL ACCEPTANCE BLOCKED است. برای این برنامه R11 تعریف نشده؛ قدم بعد بستن blockerها و rerun R09/R10 است. تصمیم رمز بسته شده: حداقل ۸ کاراکتر policy رسمی self-registration است.

سابقه داشبوردها در `GRADIAN_DASHBOARD_TASKS.md` معتبر است: T01 تا T05 و T07 تا T11 DONE، T06 و پذیرش کامل T12 به‌دلیل مرجع ناقص پایین دانشجو BLOCKED_DESIGN هستند. تغییر ثبت‌نام نباید این وضعیت‌ها یا UI پنل‌ها را خودسرانه بازنویسی کند.
تاریخ: 2026-10-20 — نسخه 1.12 — پس از بررسی نهایی T12

## دستور اصلی به عامل سشن بعد

کاربر می‌خواهد منو و داشبورد دانشجو، مشاور، استاد و ادمین عین طرح‌های فیگمای خودش پیاده شوند. پروژه موجود است؛ از صفر نساز. هر بار فقط یک تسک از `GRADIAN_DASHBOARD_TASKS.md` انجام بده و هر دو سند را در پایان به‌روز کن. T01 تا T05 تکمیل شده‌اند. T06 برای بخش قابل مشاهده اصلاح شد؛ تأیید نهایی پایین فریم BLOCKED_DESIGN است. T07 تا T11 تکمیل شدند. گزارش جاری: `docs/T12_FINAL_REVIEW.md`. گزارش‌های T01 تا T04 در ورودی این سشن موجود نبودند و مربوط به تحویل‌های قبلی‌اند؛ تست T04 در ورودی موجود بود و دوباره اجرا شد.

برای شروع، آخرین نسخه پروژه و اسناد را بخوان. مسیرهای موقت محیط قبلی پایدار نیستند. اگر فقط این Markdown را داری، به کد و تصاویر واقعی دسترسی نداری و نباید ادعا کنی آن‌ها را دیده‌ای. برای پیاده‌سازی دقیق، آخرین zip/checkout و تصاویر اصلی باید در سشن جدید در دسترس باشند.

## هدف محصول و نقش کاربر

گرادیان یک پورتال خدمات آمادگی آزمون با چهار پنل است. کاربر مسئول فرانت‌اند در پروژه تیمی/TA است؛ بک‌اند و سرویس‌های تیم‌ها موجود یا در حال توسعه‌اند. محتوای فعلی طرح‌ها درباره کنکور سراسری است؛ موضوع و متن محصول را خودسرانه با یک حوزه دیگر جایگزین نکن.

مرحله جاری پس از تحویل داشبوردها، برنامه ثبت‌نام است. R01 ممیزی قرارداد را بست؛ R03 قواعد هویت را در سطح کد/config پیاده کرد و هنوز پذیرش live می‌خواهد؛ R04 شروع registration با PKCE را در auth layer تکمیل کرد. سابقه UI/ناوبری/API داشبوردها همچنان معتبر است: T12 بررسی مرحله‌ای شده ولی پذیرش نهایی کامل به دلیل مرجع ناقص T06، BLOCKED_DESIGN است؛ T06 برای پایین فریم همچنان BLOCKED_DESIGN است. ساخت همه میکروسرویس‌ها یا بازطراحی داشبوردها در دامنه ثبت‌نام نیست.

## وضعیت جاری ثبت‌نام

- baseline ثبت‌نام: `Gradian-main (2).zip`; release candidate فعلی: خروجی R10 روی `Gradian-R09.zip`.
- R01 audit baseline را بست؛ R04 شروع registration با PKCE را DONE کرد.
- R03: `passwordPolicy=length(8)` و قواعد نام هم‌تراز شده‌اند؛ runtime realm موجود هنوز PENDING_LIVE است.
- R05: قالب Keycloak از password repopulation جلوگیری می‌کند، خطاها/semantics را دارد و لینک registration provider-owned است؛ R02 و FreeMarker/live smoke هنوز بازند.
- R06: route عمومی `/register` وجود دارد، session معتبر به خانه نقش خودش می‌رود و retry/Back با PKCE تازه مدیریت می‌شود؛ CTA لندینگ عمداً تا R02 اضافه نشده و browser acceptance باز است.
- R07: callback flow-aware و یک‌بارمصرف است؛ session فقط پس از token exchange و `/me` معتبر ذخیره می‌شود. grant نقش `student` retry-safe/idempotent شده و failure provider به موفقیت نمایشی تبدیل نمی‌شود؛ durable role/token تازه هنوز PENDING_LIVE است.
- R08: loading/error/focus/accessibility و fa/en/light/dark React states و Keycloak field errors سخت‌گیری شده‌اند؛ design/browser/live هنوز باز است.
- R09: preflight source/contract قابل‌تکرار موفق است و کل `backend/scripts/tests` در آخرین اجرا 125 تست پاس دارد؛ build/lint/typecheck، browser matrix و self-registration live هنوز پذیرش نشده‌اند.
- R10: final review و release handoff انجام شده، اما DONE نیست. در R10 دوباره preflight موفق بود؛ npm registry timeout شد، Playwright نصب نبود و Docker executable موجود نبود. گزارش: `docs/registration/R10_FINAL_ACCEPTANCE.md`.
- هیچ stage بعدی R11 در برنامه تعریف نشده است. بسته‌شدن R02 + build/browser/live و سپس rerun R09/R10 لازم است.

## منابع بررسی‌شده

- ورودی جاری ثبت‌نام R01: `Gradian-main (2).zip`؛ auth، router/Landing، Core identity و فایل‌های Keycloak ممیزی شدند. گزارش `docs/registration/R01_BASELINE.md`. هیچ build/test زنده یا تغییر محصول انجام نشد.
در این مرحله هدف، تکمیل UI، ناوبری، دسترسی و اتصال APIهای آماده است؛ ساخت همه میکروسرویس‌ها در دامنه این درخواست نیست. کاربر در سشن جاری فقط T12 را درخواست کرد؛ بررسی نهایی و تحویل مرحله‌ای انجام شد. T12 بررسی شد؛ تحویل مرحله‌ای و تست‌ها موفق‌اند، ولی پذیرش نهایی کامل آن به دلیل مرجع ناقص T06، BLOCKED_DESIGN است. T06 برای پایین فریم همچنان BLOCKED_DESIGN است؛ این مانع اتصال مستقل T07 نیست.

## منابع بررسی‌شده

- ورودی جاری T12: `Gradian(20261020-122909).zip`؛ چهار مرجع نام‌برده بازیابی، مشاهده و در `docs/t12-verification/` حفظ شدند. نتیجه جاری در انتهای این سند و گزارش T12 است.

- ورودی جاری T11: `Gradian(20261020-121042).zip`؛ کد و دو سند خوانده شدند. تصویر مرجع در این ورودی وجود ندارد؛ چیدمان پنل‌ها بازطراحی نشده و تطابق پیکسلی تازه ادعا نمی‌شود.
- ورودی تاریخی T10: `Gradian(20261020-113329).zip`؛ آخرین کد و هر دو سند ریشه خوانده شدند. تصاویر و گزارش‌های تاریخی در zip نبودند؛ مرجع ادمین `Screenshot (2418).png` با نام دقیق بازیابی و واقعاً مشاهده شد. منابع دیگر زیر سابقه‌اند.
- `Screenshot (2418).png`: مرجع کامل ادمین، node 20-18، اندازه 1280×978؛ مرجع واقعی تطبیق و پذیرش T10 بود.
- `Screenshot (2419).png`: مشاور، node 4-3083، اندازه 1280×800.
- `Screenshot (2420).png`: استاد، node 4-3475، اندازه 1280×927.
- `Screenshot (2421).png`: دانشجو، node 4-2272، اندازه 1280×1978؛ پایین فریم در screenshot کامل نیست.
- طرح موبایل و export اصلی فونت/آیکن موجود نیستند. اندازه‌های پایه T02 همچنان تا تسک تطبیق هر نقش موقت‌اند.
- خروجی تاریخی T10: `Gradian-T10.zip` کد کامل آخرین ورودی به همراه تغییرات T10، دو سند، گزارش و تست‌هاست؛ node_modules، dist، cache و تصاویر مرورگر بسته‌بندی نمی‌شوند.

## اولویت منابع و جلوگیری از اطلاعات منسوخ

ترتیب تصمیم: آخرین خواسته صریح کاربر و طرح همان نقش، سپس آخرین کد و قرارداد واقعی API، سپس این سند و برنامه تسک‌ها، سپس راهنمای معماری قدیمی.

داخل پروژه `frontend/GRADIAN_FRONTEND_PROJECT_GUIDE.md` وجود دارد، اما بخشی از آن مربوط به قبل از پیاده‌سازی است: ادعای «کد React/Django موجود نیست» و «Auth مشخص نشده» اکنون درست نیست. قواعد مفید معماری و i18n آن را حفظ کن، ولی گزارش وضعیت قدیمی را مبنای بازسازی پروژه قرار نده.

## فناوری و ساختار واقعی

- Frontend: React 19.1، TypeScript 5.9، Vite 7.1، React Router 7.9، TanStack React Query 5.90، i18next/react-i18next.
- package manager: npm؛ `package-lock.json` موجود است.
- UI عمدتاً CSS اختصاصی است؛ Tailwind، Redux و کتابخانه UI تازه بدون نیاز واقعی اضافه نشوند.
- Backend: Django/DRF، PostgreSQL 17 و Keycloak 26.0 در Docker Compose؛ نسخه دقیق Python/Django از Dockerfile و requirements آخرین کد خوانده شود. Dockerfile مرجع Python 3.13-slim است.
- پوشه‌های اصلی: `frontend/` و `backend/` در ریشه Gradian؛ تیم‌ها زیر `backend/teams/team1` تا `team10`.
- شبکه مشترک Docker: `gradian` با external=true.

### نقاط مهم فرانت‌اند

- `src/main.tsx`: QueryClientProvider، I18nProvider، ThemeProvider، AuthProvider و BrowserRouter را ترکیب می‌کند.
- `src/app/App.tsx`: AppRouter را رندر می‌کند.
- `src/app/router/AppRouter.tsx`: مسیرها و ProtectedPortal.
- `src/app/layouts/PortalLayout.tsx`: پوسته و منوی موجود؛ لوگو لینک خانه، خروج با جلوگیری از شروع ورود تازه.
- `src/app/layouts/PortalHeaderActions.tsx`: هدر مشترک چهار نقش؛ نام، avatar، رشته، subtype مشاور و اعلان‌های واقعی از query مشترک T05.
- `src/app/hooks/useMobileSidebar.ts`: breakpoint، inert، تمرکز، Escape/Tab، resize، اسکرول و بستن روی تغییر مسیر.
- `src/app/layouts/PublicLayout.tsx`: بخش عمومی؛ با تغییر داشبورد بی‌دلیل دست‌کاری نشود.
- `src/app/navigation/navigation.config.ts`: NavigationItem، گروه‌بندی و مقصد منوهای نقش‌ها.
- `src/app/providers/AuthProvider.tsx`: نشست، انقضای زنده، storage event و پاک‌سازی کش خروج/تغییر هویت.
- `src/shared/auth/session.ts`: runtime validation نقش/ساختار/انقضا؛ expiresAt ضروری است.
- `src/shared/auth/authEvents.ts`: 401 با token اولیه درخواست؛ پاسخ قدیمی نشست جدید را باطل نمی‌کند.
- `src/shared/api/queryClient.ts`: factory مشترک QueryClient؛ بدون retry روی 401/403.
- `src/features/auth/api/authApi.ts`: دریافت پیکربندی Auth، شروع login/registration، callback، دریافت /me و logout.
- `src/features/auth/api/authFlow.ts`: helper مشترک R04 برای validation issuer/registration endpoint، ساخت PKCE S256 و lock شروع همزمان login/registration.
- `src/features/auth/api/authApi.ts`: دریافت پیکربندی Auth، PKCE، callback، دریافت /me و logout.
- `src/features/auth/pages/LoginPage.tsx` و `AuthCallbackPage.tsx`: ورود و callback.
- `src/features/portal/pages/PortalHomePage.tsx` و `components/PortalHome.tsx`: خانه هر نقش؛ دانشجو محتوا دارد، سه نقش دیگر بوم خالی دارند.
- `src/features/portal/config/portalContent.ts`: داده و مقصد کارت‌های داشبورد.
- `src/features/portal/components/ServicePage.tsx`: معرفی/ورود به سرویس؛ اجرای کامل سرویس نیست.
- `src/features/portal/components/PortalIcon.tsx`: مجموعه آیکن موجود.
- `src/shared/api/httpClient.ts` و `ApiError.ts`: درخواست و خطا؛ T05 Bearer را فقط در درخواست‌های خصوصی panelApi اعمال می‌کند؛ برای URL خارجی یا API عمومی به‌صورت سراسری اضافه نمی‌شود.
- `src/shared/types/auth.ts` و `portal.ts`: نوع نشست و نقش‌ها.
- `src/shared/styles/globals.css`: قواعد عمومی، Landing و Login.
- `src/shared/styles/portals.css`: از T02 قواعد پنل‌ها و responsive، فونت محلی و توکن‌های scoped؛ بعد از globals در main import می‌شود.
- `src/assets/fonts/`: سه subset Vazirmatn variable و مجوز OFL؛ نام font-face پنل Gradian Portal است.
- `src/locales/fa/` و `src/locales/en/`: namespaceهای auth، common، navigation و portal.
- `vite.config.ts`: alias برابر `@ → src`؛ proxy مسیر `/api` به بک‌اند.

## وضعیت واقعی منو و داشبوردها

منو حذف نشده است. PortalLayout برای `instructor`، `counsellor` و `admin` سایدبار می‌سازد و منو از navigation.config می‌آید. برای student یک شاخه مجزا فقط با هدر و محتوا وجود دارد. در تصویر مرجع دانشجو هم سایدبار داخل فریم انتخاب‌شده دیده نمی‌شود؛ منوی دانشجو نباید صرفاً از روی حدس افزوده شود.

داشبورد دانشجو از T07 خوشامدگویی، tip، streak، countdown و feed را از GET /student/dashboard می‌گیرد. تعداد پست‌ها از آرایه API است و پست نمونه سمت فرانت وجود ندارد. ۹ کارت با ترتیب و عنوان‌های مرجع و تب‌های اجتماعی غیرفعال حفظ شده‌اند. PortalHome برای نقش‌های مدیریتی فقط بوم خالی رندر می‌کند؛ این با فریم‌های خالی مشاور و استاد سازگار است، ولی عملکرد سرویس‌های زیرمنو هنوز پیاده‌سازی کامل محسوب نمی‌شود.

از T05 لینک ثابت خدمات از router و portalContent حذف شده است. `api/serviceRoutes.ts` نگاشت path به key را دقیقاً از `backend/seed/content/services.yaml` نگه می‌دارد؛ مقصد و status فقط از registry می‌آیند. منوی سرویس ناموجود غیرفعال و ServicePage در ورود مستقیم بدون لینک خروجی است. پروفایل همچنان مسیر داخلی معتبر دارد و اقدام ورود به سرویس آن هم با registry کنترل می‌شود.

لایه جدید `src/features/portal/api/panelApi.ts` و `panelAdapters.ts`، و hooks در `hooks/usePanelData.ts`: پاسخ panel، envelope خدمات و اعلان‌ها را validate می‌کنند؛ خطای قرارداد با داده نمونه پنهان نمی‌شود. خدمات تمام صفحات با limit/offset جمع می‌شوند؛ اعلان‌ها صفحه‌به‌صفحه در dialog نمایش داده می‌شوند. URL next/previous فقط نشانه وجود صفحه است و با Bearer دنبال نمی‌شود. کلیدها `['portal', user.id, primaryRole, resource, ...]`، درخواست‌ها دارای AbortSignal و هدر Authorization هستند. query هدر میان layout و header dedupe می‌شود.

هدر از full_name تازه استفاده می‌کند؛ نام خالی فقط کاربر/User است. avatar واقعی در صورت وجود و بارگذاری موفق نمایش داده می‌شود؛ تصویر خراب مخفی می‌شود. رشته از field_of_study_label پاسخ واقعی نمایش داده می‌شود؛ consultant_type برچسب مشاور/رتبه برتر را تعیین می‌کند. شمارش از state و days_remaining/label پاسخ می‌آید؛ امروز و گذشته هم پشتیبانی می‌شوند. درصد پروفایل قرارداد ندارد و همچنان نمایش داده نمی‌شود (BLOCKED_API فقط برای این قابلیت، نه کل T05).

در T07 خوشامدگویی شخصی‌شده و tip، شمارش معکوس، current_days و تمام فیلدهای قابل نمایش feed به `/student/dashboard` متصل شدند. نام و رشته هدر از panel واقعی می‌آیند. query داشبورد فقط در خانه دانشجو فعال است؛ سایر نقش‌ها هیچ درخواست این endpoint را ندارند. کلید آن `portal/user.id/primaryRole/student-dashboard` است؛ AbortSignal و پاک‌سازی کش T04 حفظ شده‌اند. null هر بلوک و فهرست خالی با وضعیت روشن پشتیبانی می‌شود؛ خطای قرارداد یا HTTP به داده نمونه تبدیل نمی‌شود. خدمات همچنان از registry می‌آیند؛ description و button_label آن در صورت وجود استفاده می‌شوند. آمار، زمان‌بندی و نام مشاور نمونه کارت‌ها حذف شدند. streak و feed خود بک‌اند هنوز demo هستند. بوم خانه استاد/مشاور/ادمین خالی ماند و سایدبار دانشجو اضافه نشد.

## نقش‌ها و مسیرها

- دانشجو: backend `student` → frontend `student` → `/student`.
- مشاور: backend `consultant` → frontend `counsellor` → `/counsellor`.
- استاد: backend `professor` → frontend `instructor` → `/instructor`.
- ادمین: backend `admin` → frontend `admin` → `/admin`.
- `consultant_type` می‌تواند consultant یا top_ranker باشد؛ در UI مشاور اثر دارد، پنل پنجم فرض نشود.
- از T04 aliasهای `/professor/*` و `/consultant/*` به instructor/counsellor با حفظ suffix، search و hash می‌روند؛ مقصد محافظت‌شده است.
- مسیرهای دانشجو: exams، question-bank، final-exams، private-class، marketplace، consultation، major-selection، top-ranker، courses، community.
- مسیرهای استاد: profile، progress، questions، courses، private-class، resources.
- مسیرهای مشاور: profile، students، experiences، troubleshooting، sessions، resources.
- مسیرهای ادمین: exams، sessions، products.

از T04 نشست با runtime validator بررسی می‌شود: id، token، نام رشته‌ای، نقش معتبر و expiresAt معتبر الزامی‌اند. انقضا در load، timer و focus/visibility بررسی می‌شود؛ storage event حساب/خروج تب‌ها را هماهنگ می‌کند. کاربر نقش دیگر به خانه خودش می‌رود. guard فرانت جای permission سرور نیست.

## احراز هویت فعلی

1. فرانت از `GET /api/v1/auth/config` اطلاعات issuer و client_id را می‌گیرد.
2. verifier و state ساخته و در sessionStorage ذخیره می‌شوند؛ Authorization Code + PKCE S256 اجرا می‌شود.
3. بازگشت به `/auth/callback`، بررسی state و مبادله code در token endpoint خود Keycloak.
4. درخواست `GET /api/v1/me` با Bearer token و نگاشت panel بک‌اند به نقش فرانت.
5. نشست شامل accessToken، refreshToken احتمالی، idToken، expiresAt و user است و زیر کلید `gradian.auth.session` در localStorage نگهداری می‌شود.
6. logout نشست محلی و query/mutation cache را پاک و با end_session_url به Keycloak هدایت می‌کند. رفتار T03 برای جلوگیری از شروع ورود تازه حفظ شد.
7. Promise callback فقط هم‌زمان‌ها را dedupe می‌کند و بعد از settle آزاد می‌شود؛ نقش ناشناخته/session نامعتبر /me ذخیره نمی‌شود. خطاهای callback 401/403 پیام جدا دارند. refresh flow اضافه نشده است.

در package.json مرجع `oidc-client-ts` موجود نیست؛ جریان فعلی مستقیم پیاده شده است. هنگام تکمیل داشبورد، این dependency را بی‌دلیل دوباره اضافه نکن. client secret مربوط به بک‌اند است و نباید در VITE_* یا bundle قرار بگیرد.

## قراردادهای API که در کد وجود دارند

پیشوند اصلی `/api/v1` است. فایل‌های منبع: `backend/core/gradian/urls.py`، `accounts/urls.py`، `panels/urls.py` و `registry/urls.py`. serializerها و OpenAPI آخرین پروژه، مرجع دقیق shape هستند.

- `GET /auth/config`: پیکربندی ورود عمومی.
- `GET /me`: هویت، role، panel، home_path، نام، رشته، avatar و consultant_type.
- `GET /panel`: panel و home_path، header شامل full_name/avatar/consultant_type/field_of_study/field_of_study_label، و countdown.
- `GET /panel/services`: خدمات نقش جاری با ترتیب registry. موارد غیرفعال/بدون URL هم برمی‌گردند با status unavailable و url=null. envelope و pagination از تنظیمات و serializer بررسی شود.
- `GET /student/dashboard`: فقط دانشجو؛ welcome، countdown، study_streak و experience_feed. welcome با نام دانشجو شخصی می‌شود. streak و feed در بک‌اند فعلی محتوای demo هستند.
- `GET /notifications`: اعلان‌های همین کاربر، pagination و unread_count. فیلدهای هر اعلان: id، title، body، created_at و is_read؛ endpoint فعلی فقط نمایش است.
- `/admin/users` و `/admin/users/<uuid:sub>` در accounts وجود دارند؛ روش‌ها و مجوزها از views خوانده شوند. وجود این API به معنی درخواست افزودن مدیریت کاربران به طرح فعلی نیست.
- `GET /landing`: محتوای عمومی؛ خارج از تغییرات اصلی این برنامه.
- OpenAPI: `/api/schema/`؛ Swagger: `/api/docs/`؛ health: `/health/live` و `/health/ready` خارج از پیشوند v1.

در فایل‌های بررسی‌شده API مستقلی با عنوان instructor/dashboard یا consultant/dashboard تأیید نشده است؛ برای داده مشترک از panel و registry استفاده شود. endpoint برای درصد پروفایل، لایک پست، ذخیره، mark-as-read یا آمار ساختگی فرض نشود. اگر قرارداد وجود ندارد، بخش وابسته با BLOCKED_API ثبت شود، ولی کار مستقل UI ادامه پیدا کند.

## مرجع بصری و موارد ناقص

### دانشجو

فریم 1280×1978، هدر سفید، پس‌زمینه بسیار روشن، رنگ اصلی سرمه‌ای، خوشامدگویی و دو ویجت، شبکه ۳×۳ خدمات و شبکه اجتماعی. تصویر کامل ارتفاع فریم را نشان نمی‌دهد؛ برای پایین صفحه مرجع کامل لازم است. رنگ انتخاب‌شده در پنل فیگما `#F7F9FB` دیده می‌شود. این شاهد به معنی تعیین دقیق همه رنگ‌ها نیست.

### استاد

ارتفاع 927 و عرض 1280، در مرجع واقعی Screenshot (2420).png تأییدشده در T09، سایدبار راست با تکمیل پروفایل و منوی گروه‌بندی‌شده، شمارش معکوس پایین، هدر نام/نقش و اعلان/خروج، بوم مرکزی خالی. دو عکس این مجموعه همین فریم را نشان می‌دهند. عرض و فاصله واقعی را از فریم استخراج کن؛ scale نمایش مرورگر را به عنوان px نهایی استفاده نکن.

### مشاور

فریم 1280×800، سایدبار راست و منوی مشاور، هدر مشابه، شمارش معکوس پایین و بوم مرکزی خالی. مقایسه با استاد نباید ارتفاع متفاوت فریم را از بین ببرد.

### ادمین و موبایل

مرجع کامل ادمین اکنون `Screenshot (2418).png` با فریم 1280×978 است؛ شامل همان سه آیتم منوی موجود، هدر، شمارش پایین و بوم خالی. مرجع و نتیجه در T10 مقایسه شدند و پوسته/ناوبری DONE است؛ تطابق پیکسلی assetها ادعا نمی‌شود. هیچ منوی کاربران یا آمار جدیدی از وجود API استنباط نشود. طرح اختصاصی موبایل موجود نیست؛ رفتار responsive فقط تصمیم فنی و آزموده‌شده است.

## اجرای محلی و وضعیت زیرساخت

سیستم کاربر Windows/PowerShell و Docker Desktop است. خطای قبلی به نبود `backend/.env` مربوط بود. راهنمای ساخت env، شبکه، realm، seed و اجرای سرویس‌ها داده شد؛ کاربر گفته «این کار را کردیم» و می‌خواهد وارد فرانت شود. بنابراین رفع setup را از اول تکرار نکن؛ فقط در صورت خطای فعلی بررسی کن. در محیط بررسی، کانتینرهای سیستم کاربر اجرا و تأیید نشده‌اند.

بک‌اند از backend اجرا می‌شود. آماده‌سازی اولیه‌ای که توضیح داده شد:

```powershell
Copy-Item .env.example .env
docker network inspect gradian
# فقط اگر شبکه وجود ندارد:
docker network create gradian
docker compose build core tools
docker compose run --rm -T -w /repo tools python scripts/render_realm.py
docker compose run --rm -T -w /repo tools python scripts/seed_generate.py
docker compose up -d --build
docker compose exec core python manage.py migrate --noinput
docker compose exec core python manage.py loaddata profiles services landing widgets
```

Copy-Item فقط برای env مفقود است؛ env تنظیم‌شده را برای تکرار setup overwrite نکن. ریست volumeها ضروری نیست و داده‌ها را از بین می‌برد. در PowerShell دستورها یک‌خطی باشند و `\` انتهای دستور کپی نشود.

پورت‌ها: core روی 8000، Keycloak روی 8080، PostgreSQL روی host پورت 5433 و داخل شبکه 5432؛ frontend dev روی 5173. KEYCLOAK_PUBLIC_URL مرورگر localhost است، KEYCLOAK_URL داخل شبکه http://keycloak:8080. FRONTEND_URL باید با origin واقعی فرانت و redirectهای realm هماهنگ بماند. realm import برای تغییرات بعدی لزوماً خودکار به‌روز نمی‌شود؛ برای آن بدون بررسی reset پیشنهاد نده.

اجرای فرانت از پوشه frontend:

```powershell
npm ci
npm run dev
```

یا با Compose موجود، پس از آماده بودن شبکه و بک‌اند:

```powershell
docker compose up -d --build
```

در اجرای npm، Vite proxy به طور پیش‌فرض http://localhost:8000 است؛ در کانتینر فرانت، VITE_DEV_PROXY_TARGET برابر http://core:8000 تنظیم شده است. VITE_API_BASE_URL پیش‌فرض `/api/v1` است. Compose production جدا روی 8081 تعریف شده؛ قبل از استفاده، آدرس API، CORS و redirect فرانت production بررسی شوند. برای انجام UI، مهاجرت زیرساخت production درخواست نشده است.

## بررسی کیفیت و قواعد تغییر

- متن‌های رابط از fa/en locale بیایند؛ متن فارسی جدید در JSX پراکنده نشود.
- ظاهر فارسی RTL روشن مرجع اصلی است؛ پشتیبانی فعلی انگلیسی/LTR و dark theme خراب نشود.
- CSS و اجزای موجود اصلاح شوند؛ ساخت منو یا provider موازی ممنوع مگر با دلیل ثبت‌شده.
- API layer، query و view model از JSX جدا باشند. React Query موجود بازاستفاده شود.
- خطاهای 401، 403، network و 500 از empty و success تفکیک شوند؛ خطا با fallback نمونه پنهان نشود.
- چک‌های موجود: `npm run build` و `npm run lint`. `npm run typecheck` در T01 به `tsc -b` اصلاح شد تا references را واقعاً بررسی کند؛ build نیز همین بررسی را دارد. فایل eslint.config.js اکنون موجود است.
- در package.json مرجع script تست خودکار وجود ندارد. ادعای اجرای تست ناموجود نشود؛ smoke test ورود نقش‌ها، refresh، خروج، خدمات خاموش و نمای موبایل ثبت شود.
- برای تطابق UI تصویر نتیجه در اندازه واقعی همان فریم مقایسه شود؛ صرف build موفق، تأیید تطابق نیست.
- secret، token یا رمز واقعی در مستند تحویل، screenshot یا commit قرار نگیرد.
- کد بک‌اند، Landing، Login، Docker و امکانات سرویس‌ها فقط به ضرورت تسک تغییر کنند؛ تمیزکاری نامرتبط انجام نشود.

## وضعیت تحویل و قدم بعد

- T01 تا T04: DONE طبق سوابق ورودی. گزارش‌های قدیمی در این zip موجود نبودند؛ از وجودشان در بسته جدید ادعا نشود. کد و تست‌های T04 موجود و حفظ شده‌اند.
- T05: DONE در 2026-10-19؛ کد کامل در `Gradian-T05.zip`. گزارش پذیرش و فهرست تغییرات `docs/T05_SHARED_DATA.md`؛ شواهد مرورگر و JSON نتایج در `docs/t05-verification/`.
- فقط سه GET موجود panel، panel/services، notifications استفاده شدند. بک‌اند، auth/PKCE، Landing/Login، Docker و package dependencies تغییر نکردند.
- build و lint نهایی موفق؛ lint صفر خطا و همان سه warning react-refresh در providerهای قبلی. 20 گروه تست T05 و 39 گروه regression T04 موفق.
- سناریوها با Playwright/Chromium و پاسخ‌های کنترل‌شده مطابق serializer واقعی اجرا شدند؛ API زنده، Keycloak و کانتینرهای سیستم کاربر اینجا اجرا نشده‌اند. تأیید اتصال کد، جای تست محیط واقعی کاربر نیست.
- درصد پروفایل BLOCKED_API باقی است؛ endpoint/درصد تخمینی ساخته نشده. اعلان‌ها فقط خواندنی‌اند؛ بازکردن dialog آن‌ها را خوانده‌شده نمی‌کند. iframe/SSO سرویس‌ها و امکانات خود سرویس‌ها خارج از T05 هستند؛ اقدام فعلی ورود، بازکردن URL معتبر registry است.
- مرجع کامل ادمین در T10 مشاهده و تطبیق شد؛ T10: DONE. پایین دانشجو و فونت/آیکن اصلی هنوز ناقص‌اند.
- وضعیت جاری T06: BLOCKED_DESIGN فقط برای تأیید نهایی بخش پوشیده/خارج تصویر. بخش قابل مشاهده بازتنظیم شد؛ گزارش `docs/T06_STUDENT_VISUAL.md`. نهایی‌سازی T06 نیازمند مرجع کامل است. T07 اتصال welcome/streak/feed را انجام داده است؛ T08 تا T10 نیز تکمیل شدند و T11 تکمیل شده و تسک بعدی T12 است.

## قالب ثبت پایان هر سشن

```text
تاریخ:
تسک:
وضعیت: DONE | IN_PROGRESS | BLOCKED_DESIGN | BLOCKED_API
آخرین نسخه کد/commit/نام zip:
مرجع بصری استفاده‌شده:
فایل‌های تغییرکرده:
APIهای استفاده‌شده:
فرمان‌ها و نتیجه واقعی بررسی:
محدودیت‌ها و موارد باقی‌مانده:
تصمیم جدید و علت:
تسک بعدی:
```

کاربر در سشن بعد آخرین کد، این دو سند و تصاویر مرجع لازم را می‌دهد. گزارش این سند جای بررسی آخرین کد را نمی‌گیرد. پس از هر تسک، اطلاعات منسوخ را اصلاح کن تا سشن بعد مجبور به حدس یا تکرار کار نباشد.

## سابقه تحویل T06 — 2026-10-20

- ورودی واقعی `Gradian(20261020-085854).zip`؛ دو سند ریشه پیش از تغییر خوانده شدند. مسیرهای فرانت موجود بازاستفاده شدند.
- مرجع دانشجو `image(20261020-091404).png`؛ عرض فریم 1280 و ارتفاع 1978. پنج تصویر جدید بررسی شدند؛ 091410 مرجع کامل پایین دانشجو نیست. منبع و برش قابل مشاهده با ابعاد نرمال‌شده در docs/t06-verification حفظ می‌شود.
- فقط PortalHome، StudentIcon جدید، portals.css و localeهای fa/en تغییر کردند؛ هیچ endpoint، dependency، backend یا auth تغییر نکرد. پیکربندی کارت‌ها از قبل ترتیب درست را داشت و بازاستفاده شد.
- سه ستون در عرض مرجع، کارت‌های حدود 205px، فاصله‌های نزدیک به تصویر، هدر و badge نقش، ویجت‌ها، تب‌های زیر عنوان، ضمیمه صوتی نمایشی و آیکن‌های پست اصلاح شدند. SVGها بازسازی ساده‌اند و asset قطعی فیگما نیستند.
- نام خوشامدگویی، streak و feed هنوز داده نمایشی پیشین‌اند؛ T07 انجام نشده. شمارش و خدمات همچنان از API مشترک T05 می‌آیند. توضیح نمایشی بودن feed و غیرفعال بودن فیلترها اضافه شد؛ پخش صوت/لایک/ذخیره ساختگی وجود ندارد.
- گزارش بررسی، وضعیت پذیرش و محدودیت‌ها: `docs/T06_STUDENT_VISUAL.md`. گزارش‌ها و تصاویر T05 که اسناد قبلی نام می‌بردند در zip ورودی این سشن موجود نبودند؛ تست T05 موجود است.

بررسی نهایی T06: build موفق؛ lint صفر خطا و سه هشدار قبلی؛ ۸ گروه مرورگر T06 و ۲۰ گروه regression T05 موفق. API زنده اجرا نشد.


## سابقه تحویل T07 — 2026-10-20

- منبع واقعی این سشن: `Gradian(20261020-095450).zip` شامل آخرین کد و دو سند؛ فقط فایل‌های همین ورودی مبنای تغییر بوده‌اند. تصاویر مرجع و گزارش‌های قدیمی docs در این zip نبودند؛ نام تصاویر بخش‌های قبل صرفاً سابقه است. ظاهر CSS و شبکه T06 بازطراحی نشد و ادعای تطابق پیکسلی تازه وجود ندارد.
- منابع قرارداد: `backend/core/panels/content.py`، `serializers.py`، `views.py` و `backend/seed/content/widgets.yaml`. هیچ endpoint یا قرارداد جدید و هیچ تغییر بک‌اندی اضافه نشده است.
- adapter و نوع جدید در panelApi/panelAdapters؛ hook جدید useStudentDashboard؛ PortalHome موجود تکمیل شد و ترجمه‌های فارسی/انگلیسی داده نمونه حذف شدند.
- آمار بدون قرارداد خدمات حذف شد؛ نام نویسنده، عنوان، excerpt، likes و comments از feed می‌آیند. avatar فقط حرف اول author است؛ attachment، برچسب، زمان انتشار یا bookmark ساختگی وجود ندارد. best_days و week اعتبارسنجی می‌شوند اما چون جای تأییدشده‌ای در طرح ندارند، ویجت تازه برایشان ساخته نشد.
- `countdown` طبق serializer فعلی non-null است؛ برای تاب‌آوری null صریح هم پذیرفته می‌شود. نبود کلید یا shape نامعتبر خطا محسوب می‌شود. سه بلوک محتوایی دیگر طبق قرارداد nullable هستند.
- بررسی: build و typecheck داخل آن موفق؛ lint صفر خطا و همان سه هشدار Fast Refresh قبلی؛ ۲۲ گروه T07، ۲۰ گروه T05 و ۸ گروه T06 با API کنترل‌شده در Chromium موفق. نتایج JSON همراه کد است. API زنده، Docker و Keycloak این محیط اجرا نشدند؛ این بررسی تأیید سرویس مستقل شبکه اجتماعی نیست.
- دو تست قبلی T05/T06 برای پاسخ تازه و تعداد درخواست مجاز دانشجو به‌روز شدند؛ معنای سایر assertionها حفظ شد. تست T07 و fixture قرارداد همراه تحویل هستند.
- خروجی: `Gradian-T07.zip` کد کامل ورودی با تغییرات T07 و هر دو سند. node_modules، dist، cacheهای تولیدی و تصاویر مرورگر در آرشیو تحویل نیستند. تصاویر مرورگر فقط برای بازرسی داخلی استفاده شدند.
- گزارش کامل و فهرست فایل‌ها: `docs/T07_STUDENT_DATA.md`. تسک بعدی T08 با درخواست صریح؛ محدودیت T06 تغییری نکرده است.


## سابقه تحویل T08 — 2026-10-20

- ورودی: `Gradian(20261020-105621).zip`؛ دو سند ریشه پیش از تغییر خوانده شدند. وضعیت T08: DONE برای پوسته و ناوبری مشاور؛ تسک بعدی T09 فقط با درخواست کاربر.
- مرجع واقعی: `image(20261019-083705).png`، node 4-3083، screenshot با ابعاد 1920×1080 و فریم طراحی 1280×800. فریم حدود x=510..1475 و y=302..905 است؛ نسبت نمایش حدود 0.754 است و 60% فیگما مستقیماً ضریب پیکسل خروجی فرض نشد. مرجع بازیابی و مشاهده شد؛ نام Screenshot (2419).png صرفاً سابقه است.
- عرض 288px سایدبار و ارتفاع 64px هدر موجود مناسب بودند. فقط فاصله‌های اختصاصی مشاور، شکل آیکن‌های همان نقش، دکمه پروفایل و کارت شمارش اصلاح شدند. CSS دیگر نقش‌ها حفظ شد. مرکز خانه خالی است؛ آمار یا گزارش تازه اضافه نشد.
- عنوان و ترتیب پنج آیتم و مسیرهای ثبت‌شده از قبل درست بودند و حفظ شدند. آیکن‌های reports/experience/help/headset/library به SVG ساده نزدیک به مرجع تغییر کردند؛ alarm و نشان تأیید فقط در پوسته مشاور استفاده می‌شوند. asset اصلی فونت/آیکن موجود نیست و تطابق پیکسلی ادعا نمی‌شود.
- هدر نام و consultant_type و شمارش از panel واقعی می‌آیند؛ سرویس‌ها از registry هستند. درصد پروفایل همچنان BLOCKED_API است؛ تکمیل پروفایل به مسیر داخلی موجود می‌رود. هایلایت مرجع به خانه تحمیل نشد و فقط مسیر واقعی فعال می‌شود.
- فایل‌های محصول: `frontend/src/app/navigation/navigation.config.ts`، `frontend/src/features/portal/components/PortalIcon.tsx`، `frontend/src/app/layouts/PortalLayout.tsx` و `frontend/src/shared/styles/portals.css`. فایل‌های بررسی: `frontend/tests/t08-counsellor.cjs` و `docs/t08-verification/results.json`؛ گزارش: `docs/T08_COUNSELLOR_PANEL.md`.
- build/typecheck موفق؛ lint صفر خطا و سه هشدار قبلی؛ ۹ گروه T08 و ۲۰ گروه regression T05 موفق. سناریوها با Chromium و پاسخ کنترل‌شده مطابق قرارداد موجود اجرا شدند؛ API زنده، Keycloak و Docker اجرا نشدند. تصاویر مرورگر فقط برای بازرسی داخلی نگه داشته شدند.
- endpoint، dependency، backend، auth، Landing و Login تغییر نکردند. T09 تا T12 شروع نشدند؛ محدودیت پایین فریم T06 تغییری نکرده است. گزارش‌های تاریخی در بسته ورودی نبودند؛ ادعای وجودشان در خروجی نمی‌شود.


## سابقه تحویل T09 — 2026-10-20

- ورودی: `Gradian(20261020-111952).zip`؛ وضعیت: DONE برای پوسته و ناوبری استاد؛ خروجی `Gradian-T09.zip`. قدم بعد T10 با درخواست جدا؛ T06 همچنان BLOCKED_DESIGN است.
- مرجع مشاهده‌شده: `Screenshot (2420).png`، node 4-3475، screenshot 1920×1080؛ فریم x≈466..1431 و y≈292..991 با نسبت حدود 0.754 به 1280×927 نرمال شد. نوار مرورگر و محیط فیگما جزو محصول نیستند. تصویر نتیجه در 1280×927 واقعاً مشاهده و مقایسه شد؛ تصاویر مرورگر برای بازرسی داخلی‌اند و در بسته خروجی نیستند.
- سایدبار 288 و هدر 64 پیکسلی موجود مناسب بودند. فاصله‌های منو، آیکن‌های dashboard/course/classroom/library، نشان تأیید تکمیل پروفایل و alarm شمارش تنظیم شدند. ترتیب و مقصد پنج آیتم از قبل درست بودند. هدر از panel واقعی و خدمات از registry می‌آیند؛ endpoint جدیدی ساخته نشد.
- مرکز خانه خالی؛ هایلایت مرجع به خانه تحمیل نشد و فقط مسیر فعال URL رنگ می‌گیرد. ۸۰٪ و ۱۲۸ روز مرجع داده واقعی نیستند؛ درصد فاقد قرارداد نمایش داده نمی‌شود و شمارش از API می‌آید. SVGها بازسازی ساده‌اند؛ تطابق پیکسلی فونت و asset اصلی ادعا نمی‌شود. رفتار موبایل تصمیم پیاده‌سازی موجود است و مرجع مستقل ندارد.
- فایل‌های محصول: `frontend/src/app/navigation/navigation.config.ts`، `frontend/src/app/layouts/PortalLayout.tsx`، `frontend/src/features/portal/components/PortalIcon.tsx`، `frontend/src/shared/styles/portals.css`.
- فایل‌های بررسی: `frontend/tests/t09-instructor.cjs`، `docs/t09-verification/results.json` و `docs/t05-verification/results.json`؛ گزارش `docs/T09_INSTRUCTOR_PANEL.md`.
- build/typecheck موفق؛ lint صفر خطا و سه warning قبلی providerها؛ ۷ گروه T09 و ۲۰ گروه T05 موفق در Chromium با پاسخ کنترل‌شده مطابق serializerها. نام/نقش/شمارش API، Bearer، نبود درخواست داشبورد دانشجو، ترتیب پنج آیتم، active، refresh، پروفایل، unavailable و موبایل fa/en dark بررسی شدند. API زنده، Docker و Keycloak اجرا نشدند.
- backend، endpointها، auth، Landing/Login، Docker و dependencies پروژه تغییر نکردند. گزارش‌های قدیمی در ورودی نبودند و بازسازی نشده‌اند؛ بخش‌های سابقه فقط سوابق‌اند، وضعیت جاری همین بخش است.


## سابقه تحویل T10 — 2026-10-20

- ورودی `Gradian(20261020-113329).zip`؛ خروجی `Gradian-T10.zip`؛ وضعیت DONE برای پوسته و ناوبری ادمین. قدم بعد T11 با درخواست جدا؛ T06 همچنان BLOCKED_DESIGN است.
- مرجع واقعی `Screenshot (2418).png`، node 20-18، screenshot 1920×1080؛ فریم x≈522..1487 و y≈192..929 با نسبت حدود 0.754 به 1280×978 نرمال شد. نتیجه در همین اندازه واقعاً مشاهده و مقایسه شد. تصاویر مرورگر فقط برای بازرسی داخلی‌اند و بسته‌بندی نمی‌شوند؛ مرجع طراحی اصلی در docs/t10-verification/reference.png حفظ شد.
- سایدبار 288 و هدر 64 پیکسلی موجود مناسب بودند. ارتفاع ردیف لوگو و فاصله‌های منو مختص ادمین تنظیم شدند؛ آیکن مشاوره headset، محصولات library و شمارش alarm از مجموعه SVG موجود انتخاب شدند. سه عنوان و مسیر موجود از قبل درست بودند و حفظ شدند. ردیف پروفایل ندارد و خانه خالی ماند. هایلایت از URL است؛ داده نمونه مرجع به محصول وارد نشد.
- نام/نقش/شمارش از panel و خدمات از registry می‌آیند. قراردادها و بک‌اند تغییر نکردند؛ مدیریت کاربران یا امکانات مالی اضافه نشدند. asset اصلی فونت و آیکن در دسترس نیست و تطابق پیکسلی ادعا نمی‌شود؛ موبایل تصمیم پیاده‌سازی موجود است.
- فایل‌های محصول: `frontend/src/app/layouts/PortalLayout.tsx`، `frontend/src/app/navigation/navigation.config.ts` و `frontend/src/shared/styles/portals.css`. بررسی: `frontend/tests/t10-admin.cjs`، `docs/t10-verification/results.json` و نتایج regression؛ گزارش `docs/T10_ADMIN_PANEL.md`.
- build/typecheck موفق؛ lint صفر خطا و سه warning قبلی؛ ۷ گروه T10، ۲۰ گروه T05 و ۳۹ گروه دسترسی/نشست T04 موفق با Chromium و پاسخ کنترل‌شده مطابق قرارداد. API زنده، Docker و Keycloak اجرا نشدند. dependencies و auth و Landing/Login تغییر نکردند. گزارش‌های تاریخی در ورودی نبودند و بازسازی نشده‌اند.


## تحویل جاری T11 — 2026-10-20

- ورودی `Gradian(20261020-121042).zip`؛ خروجی `Gradian-T11.zip`؛ وضعیت DONE برای یکپارچگی خدمات. T12 شروع نشده؛ T06 همچنان BLOCKED_DESIGN است.
- مرجع قرارداد `registry/models.py`، `serializers.py`، `views.py`، seed و fixture خدمات است. همه ۲۵ نگاشت مسیر به key تأیید شدند. target_url همه ورودی‌های fixture خالی است؛ هیچ پورت، مقصد یا شماره تیم حدس زده نشد. VITE_API_BASE_URL فقط نشانی API هسته است و fallback سرویس نیست.
- redirect: کارت/CTA دانشجو مستقیماً full-page navigation؛ منوی مدیریتی ابتدا مسیر داخلی موجود و سپس دکمه خروجی. embed: کارت/CTA به مسیر محافظت‌شده فعلی می‌رود و ServicePage همان URL registry را در iframe نمایش می‌دهد. دکمه باز کردن جداگانه همیشه برای محدودیت frame/ورود سرویس موجود است.
- iframe دارای عنوان و sandbox است؛ سرویس خارجی allow-same-origin دارد، ولی iframe هم‌مبدأ عمداً آن را ندارد تا همراه اجرای script به والد دسترسی نگیرد. ذخیره‌سازی/ورود سرویس هم‌مبدأ ممکن است نیازمند بازکردن جداگانه باشد. تشخیص قطعی X-Frame-Options/CSP/مجوز داخلی سرویس از والد ممکن نیست؛ نمایش موفق یا SSO ساختگی اعلام نمی‌شود.
- URL فقط absolute HTTP(S) بدون username/password و بدون پارامترهای credential مانند access_token، refresh_token، id_token و token در query/hash پذیرفته می‌شود. token برنامه هیچ‌گاه به URL/iframe/header سرویس افزوده نمی‌شود؛ referrer ارسال نمی‌شود. این اعتبارسنجی مقصد registry است و ادعای کنترل redirectهای بعدی خود سرویس نیست.
- بارگذاری، خطای شبکه/سرور، 403، 401 و unavailable تفکیک شدند؛ خطای refetch مقصد cache شده را دوباره فعال نگه نمی‌دارد. نبود entry «ناموجود» است؛ API وضعیت forbidden مجزا برای هر entry ندارد. 403 فهرست و guard نقش موجود مرجع عدم دسترسی‌اند.
- کد جدید: `api/serviceNavigation.ts` و `components/ServiceLink.tsx`. تغییرات: `panelApi.ts`، `PortalLayout.tsx`، `PortalHome.tsx`، `ServicePage.tsx`، localeهای navigation و CSS محدود به نمایش frame. چیدمان چهار خانه و ترتیب خدمات حفظ شدند.
- بررسی: build/typecheck موفق؛ lint صفر خطا و همان سه warning providerها. ۱۳ گروه T11، ۲۰ گروه T05، ۳۹ گروه T04 و ۷ گروه T10 موفق؛ نتایج در docs هستند؛ گزارش تفصیلی `docs/T11_SERVICE_NAVIGATION.md`. تمام سناریوهای مرورگر با پاسخ کنترل‌شده اجرا شدند؛ API زنده، Docker، Keycloak و SSO سرویس‌های تیم‌ها اجرا نشده‌اند.
- backend، endpoint، dependencies، auth، Landing/Login و Docker تغییر نکردند. گزارش‌های تاریخی نام‌برده‌شده در اسناد که در ورودی نبودند بازسازی نشده‌اند. خروجی شامل کد کامل و هر دو سند است؛ node_modules، dist، cache و تصاویر مرورگر بسته‌بندی نمی‌شوند.
- قدم بعد T12 با درخواست جدا؛ مرجع کامل پایین T06 همچنان لازم است.


## تحویل جاری T12 — 2026-10-20

- ورودی: `Gradian(20261020-122909).zip`؛ خروجی: `Gradian-T12.zip`. هر دو سند پیش از کار خوانده شدند. فقط بررسی نهایی T12 انجام شد؛ کد محصول، endpoint، dependency، CSS، backend و جریان Auth تغییر نکردند.
- وضعیت T12: **BLOCKED_DESIGN برای پذیرش نهایی کامل**؛ بررسی‌های مستقل و تحویل مرحله‌ای انجام شدند. T06 همچنان BLOCKED_DESIGN است؛ پایین فریم دانشجو مرجع کامل ندارد. این وضعیت به معنی شکست build یا smoke test نیست.
- مراجع چهار نقش با نام دقیق بازیابی و واقعاً مشاهده شدند؛ تصاویر اصلی، مقایسه‌های هم‌اندازه و ۳۲ تصویر نتیجه در `docs/t12-verification/` قرار دارند. ادمین 1280×978، استاد 1280×927، مشاور 1280×800 و دانشجو 1280×1978؛ مقایسه دانشجو فقط تا ارتفاع قابل مشاهده حدود 1754 است. تصویر اصلی دانشجو شامل پوشیدگی ابزار فیگما و انتهای نامشخص است.
- `frontend/tests/t12-final.cjs`: ورودی واقعی برنامه، ۴ نقش × ۲ زبان × ۲ تم × ۳ عرض (1280،390،320)؛ ۴۸ حالت موفق. جهت، تم، نبود سرریز، خدمات نقش، نبود سایدبار دانشجو، بوم خالی مدیریتی، اندازه پوسته، drawer/Escape و refresh مسیر خدمات بررسی شدند. ۱۶ ترکیب نقش/زبان/تم، refresh مستقل دارند. این تست از fixture صفحه harness استفاده نمی‌کند؛ فقط پاسخ‌های API intercept می‌شوند.
- اصلاح `frontend/tests/t05-data.cjs`: انتظار پیام unavailable به `.management-service-card` محدود شد تا پیام قدیمی سایدبار باعث خواندن DOM پیش از پایان تغییر مسیر نشود. assertion رفتار محصول حذف یا ضعیف نشد؛ کد محصول نیاز به اصلاح نداشت.
- build شامل `tsc -b` موفق؛ lint صفر خطا و همان سه warning Fast Refresh در providerها. تست‌های T04=39، T05=20، T06=8، T07=22، T08=9، T09=7، T10=7 و T11=13 گروه موفق‌اند. همراه با ۱۶ گروه T12 جمعاً ۱۴۱ گروه (تعداد حالت‌های viewport جداگانه ۴۸)؛ خطای JavaScript مرورگر گزارش نشد.
- ورود/callback چهار نقش، خروج، انقضا، 401/403، اختلال API/retry، خدمات unavailable، redirect/embed، مقصد و cache با قراردادهای واقعی و پاسخ کنترل‌شده بررسی شدند. API زنده، Docker، Keycloak واقعی و SSO بین سرویس‌ها اجرا نشده‌اند. موفقیت این تست‌ها تأیید استقرار نیست.
- تفاوت مجاز با مرجع: نام/شمارش/تعداد feed از داده API می‌آیند؛ درصد پروفایل فاقد قرارداد نمایش داده نمی‌شود؛ active تابع URL است. فونت/آیکن اصلی طراحی موجود نیست و تطابق پیکسلی تأیید نمی‌شود. برای dark/LTR/موبایل طرح مستقلی نداریم و بررسی آن‌ها عملکردی است.
- گزارش کامل و فهرست تغییرات: `docs/T12_FINAL_REVIEW.md`. گام بعدی، دریافت export کامل پایین فریم دانشجو برای نهایی‌سازی T06 و سپس بستن پذیرش بصری T12 است؛ smoke زنده روی محیط کاربر نیز جداگانه لازم است. هیچ تسک تازه‌ای خودکار آغاز نشد.


## تحویل جاری R01 — 2026-10-21

- ورودی: `Gradian-main (2).zip`؛ فقط R01 انجام شد و وضعیت آن DONE است.
- محصول، endpoint، dependency، realm template، theme و داده کاربر تغییر نکردند؛ فقط گزارش و دو سند جاری به‌روز شدند.
- `realm-template.json` و `user-profile.json` با `python3 -m json.tool` parse شدند. `backend/build/realm-gradian.json` و `frontend/node_modules` در archive حاضر نبودند؛ build/lint و محیط زنده اجرا نشدند.
- گزارش baseline: `docs/registration/R01_BASELINE.md`. اختلاف README و کد، قواعد فیلدها، session/PKCE، نقش تازه‌وارد و تفاوت template با realm زنده در آن ثبت شده‌اند.
- R02 همچنان BLOCKED_DESIGN. R03 از نظر وابستگی آماده است، ولی برای password policy تصمیم حداقل ۸ کاراکتر لازم است. R04 نیز مستقل از مانع طراحی قابل انتخاب است. هیچ‌کدام در این سشن شروع نشدند.


## تحویل جاری R03 — 2026-10-21

- ورودی: `Gradian-R01.zip`. کاربر policy حداقل ۸ کاراکتر را تأیید کرد.
- تغییر محصول محدود: `backend/keycloak/realm-template.json`، `backend/keycloak/user-profile.json` و validator نام در `backend/packages/gradian-auth/.../claims.py`. endpoint، PKCE، role mapping، dashboard و session بازنویسی نشدند.
- `passwordPolicy` اکنون `length(8)` است. نام باید حداقل یک Unicode letter/mark داشته باشد؛ space/ZWNJ در کنار نام معتبر مجازند ولی به‌تنهایی معتبر نیستند. mobile/email rules و ممنوعیت edit عمومی subtype حفظ شدند.
- تست مستقل R03 چهار مورد موفق؛ JSON parse، py_compile و sanity check نام موفق. تست کامل Django/Keycloak و self-registration زنده در این محیط اجرا نشدند.
- روش اعمال/rollback بدون حذف volume و backup قبل از تغییر در `docs/registration/R03_IDENTITY_RULES.md` ثبت شده است. `make reset` برای R03 استفاده نشود.
- وضعیت: R03 = IN_PROGRESS (IMPLEMENTED / PENDING_LIVE)، R02 = BLOCKED_DESIGN، R04 = TODO و قابل شروع.

## تحویل جاری R04 — 2026-10-21

- ورودی: `Gradian-R03.zip`. فقط R04 انجام شد؛ R05/R06/R07 شروع نشدند.
- کد محصول: `frontend/src/features/auth/api/authFlow.ts` اضافه شد و `authApi.ts` برای استفاده از helper مشترک تغییر کرد. `beginRegistration()` اکنون endpoint ثبت‌نام را از config واقعی می‌گیرد؛ هیچ URL ثابت localhost، endpoint ساخت حساب Core یا کتابخانه OIDC تازه اضافه نشد.
- validation: issuer باید URL مطلق HTTP(S) بدون credential/query/hash باشد. registration endpoint باید HTTP(S)، بدون credential/query/hash، هم-origin با issuer و دقیقاً مسیر `${issuer}/protocol/openid-connect/registrations` باشد. validation قبل از ذخیره verifier/state و redirect انجام می‌شود.
- PKCE: login و registration هر دو `response_type=code`، `scope=openid`، callback موجود، state تصادفی، verifier تصادفی و `code_challenge_method=S256` دارند. verifier در URL قرار نمی‌گیرد و فقط در sessionStorage موجود ذخیره می‌شود.
- همزمانی/retry: lock مشترک یک شروع در حال اجرا را حفظ می‌کند تا double click/StrictMode جفت PKCE را overwrite نکند. config failure یا endpoint نامعتبر lock را آزاد می‌کند؛ retry بعدی از state/verifier تازه استفاده می‌کند.
- regression: login عادی همچنان `/protocol/openid-connect/auth` را استفاده می‌کند. callback/token exchange/session/role mapping و backend تغییر نکردند. `/register` عمومی و CTA هنوز بخشی از R06 و قالب واقعی فرم بخشی از R05 هستند.
- تست: `frontend/tests/r04-auth-flow.cjs` با source واقعی helper و TypeScript سیستم اجرا شد؛ ۶ گروه سناریو موفق: URL+S256، freshness، dedupe، retry، endpoint ناسازگار و login regression. transpile syntax برای `authFlow.ts` و `authApi.ts` نیز موفق بود. npm dependency install کامل به‌دلیل timeout محیط انجام نشد، بنابراین build کامل frontend در این سشن موفق اعلام نمی‌شود. Keycloak زنده نیز اجرا نشد؛ این تست نمایش واقعی فرم ثبت‌نام را اثبات نمی‌کند.
- وضعیت: R04 = DONE؛ R03 = IN_PROGRESS (IMPLEMENTED / PENDING_LIVE)؛ R02 = BLOCKED_DESIGN.


## تحویل جاری R05 — 2026-10-21

- ورودی: `Gradian-R04.zip`. فقط بخش مستقل و قابل‌پیاده‌سازی R05 انجام شد؛ R06/R07 شروع نشدند.
- theme: `register.ftl` برای عدم بازتاب password، autocomplete، aria/error linking و inputmode اصلاح شد. `login.ftl` لینک ثبت‌نام conditional با `${url.registrationUrl}` دارد و back link ثبت‌نام `${url.loginUrl}` است. `template.ftl` پیام عمومی sanitize‌شده را با live region نمایش می‌دهد؛ CSS focus-visible/footer/mobile پایه را پوشش می‌دهد.
- امنیت: هیچ password در value/log/storage جدید قرار نگرفت؛ هیچ endpoint یا URL ثبت‌نام دستی ساخته نشد؛ `url.registrationAction` و `url.loginAction` حفظ شدند.
- تست مستقل `backend/scripts/tests/test_r05_theme_contract.py` قرارداد source را بررسی می‌کند. رندر FreeMarker/Keycloak زنده، submit واقعی، conflictها و policy runtime هنوز اجرا نشده‌اند.
- طراحی: R02 همچنان BLOCKED_DESIGN است؛ بنابراین password toggle تازه و بازطراحی بصری ثبت‌نام اضافه نشد و screenshot comparison موفق ادعا نمی‌شود.
- وضعیت: R05 = IN_PROGRESS (FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_LIVE)، R03 = IN_PROGRESS (IMPLEMENTED / PENDING_LIVE)، R04 = DONE. گزارش: `docs/registration/R05_KEYCLOAK_FORM.md`.


## تحویل جاری R07 — 2026-10-21

- ورودی: `Gradian-R05.zip`. R06 به‌دلیل R02/BLOCKED_DESIGN شروع نشد؛ بخش مستقل R07 اجرا شد.
- frontend: `gradian.auth.oidc_flow` کنار verifier/state ذخیره می‌شود تا callback بداند retry باید login یا registration باشد. state پیش از اعتماد به provider error بررسی می‌شود؛ callback تکراری/ناقص/mismatch code exchange نمی‌کند و transient PKCE در همه پایان‌ها پاک می‌شود.
- callback UI: session قبلی و React Query cache قبل از verification پاک می‌شوند. 400/401/403/409 و provider outage به حالت‌های `invalid/unauthorized/forbidden/conflict/provider` نگاشت شده‌اند. دکمه retry callback مصرف‌شده را دوباره استفاده نمی‌کند و flow تازه هم‌نوع آغاز می‌کند.
- session: access token ابتدا exchange می‌شود، سپس `/me` خوانده می‌شود، panel معتبر به role فرانت نگاشت می‌شود و فقط بعد از `isUsableSession`، AuthProvider آن را persist می‌کند. token payload ناقص/منقضی نشست نمی‌سازد.
- backend: roleless token همچنان student resolve می‌شود، اما `/me` اکنون پیش از موفقیت `student` را در Keycloak با `ensure_role` idempotent تضمین می‌کند. شکست Admin API دیگر فقط log نمی‌شود؛ 502 `identity_provider_unavailable` می‌دهد و درخواست بعدی حتی با Profile از قبل ساخته‌شده دوباره تلاش می‌کند.
- توکن همان callback ممکن است هنوز claim نقش `student` نداشته باشد؛ Core فقط پس از تضمین role durable اجازه `/me` می‌دهد. برای سرویس‌هایی که نقش را از token می‌خوانند، ورود مجدد/توکن تازه لازم است. refresh flow خودکار یا قرارداد SSO جدید در R07 اضافه نشد.
- تست اجراشده: `frontend/tests/r07-callback.cjs` = 6 گروه موفق؛ regression `frontend/tests/r04-auth-flow.cjs` = 6 گروه موفق؛ `backend/scripts/tests/test_r07_identity_contract.py` = 5 تست موفق؛ `py_compile` فایل‌های تغییرکرده و parse JSONهای Keycloak موفق. تست کامل Django و Keycloak زنده در این محیط اجرا نشد.
- وضعیت: R07 = IN_PROGRESS (IMPLEMENTED / PENDING_LIVE). برای DONE باید روی stack واقعی ثبت‌نام roleless، 502/retry در outage کنترل‌شده، role `student` در Keycloak و claim نقش در token تازه بعد از login مجدد تأیید شوند.

## تحویل جاری R06 — 2026-10-21

- ورودی: `Gradian-R07.zip`. چون R08 به R06 وابسته است، بخش مستقل R06 قبل از R08 تکمیل شد؛ R02 هنوز BLOCKED_DESIGN است.
- frontend: مسیر `/register` زیر PublicLayout و `RegisterPage` اضافه شد. صفحه فقط `authApi.beginRegistration()` از R04 را فراخوانی می‌کند و `/login` حفظ شده است.
- session: فقط `isUsableSession` ثبت‌نام را bypass می‌کند و مقصد، خانه نقش معتبر همان session است؛ نشست منقضی مانع ورود به registration نمی‌شود.
- UX functional: loading/error/retry با promise handling کامل و semantics قابل‌دسترسی اضافه شد. fa/en هر دو کلیدهای transition ثبت‌نام دارند.
- Back: اگر state/verifier/flow ثبت‌نام از تلاش رهاشده باقی باشد، route دوباره auto-redirect نمی‌کند؛ پیام تلاش ناتمام و ادامه با PKCE تازه نشان می‌دهد. retry material قبلی را پاک می‌کند. lock R04 بعد از assign آزاد می‌شود تا bfcache restore به lock دائمی نخورد.
- CTA: LandingPage عمداً تغییر نکرد چون محل/متن CTA نیازمند R02 است. بنابراین R06 = IN_PROGRESS (FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_BROWSER)، نه DONE.
- تست اجراشده: `frontend/tests/r06-public-registration.cjs` = 17 check موفق؛ regression `r04-auth-flow.cjs` = 7 گروه و `r07-callback.cjs` = 6 گروه موفق. مرورگر/Keycloak واقعی اجرا نشده است.
- گزارش: `docs/registration/R06_PUBLIC_ENTRY.md`.


## تحویل جاری R08 — 2026-10-21

- ورودی: `Gradian-R06.zip`. فقط بخش R08 اجرا شد؛ معماری PKCE/role/dashboard و CTA لندینگ بازطراحی نشدند.
- React: `LoginPage` پیام‌های hard-coded فارسی را به i18n منتقل کرد؛ Login/Register/Callback برای pending از status/live-region و برای failure از alert + focus programmatic استفاده می‌کنند. retryها busy/disabled semantics دارند و success قبل از session معتبر نمایش داده نمی‌شود.
- display: auth cardهای React از `text-align:start`، theme variableها، dark error state، wrap متن بلند و guard 360px استفاده می‌کنند. fa/en React حفظ شده‌اند؛ Keycloak فقط fa در scope ادعا می‌شود.
- Keycloak: field errorها به input با aria-invalid/describedby/errormessage وصل‌اند؛ اولین invalid focus می‌گیرد؛ mobile/email در RTL فارسی LTR هستند؛ password value بعد از خطا بازتاب نمی‌شود. general error/status live semantics جدا و پیام‌های فارسی duplicate mobile/email، invalid email، required، mismatch و min-length افزوده شدند.
- تست واقعی اجراشده: `frontend/tests/r08-auth-accessibility.cjs` = 28 check؛ `backend/scripts/tests/test_r08_theme_accessibility.py` = 7 تست؛ regression R04=7 گروه، R06=17 check، R07=6 گروه، R07 backend=5، R05 theme=6، R03 rules=4؛ همه موفق.
- `frontend/node_modules` در archive حاضر نبود، بنابراین npm build/lint و browser matrix اجرا نشده‌اند. Keycloak/realm زنده، submit واقعی duplicate/mismatch/password policy و outage واقعی نیز اجرا نشده‌اند.
- R02 همچنان BLOCKED_DESIGN است؛ screenshot comparison مطابق مرجع ثبت‌نام/CTA ممکن نبود. R08 = IN_PROGRESS (FUNCTIONAL HARDENED / BLOCKED_DESIGN / PENDING_BROWSER_LIVE)، نه DONE.
- گزارش: `docs/registration/R08_ACCESSIBILITY_ERRORS.md`. R09 طبق وابستگی رسمی تا DONE شدن R08 نباید به‌عنوان verification نهایی شروع شود.


## تحویل جاری R09 — 2026-10-21

- ورودی `Gradian-R08.zip`. وابستگی رسمی R09 یعنی R08 هنوز بسته نشده، پس فقط precheck non-live انجام شد؛ R09 DONE نیست.
- هیچ کد محصول/endpoint/dependency/realm data تغییر نکرد. دو تست contract جدید و runner `scripts/r09-registration-preflight.sh` اضافه شدند.
- نتایج واقعی: R04=7 گروه، R06=17 check، R07=6 گروه، R08 frontend=28 check، R09 frontend=22 check؛ R03=4، R05=6، R07 backend=5، R08 backend=7، R09 backend=5 و suite `backend/scripts/tests`=125 تست موفق. parse JSON، py_compile و syntax check موفق.
- npm registry در این محیط با `EAI_AGAIN` در دسترس نبود و cache هم کامل نبود؛ build/lint/typecheck با dependency ناقص پذیرفته نشدند. Playwright نصب نبود و Docker executable وجود نداشت؛ بنابراین browser matrix و ثبت‌نام/Keycloak/Core زنده اجرا نشدند.
- گزارش کامل: `docs/registration/R09_VERIFICATION.md`. وضعیت R09: `IN_PROGRESS (STATIC/CONTRACT PRECHECK COMPLETE / BLOCKED_BY_R08 / PENDING_BUILD_BROWSER_LIVE)`.
