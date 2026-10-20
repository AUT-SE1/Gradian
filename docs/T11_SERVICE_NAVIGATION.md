# T11 — یکپارچگی لینک خدمات و حالت‌های UI

تاریخ: 2026-10-20
وضعیت: DONE
ورودی: `Gradian(20261020-121042).zip`
خروجی: `Gradian-T11.zip`

## تغییر و علت

کد پیشین mode=embed را نادیده می‌گرفت و در تمام حالت‌ها لینک خروجی می‌ساخت؛ خطای دسترسی/بارگذاری منو نیز زیر برچسب ناموجود پنهان بود. اکنون رفتار از mode و URL معتبر registry می‌آید و وضعیت خطا از unavailable جداست. هیچ endpoint یا مقصد/پورت جدیدی ساخته نشده است.

- redirect کارت و CTA دانشجو: anchor و full-page navigation به همان URL registry؛ حتی مقصد هم‌مبدأ هم route React فرض نمی‌شود.
- embed کارت و CTA دانشجو: Link به همان مسیر محافظت‌شده موجود؛ ServicePage سرویس را در محتوای صفحه بارگذاری می‌کند.
- منوی مدیریتی برای هر دو mode ابتدا به ServicePage فعلی می‌رود؛ مقصد خارجی از دکمه باز کردن سرویس قابل دسترسی است و embed در محتوا نمایش داده می‌شود.
- حالت Connected در صفحه خدمات یعنی ثبت مقصد معتبر در registry؛ این نشانگر health check سرویس نیست.
- loading، خطای سرور/شبکه، forbidden و unavailable متن مجزا دارند؛ خطا با retry فعلی قابل بازیابی است. 401 طبق رفتار موجود نشست را پاک می‌کند. در خطای refetch، لینک و frame قدیمی غیرفعال می‌شوند.
- API وضعیت forbidden برای یک entry ندارد؛ 403 فهرست، و guard نقش موجود مبنای عدم دسترسی‌اند. entry غایب را «ناموجود» نشان می‌دهیم و مجوزی اختراع نمی‌کنیم. مجوز داخلی میکروسرویس در همان سرویس بررسی می‌شود.
- URL مطلق HTTP(S)، فاقد userinfo و پارامترهای token پذیرفته می‌شود. query/hash عادی حفظ می‌شوند. accessToken نشست هرگز به URL یا header سرویس منتقل نمی‌شود؛ referrerPolicy=no-referrer است.
- iframe با title و sandbox ساخته می‌شود. اجازه same-origin فقط برای مقصد خارجی است؛ برای مقصد هم‌مبدأ همراه script فعال نمی‌شود. محدودیت storage یا سیاست CSP/X-Frame-Options و ورود سرویس ممکن است نمایش داخل frame را محدود کند؛ متن روشن و دکمه بازکردن جداگانه موجود است. load iframe به‌عنوان اثبات موفقیت کسب‌وکار یا SSO استفاده نمی‌شود.

## مرجع و دامنه بصری

مرجع این تسک قرارداد واقعی registry و آخرین کد T10 است. تصاویر فیگما در zip ورودی نبودند؛ چهار خانه، ترتیب و عنوان کارت‌ها، sidebar و header بازطراحی نشدند. تنها CSS تازه برای قاب محتواست. تطابق پیکسلی تازه یا نهایی شدن T06 ادعا نمی‌شود؛ T12 انجام نشده است.

## منبع مقصد و شماره تیم

`backend/core/registry/{models,serializers,views}.py` قرارداد status، mode و URL را تعیین می‌کند. `backend/seed/content/services.yaml` و fixture زیر نگاشت قطعی را تأیید کردند. هر ۲۵ target_url در fixture خالی و mode پیش‌فرض redirect است؛ availability واقعی فقط پاسخ API در محیط کاربر است. `VITE_API_BASE_URL` مقصد API هسته است و fallback خدمات نیست. شماره گروه هیچ‌گاه به پورت تبدیل نشده است.

| key | owner_group در fixture | target_url ورودی |
| --- | --- | --- |
| student.simulated-exam | 1 | خالی |
| student.topic-exam | 2 | خالی |
| student.final-exam-12th | 3 | خالی |
| student.major-selection | 9 | خالی |
| student.top-ranker-experiences | 10 | خالی |
| student.courses | 8 | خالی |
| student.private-class | 4 | خالی |
| student.marketplace | 6 | خالی |
| student.counseling-planning | 5 | خالی |
| student.experience-exchange | 10 | خالی |
| consultant.profile | 10 | خالی |
| consultant.student-reports | 7 | خالی |
| consultant.add-experiences | 10 | خالی |
| consultant.resolve-problems | 8 | خالی |
| consultant.counseling-sessions | 5 | خالی |
| consultant.resources-hub | 6 | خالی |
| professor.profile | 10 | خالی |
| professor.progress-dashboard | 7 | خالی |
| professor.exam-question-management | 8 | خالی |
| professor.create-course | 10 | خالی |
| professor.private-class | 4 | خالی |
| professor.resources-hub | 6 | خالی |
| admin.exam-bank | 2 | خالی |
| admin.counseling-sessions | 5 | خالی |
| admin.store-management | 6 | خالی |

## معیار پذیرش

- وضعیت متصل/ناموجود/عدم دسترسی: از URL/status و خطای واقعی API؛ متن‌ها fa/en، بدون fallback نمونه.
- رفتار دکمه‌ها: redirect خروج کامل، embed مسیر داخلی و iframe، بازکردن جداگانه، back و retry موجود.
- mode: تغییر آن با refetch، frame را ایجاد/حذف می‌کند؛ refresh مسیر embed معتبر است.
- بدون accessToken در query: هیچ الحاق token وجود ندارد؛ URLهای دارای پارامترهای credential شناخته‌شده نیز فعال نمی‌شوند. هدایت‌های بعدی و health/مجوز خود سرویس در قرارداد این API نیستند.

## فایل‌های تغییرکرده

- `frontend/src/features/portal/api/panelApi.ts`
- `frontend/src/features/portal/api/serviceNavigation.ts` (جدید)
- `frontend/src/features/portal/components/ServiceLink.tsx` (جدید)
- `frontend/src/features/portal/components/PortalHome.tsx`
- `frontend/src/features/portal/components/ServicePage.tsx`
- `frontend/src/app/layouts/PortalLayout.tsx`
- `frontend/src/shared/styles/portals.css`
- `frontend/src/locales/fa/navigation.json` و `en/navigation.json`
- `frontend/tests/t11-services.cjs` و `docs/t11-verification/results.json`
- دو سند ریشه و همین گزارش؛ نتایج regression اجراشده در docs.

## بررسی

- `npm run build`: موفق، شامل tsc -b.
- `npm run lint`: صفر خطا؛ همان سه warning قبلی Fast Refresh در AuthProvider/I18nProvider/ThemeProvider.
- تست T11: ۱۳ گروه موفق؛ redirect/embed چهار نقش، iframe واقعی با پاسخ کنترل‌شده، fallback، تغییر mode، refresh، کارت و CTA، full-page navigation بدون Bearer/referrer، URLهای نامعتبر و token، تطبیق ۲۵ key، 403/500 و retry، entry غایب، loading و پاک شدن مقصد cached در 403.
- regression T05: ۲۰ گروه موفق؛ loading/error/empty، داده نقش‌ها، اعلان، pagination، 401، mobile dark/LTR و logout.
- regression T10: ۷ گروه موفق؛ هندسه 1280×978، ترتیب منو، ناوبری/refresh و drawer فارسی/انگلیسی تیره. تصویر رندر داخلی مشاهده شد؛ مرجع فیگمای تازه در ورودی وجود ندارد.
- regression T04: ۳۹ گروه موفق؛ guard چهار نقش، نشست، 401/403، alias، expiry، logout/cache و PKCE.
- سناریوها با Playwright/Chromium و پاسخ‌های کنترل‌شده مطابق serializer اجرا شدند؛ بک‌اند زنده، Docker، Keycloak، health و SSO سرویس‌های تیم‌ها اجرا نشده‌اند. تصاویر مرورگر فقط برای بررسی داخلی‌اند و در تحویل ذخیره نشده‌اند.

## باقی‌مانده

T12 با درخواست جدا؛ T06 همچنان برای پایین مرجع BLOCKED_DESIGN است. هر تیم باید target_url و mode صحیح خودش را در registry ثبت کند؛ قرارداد فعلی به فرانت اجازه ساخت SSO یا حدس مقصد را نمی‌دهد. backend، auth، dependencies، Landing/Login و Docker تغییر نکرده‌اند.
