# تغییرات اتصال فرانت به بک‌اند

تغییرات بر اساس قرارداد backend/docs/05-frontend-guide.md و endpointهای موجود انجام شده‌اند. کد بک‌اند تغییر نکرده است.

- ورود/ثبت‌نام Keycloak با PKCE و callback در /auth/callback؛ فرم ورود به endpoint ناموجود حذف شد.
- نقش و هدایت پنل از /me؛ guard برای چهار نقش و alias برای مسیرهای قدیمی.
- بازیابی نشست، تمدید توکن، تکرار محدود 401، نمایش جداگانه 403 و خروج از Keycloak.
- درخواست‌های محافظت‌شده با Bearer و محتوای /landing، /panel، /panel/services، /student/dashboard و /notifications.
- نمایش غیرفعال سرویس‌های آماده‌نشده؛ redirect بدون افزودن توکن به URL.
- هماهنگی .env، Docker و proxy تولیدی با /api/v1.
- متن‌های محلی فارسی و انگلیسی، نمایش محتوای برگشتی سرور، و حالات loading/error/empty.

## استفاده از تغییرات

پوشه frontend این نسخه را در پروژه خود جایگزین/ادغام کنید. backend و فایل‌های git نیازی به جایگزینی ندارند. سپس در frontend:

```powershell
npm ci
npm run dev
```

برای Docker فرانت، کانتینر را با `docker compose up --build` بازسازی کنید.

بک‌اند و Keycloak باید روشن باشند و FRONTEND_URL با آدرس مرورگر فرانت یکسان باشد؛ پیش‌فرض localhost:5173 است. رمزهای آزمایشی را از خروجی make users بخوانید. جزئیات در README.md است.

## اعتبارسنجی

Build، lint و 25 آزمون موفق‌اند. آزمون‌ها از mock استفاده می‌کنند؛ ورود واقعی در این محیط اجرا نشده است. برای بررسی واقعی با یک حساب از هر نقش وارد شوید، refresh بزنید، آدرس پنل نقش دیگر را باز کنید و خروج را امتحان کنید.

## فایل‌های تغییرکرده و افزوده‌شده

| فایل | وضعیت |
| --- | --- |
| `frontend/.env` | اصلاح |
| `frontend/.env.example` | اصلاح |
| `frontend/Dockerfile` | اصلاح |
| `frontend/GRADIAN_FRONTEND_PROJECT_GUIDE.md` | اصلاح |
| `frontend/README.md` | اصلاح |
| `frontend/docker-compose.prod.yml` | اصلاح |
| `frontend/docker-compose.yml` | اصلاح |
| `frontend/eslint.config.js` | افزوده |
| `frontend/nginx.conf` | اصلاح |
| `frontend/package-lock.json` | اصلاح |
| `frontend/package.json` | اصلاح |
| `frontend/src/app/layouts/PortalLayout.tsx` | اصلاح |
| `frontend/src/app/providers/AuthProvider.tsx` | اصلاح |
| `frontend/src/app/router/AppRouter.tsx` | اصلاح |
| `frontend/src/features/auth/api/authApi.ts` | اصلاح |
| `frontend/src/features/auth/oidc.ts` | افزوده |
| `frontend/src/features/auth/pages/AuthCallbackPage.tsx` | افزوده |
| `frontend/src/features/auth/pages/LoginPage.tsx` | اصلاح |
| `frontend/src/features/landing/pages/LandingPage.tsx` | اصلاح |
| `frontend/src/features/portal/api/portalApi.ts` | افزوده |
| `frontend/src/features/portal/pages/PortalHomePage.tsx` | اصلاح |
| `frontend/src/locales/en/common.json` | اصلاح |
| `frontend/src/locales/en/navigation.json` | اصلاح |
| `frontend/src/locales/fa/common.json` | اصلاح |
| `frontend/src/locales/fa/navigation.json` | اصلاح |
| `frontend/src/shared/api/QueryState.tsx` | افزوده |
| `frontend/src/shared/api/authedClient.ts` | افزوده |
| `frontend/src/shared/api/httpClient.ts` | اصلاح |
| `frontend/src/shared/styles/globals.css` | اصلاح |
| `frontend/src/shared/types/auth.ts` | اصلاح |
| `frontend/src/shared/types/content.ts` | افزوده |
| `frontend/src/shared/types/portal.ts` | اصلاح |
| `frontend/tests/api.test.ts` | افزوده |
| `frontend/tests/oidc.test.ts` | افزوده |
| `frontend/tests/provider.test.tsx` | افزوده |
| `frontend/tests/routes.test.tsx` | افزوده |
| `frontend/tests/services.test.ts` | افزوده |
| `frontend/tests/setup.ts` | افزوده |
| `frontend/vitest.config.ts` | افزوده |
| `frontend/INTEGRATION_CHANGES.md` | افزوده |
