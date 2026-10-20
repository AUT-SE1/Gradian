# زمینه پروژه گرادیان برای سشن جدید

تاریخ: 2026-10-20 — نسخه 1.9 — پس از تکمیل T09

## دستور اصلی به عامل سشن بعد

کاربر می‌خواهد منو و داشبورد دانشجو، مشاور، استاد و ادمین عین طرح‌های فیگمای خودش پیاده شوند. پروژه موجود است؛ از صفر نساز. هر بار فقط یک تسک از `GRADIAN_DASHBOARD_TASKS.md` انجام بده و هر دو سند را در پایان به‌روز کن. T01 تا T05 تکمیل شده‌اند. T06 برای بخش قابل مشاهده اصلاح شد؛ تأیید نهایی پایین فریم BLOCKED_DESIGN است. T07 تا T09 تکمیل شدند. گزارش جاری: `docs/T09_INSTRUCTOR_PANEL.md`. گزارش‌های T01 تا T04 در ورودی این سشن موجود نبودند و مربوط به تحویل‌های قبلی‌اند؛ تست T04 در ورودی موجود بود و دوباره اجرا شد.

برای شروع، آخرین نسخه پروژه و اسناد را بخوان. مسیرهای موقت محیط قبلی پایدار نیستند. اگر فقط این Markdown را داری، به کد و تصاویر واقعی دسترسی نداری و نباید ادعا کنی آن‌ها را دیده‌ای. برای پیاده‌سازی دقیق، آخرین zip/checkout و تصاویر اصلی باید در سشن جدید در دسترس باشند.

## هدف محصول و نقش کاربر

گرادیان یک پورتال خدمات آمادگی آزمون با چهار پنل است. کاربر مسئول فرانت‌اند در پروژه تیمی/TA است؛ بک‌اند و سرویس‌های تیم‌ها موجود یا در حال توسعه‌اند. محتوای فعلی طرح‌ها درباره کنکور سراسری است؛ موضوع و متن محصول را خودسرانه با یک حوزه دیگر جایگزین نکن.

در این مرحله هدف، تکمیل UI، ناوبری، دسترسی و اتصال APIهای آماده است؛ ساخت همه میکروسرویس‌ها در دامنه این درخواست نیست. کاربر در سشن جاری فقط T09 را درخواست کرد؛ پوسته و ناوبری استاد تکمیل شد. T10 و مراحل بعدی شروع نشده‌اند. T06 برای پایین فریم همچنان BLOCKED_DESIGN است؛ این مانع اتصال مستقل T07 نیست.

## منابع بررسی‌شده

- ورودی فعلی: `Gradian(20261020-111952).zip`؛ آخرین کد و هر دو سند ریشه خوانده شدند. تصاویر مرجع و گزارش‌های تاریخی در zip نبودند؛ مرجع استاد `Screenshot (2420).png` با نام دقیق بازیابی و واقعاً مشاهده شد. منابع دیگر زیر سابقه‌اند.
- `Screenshot (2418).png`: مرجع کامل ادمین، node 20-18، اندازه 1280×978؛ مانع فقدان مرجع T10 رفع شد، اما تطبیق آن تسک انجام نشده است.
- `Screenshot (2419).png`: مشاور، node 4-3083، اندازه 1280×800.
- `Screenshot (2420).png`: استاد، node 4-3475، اندازه 1280×927.
- `Screenshot (2421).png`: دانشجو، node 4-2272، اندازه 1280×1978؛ پایین فریم در screenshot کامل نیست.
- طرح موبایل و export اصلی فونت/آیکن موجود نیستند. اندازه‌های پایه T02 همچنان تا تسک تطبیق هر نقش موقت‌اند.
- خروجی فعلی `Gradian-T09.zip` کد کامل آخرین ورودی به همراه تغییرات T09، دو سند، گزارش و تست‌هاست؛ node_modules، dist، cache و تصاویر مرورگر بسته‌بندی نمی‌شوند.

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

مرجع کامل ادمین اکنون `Screenshot (2418).png` با فریم 1280×978 است؛ شامل همان سه آیتم منوی موجود، هدر، شمارش پایین و بوم خالی. دریافت مرجع، تأیید تطابق بصری نهایی نیست؛ T10 هنوز TODO است. هیچ منوی کاربران یا آمار جدیدی از وجود API استنباط نشود. طرح اختصاصی موبایل موجود نیست؛ رفتار responsive فقط تصمیم فنی و آزموده‌شده است.

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
- مرجع کامل ادمین دریافت شد؛ وضعیت T10 به TODO اصلاح شده است؛ T10 اجرا نشده. پایین دانشجو و فونت/آیکن اصلی هنوز ناقص‌اند.
- وضعیت جاری T06: BLOCKED_DESIGN فقط برای تأیید نهایی بخش پوشیده/خارج تصویر. بخش قابل مشاهده بازتنظیم شد؛ گزارش `docs/T06_STUDENT_VISUAL.md`. نهایی‌سازی T06 نیازمند مرجع کامل است. T07 اتصال welcome/streak/feed را انجام داده است؛ T08 و T09 نیز تکمیل شدند و تسک بعدی T10 است.

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


## تحویل جاری T09 — 2026-10-20

- ورودی: `Gradian(20261020-111952).zip`؛ وضعیت: DONE برای پوسته و ناوبری استاد؛ خروجی `Gradian-T09.zip`. قدم بعد T10 با درخواست جدا؛ T06 همچنان BLOCKED_DESIGN است.
- مرجع مشاهده‌شده: `Screenshot (2420).png`، node 4-3475، screenshot 1920×1080؛ فریم x≈466..1431 و y≈292..991 با نسبت حدود 0.754 به 1280×927 نرمال شد. نوار مرورگر و محیط فیگما جزو محصول نیستند. تصویر نتیجه در 1280×927 واقعاً مشاهده و مقایسه شد؛ تصاویر مرورگر برای بازرسی داخلی‌اند و در بسته خروجی نیستند.
- سایدبار 288 و هدر 64 پیکسلی موجود مناسب بودند. فاصله‌های منو، آیکن‌های dashboard/course/classroom/library، نشان تأیید تکمیل پروفایل و alarm شمارش تنظیم شدند. ترتیب و مقصد پنج آیتم از قبل درست بودند. هدر از panel واقعی و خدمات از registry می‌آیند؛ endpoint جدیدی ساخته نشد.
- مرکز خانه خالی؛ هایلایت مرجع به خانه تحمیل نشد و فقط مسیر فعال URL رنگ می‌گیرد. ۸۰٪ و ۱۲۸ روز مرجع داده واقعی نیستند؛ درصد فاقد قرارداد نمایش داده نمی‌شود و شمارش از API می‌آید. SVGها بازسازی ساده‌اند؛ تطابق پیکسلی فونت و asset اصلی ادعا نمی‌شود. رفتار موبایل تصمیم پیاده‌سازی موجود است و مرجع مستقل ندارد.
- فایل‌های محصول: `frontend/src/app/navigation/navigation.config.ts`، `frontend/src/app/layouts/PortalLayout.tsx`، `frontend/src/features/portal/components/PortalIcon.tsx`، `frontend/src/shared/styles/portals.css`.
- فایل‌های بررسی: `frontend/tests/t09-instructor.cjs`، `docs/t09-verification/results.json` و `docs/t05-verification/results.json`؛ گزارش `docs/T09_INSTRUCTOR_PANEL.md`.
- build/typecheck موفق؛ lint صفر خطا و سه warning قبلی providerها؛ ۷ گروه T09 و ۲۰ گروه T05 موفق در Chromium با پاسخ کنترل‌شده مطابق serializerها. نام/نقش/شمارش API، Bearer، نبود درخواست داشبورد دانشجو، ترتیب پنج آیتم، active، refresh، پروفایل، unavailable و موبایل fa/en dark بررسی شدند. API زنده، Docker و Keycloak اجرا نشدند.
- backend، endpointها، auth، Landing/Login، Docker و dependencies پروژه تغییر نکردند. گزارش‌های قدیمی در ورودی نبودند و بازسازی نشده‌اند؛ بخش‌های سابقه فقط سوابق‌اند، وضعیت جاری همین بخش است.
