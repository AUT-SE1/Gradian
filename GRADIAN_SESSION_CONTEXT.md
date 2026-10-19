# زمینه پروژه گرادیان برای سشن جدید

تاریخ: 2026-10-19 — نسخه 1.4 — پس از T04

## دستور اصلی به عامل سشن بعد

کاربر می‌خواهد منو و داشبورد دانشجو، مشاور، استاد و ادمین عین طرح‌های فیگمای خودش پیاده شوند. پروژه موجود است؛ از صفر نساز. هر بار فقط یک تسک از `GRADIAN_DASHBOARD_TASKS.md` انجام بده و هر دو سند را در پایان به‌روز کن. T01 تا T04 تکمیل شده‌اند. قدم بعد فقط T05 است. گزارش جاری: `docs/T04_ACCESS_SESSION.md`. گزارش‌های قبلی در zip نسخه 10 موجود نبودند و مربوط به تحویل‌های قبلی‌اند.

برای شروع، آخرین نسخه پروژه و اسناد را بخوان. مسیرهای موقت محیط قبلی پایدار نیستند. اگر فقط این Markdown را داری، به کد و تصاویر واقعی دسترسی نداری و نباید ادعا کنی آن‌ها را دیده‌ای. برای پیاده‌سازی دقیق، آخرین zip/checkout و تصاویر اصلی باید در سشن جدید در دسترس باشند.

## هدف محصول و نقش کاربر

گرادیان یک پورتال خدمات آمادگی آزمون با چهار پنل است. کاربر مسئول فرانت‌اند در پروژه تیمی/TA است؛ بک‌اند و سرویس‌های تیم‌ها موجود یا در حال توسعه‌اند. محتوای فعلی طرح‌ها درباره کنکور سراسری است؛ موضوع و متن محصول را خودسرانه با یک حوزه دیگر جایگزین نکن.

در این مرحله هدف، تکمیل UI، ناوبری، دسترسی و اتصال APIهای آماده است؛ ساخت همه میکروسرویس‌ها در دامنه این درخواست نیست. کاربر در این سشن فقط T04 را درخواست کرده؛ T05 و مراحل بعدی شروع نشده‌اند.

## منابع بررسی‌شده

- ورودی این سشن: `Gradian(10).zip`؛ شامل T01 تا T03. HEAD آرشیو `e8d9e44` به‌تنهایی معرف همه تغییرات فایل‌ها نیست؛ مقایسه بایت‌ها با zip مبنای تغییرات T04 است.
- دانشجو: `image(20261019-083655).png`، 1280×1978؛ انتهای صفحه ناقص.
- استاد: `image(20261019-083700).png` و `image(20261019-083704).png`؛ هر دو node 4-3475، ارتفاع 927؛ عرض مبنای برنامه 1280 ولی W کامل در پنل screenshot خوانا نیست.
- مشاور: `image(20261019-083705).png`، 1280×800.
- طرح کامل ادمین، موبایل، export اصلی فونت و آیکن موجود نیستند. اسناد قدیمی درباره وجود exportها به معنی در دسترس بودن آن‌ها در این ورودی نیست.
- آخرین خروجی `Gradian-T04-update.zip` فقط تغییرات T04 روی Gradian(10) است؛ فایل‌های مشابه قدیمی با پسوند (1) جای سند canonical جدید خوانده نشوند.

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
- `src/app/layouts/PortalHeaderActions.tsx`: هدر مشترک چهار نقش و dialog اعلان با وضعیت unavailable تا T05.
- `src/app/hooks/useMobileSidebar.ts`: breakpoint، inert، تمرکز، Escape/Tab، resize، اسکرول و بستن روی تغییر مسیر.
- `src/app/layouts/PublicLayout.tsx`: بخش عمومی؛ با تغییر داشبورد بی‌دلیل دست‌کاری نشود.
- `src/app/navigation/navigation.config.ts`: NavigationItem، گروه‌بندی و مقصد منوهای نقش‌ها.
- `src/app/providers/AuthProvider.tsx`: نشست، انقضای زنده، storage event و پاک‌سازی کش خروج/تغییر هویت.
- `src/shared/auth/session.ts`: runtime validation نقش/ساختار/انقضا؛ expiresAt ضروری است.
- `src/shared/auth/authEvents.ts`: 401 با token اولیه درخواست؛ پاسخ قدیمی نشست جدید را باطل نمی‌کند.
- `src/shared/api/queryClient.ts`: factory مشترک QueryClient؛ بدون retry روی 401/403.
- `src/features/auth/api/authApi.ts`: دریافت پیکربندی Auth، PKCE، callback، دریافت /me و logout.
- `src/features/auth/pages/LoginPage.tsx` و `AuthCallbackPage.tsx`: ورود و callback.
- `src/features/portal/pages/PortalHomePage.tsx` و `components/PortalHome.tsx`: خانه هر نقش؛ دانشجو محتوا دارد، سه نقش دیگر بوم خالی دارند.
- `src/features/portal/config/portalContent.ts`: داده و مقصد کارت‌های داشبورد.
- `src/features/portal/components/ServicePage.tsx`: معرفی/ورود به سرویس؛ اجرای کامل سرویس نیست.
- `src/features/portal/components/PortalIcon.tsx`: مجموعه آیکن موجود.
- `src/shared/api/httpClient.ts` و `ApiError.ts`: درخواست و خطا؛ header Authorization به‌صورت سراسری خودکار به همه درخواست‌ها افزوده نمی‌شود.
- `src/shared/types/auth.ts` و `portal.ts`: نوع نشست و نقش‌ها.
- `src/shared/styles/globals.css`: قواعد عمومی، Landing و Login.
- `src/shared/styles/portals.css`: از T02 قواعد پنل‌ها و responsive، فونت محلی و توکن‌های scoped؛ بعد از globals در main import می‌شود.
- `src/assets/fonts/`: سه subset Vazirmatn variable و مجوز OFL؛ نام font-face پنل Gradian Portal است.
- `src/locales/fa/` و `src/locales/en/`: namespaceهای auth، common، navigation و portal.
- `vite.config.ts`: alias برابر `@ → src`؛ proxy مسیر `/api` به بک‌اند.

## وضعیت واقعی منو و داشبوردها

منو حذف نشده است. PortalLayout برای `instructor`، `counsellor` و `admin` سایدبار می‌سازد و منو از navigation.config می‌آید. برای student یک شاخه مجزا فقط با هدر و محتوا وجود دارد. در تصویر مرجع دانشجو هم سایدبار داخل فریم انتخاب‌شده دیده نمی‌شود؛ منوی دانشجو نباید صرفاً از روی حدس افزوده شود.

داشبورد دانشجو کارت خوشامدگویی، streak و countdown ثابت، ۹ کارت خدمات، سه پست نمایشی و تب‌های غیرتعاملی دارد. برخی اسم‌ها و متن‌ها از ترجمه ولی داده‌ها ثابت‌اند. PortalHome برای نقش‌های مدیریتی فقط بوم خالی رندر می‌کند؛ این با فریم‌های خالی مشاور و استاد سازگار است، ولی عملکرد سرویس‌های زیرمنو هنوز پیاده‌سازی کامل محسوب نمی‌شود.

شماره پورت خدمات در router و portalContent پراکنده است. URLها باید با registry واقعی تطبیق داده شوند؛ عنوان کارت دلیل کافی برای انتخاب شماره تیم نیست. ServicePage عمدتاً صفحه توضیح و لینک ورود است.

از T03 هدر نام نشست را دارد و fallback فقط کاربر/User است؛ نام نمونه و رشته ثابت هدر حذف شدند. عدد 80٪ پروفایل و 128 روز سایدبار حذف شده‌اند. لینک تکمیل پروفایل پابرجاست؛ شمارش معکوس پیام unavailable دارد و اعلان پنجره قابل بستن با پیام unavailable باز می‌کند. نقطه unread همیشگی حذف شد. اتصال نام تازه/رشته/avatar/countdown/consultant_type و اعلان‌های واقعی با حالت‌های داده هنوز T05 است؛ درصد بدون قرارداد محاسبه نشود.

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

ارتفاع 927 و عرض مبنای برنامه 1280 (W کامل در تصویر جدید خوانا نیست)، سایدبار راست با تکمیل پروفایل و منوی گروه‌بندی‌شده، شمارش معکوس پایین، هدر نام/نقش و اعلان/خروج، بوم مرکزی خالی. دو عکس این مجموعه همین فریم را نشان می‌دهند. عرض و فاصله واقعی را از فریم استخراج کن؛ scale نمایش مرورگر را به عنوان px نهایی استفاده نکن.

### مشاور

فریم 1280×800، سایدبار راست و منوی مشاور، هدر مشابه، شمارش معکوس پایین و بوم مرکزی خالی. مقایسه با استاد نباید ارتفاع متفاوت فریم را از بین ببرد.

### ادمین و موبایل

طرح کامل ادمین و طرح اختصاصی موبایل در فایل‌های فعلی نیستند. پنل باریک مجاور در screenshot جایگزین مرجع کامل ادمین نیست. کار مستقل دسترسی و بررسی کد ادمین قابل انجام است؛ تأیید تطابق بصری آن تا دریافت مرجع مسدود است. برای رفتار موبایل تصمیم فنی مستند بگیر و ادعای تطابق با فیگمای موبایل نکن.

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

- T01: DONE در 2026-10-19، روی Gradian(8).zip؛ شناسایی منو، مسیرها، منابع و مغایرت‌ها انجام شد.
- build اولیه و نهایی موفق؛ lint اولیه exit 2 به دلیل نبود config؛ پس از اصلاح exit 0 با 3 warning و بدون error؛ typecheck واقعی موفق.
- در T01 فایل eslint.config.js و script typecheck اصلاح شدند. در T02 استایل پنل از globals به portals.css منتقل و فونت محلی اضافه شد؛ main.tsx فقط import جدید دارد. در T02 router، PortalLayout، API و auth تغییر نکردند؛ در T03 PortalLayout و اجزای پوسته تغییر کردند و خود router/AuthProvider/authApi دست‌نخورده‌اند.
- فایل‌های مستند: همین سند، GRADIAN_DASHBOARD_TASKS.md، گزارش‌های T01/T02 و تصاویر t02-visuals. بسته جدید Gradian-T04-update.zip تغییرات T04 روی Gradian(10) است؛ شامل گزارش، نتیجه بررسی و تست‌های قابل اجرای T04 نیز هست.
- هشدارهای lint موجود: react-refresh/only-export-components در سه provider. برای پاک‌شدن هشدارها providerها بی‌دلیل بازنویسی نشوند.
- در T01 مرورگر اجرا نشد؛ در T02 بررسی بصری مرورگر، موبایل، dark و LTR با داده آزمایشی انجام شد؛ Keycloak و API زنده همچنان تأیید نشده‌اند.
- T02: DONE؛ فونت محلی، رنگ #F7F9FB، هدر دانشجو 80 و مدیریتی 64، سایدبار 288 و gutter برابر 24؛ همه جز رنگ پس‌زمینه تصمیم موقت‌اند. جزئیات در گزارش T02.
- تصاویر و metrics: docs/t02-visuals؛ 14 حالت مرورگر با داده آزمایشی و شبکه کنترل‌شده، بدون overflow؛ بارگذاری محلی فونت و پنج وزن تأیید شد؛ تصاویر Landing/Login فارسی روشن 1280 قبل/بعد یکسان‌اند.
- آخرین build موفق؛ lint صفر خطا و سه هشدار قبلی. تست auth/API واقعی انجام نشده است.
- T03: DONE؛ منو و پوسته تکمیل، focus/inert/Tab/Escape/resize و اعلان unavailable، حذف داده نمونه پوسته، خروج بدون ورود خودکار تازه؛ 19 گروه سناریوی مرورگر موفق. جزئیات و محدودیت‌ها در docs/T03_PORTAL_SHELL.md.
- T04: DONE؛ runtime validation نشست/نقش، انقضا، cache، تب‌ها، 401/403 و aliasها اصلاح شدند. 39 گروه T04 و 19 گروه regression T03، build و lint موفق.
- 401 با token جاری نشست/کش را پاک می‌کند؛ 403 و 401 قدیمی/بدون Bearer حساب جدید را خارج نمی‌کنند. caller همچنان ApiError می‌گیرد؛ UI خطای هر سرویس در T05 لازم است.
- خروج/تغییر id یا نقش، queryهای در حال اجرا را cancel و هر دو cache را پاک می‌کند؛ چرخش token همان هویت کش را نگه می‌دارد. کلید query با user/role در T05 همچنان لازم است.
- اتصال واقعی panel/services/notifications و Bearer خودکار هنوز انجام نشده و موضوع T05 است.
- تسک بعدی فقط T05؛ T05 تا T12 شروع نشده‌اند و T10 همچنان BLOCKED_DESIGN است.
- منبع مفقود: طرح کامل ادمین، پایین دانشجو و فایل اصلی font/assets. نبود آن‌ها مانع تکمیل خط مبنا نیست.

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
