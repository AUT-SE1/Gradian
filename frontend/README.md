# Gradian Frontend

React 19 + TypeScript + Vite. قرارداد اتصال: [راهنمای بک‌اند](../backend/docs/05-frontend-guide.md).

## اجرا

ابتدا بک‌اند را با `make start` در پوشه `backend` اجرا کنید. سپس:

```powershell
cd frontend
npm ci
npm run dev
```

آدرس فرانت باید با `FRONTEND_URL` بک‌اند یکسان باشد (پیش‌فرض `http://localhost:5173`). اگر آن را تغییر می‌دهید، طبق راهنمای بک‌اند realm را با `make reset` بازسازی کنید؛ این فرمان داده‌های محیط توسعه را بازنشانی می‌کند.

`frontend/.env` و `.env.example` از `VITE_API_BASE_URL=/api/v1` استفاده می‌کنند. اجرای محلی با Vite به `http://localhost:8000` proxy می‌شود. در Docker، `docker compose up --build` از شبکه مشترک `gradian` و `http://core:8000` استفاده می‌کند. بعد از تغییر وابستگی‌ها کانتینر را rebuild کنید.

## ورود و دسترسی

- ورود و ثبت‌نام روی صفحات Keycloak با Authorization Code + PKCE انجام می‌شود. فرم ارسال رمز یا endpoint ورود در React وجود ندارد.
- تنظیمات از `/api/v1/auth/config` دریافت می‌شود؛ callback دقیقاً `/auth/callback` است.
- `/me` منبع نام، نقش، `panel` و `home_path` است. هدایت پس از ورود بر اساس `home_path` است.
- مسیرهای `/student`، `/consultant`، `/professor` و `/admin` محافظت شده‌اند. هر حساب فقط پنل خودش را می‌بیند؛ admin دسترسی ضمنی به پنل دانش‌آموز ندارد.
- مسیرهای قدیمی `/instructor` و `/counsellor` به مسیر جدید هدایت می‌شوند و همان کنترل دسترسی را دارند.
- نشست پس از refresh بازیابی می‌شود. OIDC تمدید خودکار دارد؛ درخواست 401 فقط یک بار تمدید و تکرار می‌شود. شکست تمدید به صفحه ورود می‌برد. 403 حالت عدم دسترسی است، نه ورود مجدد.
- خروج، نشست Keycloak را پایان می‌دهد. داده‌های cache پس از خروج یا تغییر هویت/نقش پاک می‌شوند.
- نقش‌ها همچنان در بک‌اند کنترل می‌شوند؛ guard فرانت برای کنترل صفحه و تجربه کاربری است.

## درخواست‌ها

`httpClient` برای مسیرهای عمومی `/landing` و `/auth/config` است. برای درخواست محافظت‌شده از `api` در `shared/api/authedClient.ts` استفاده کنید؛ خودش Bearer token جاری را اضافه می‌کند.

`authApi.me()` و `authApi.updateProfile()` قرارداد `/me` را دارند. تغییر پروفایل از `useAuth().updateProfile()` انجام شود تا پاسخ سرور جایگزین state شود.

`portalApi` مسیرهای `/panel`، `/panel/services`، `/student/dashboard` و `/notifications` را پوشش می‌دهد. پاسخ‌های لیستی از `results` خوانده می‌شوند. داشبورد دانش‌آموز برای نقش‌های دیگر درخواست نمی‌شود.

سرویس فعال با آدرس HTTP/HTTPS باز می‌شود؛ توکن وارد URL نمی‌شود. سرویس غیرفعال لینک ندارد و `embed` طبق قرارداد فعلی همان redirect است. گروه مقصد مسئول SSO خود است. اعلان‌ها فقط نمایش داده می‌شوند؛ endpoint خوانده‌شدن هنوز وجود ندارد.

متن‌های محلی در i18n فارسی/انگلیسی هستند. محتوای دمو که بک‌اند فارسی برمی‌گرداند همان‌طور نمایش داده می‌شود.

## بررسی

```powershell
npm run build
npm run lint
npm test
```

آزمون‌ها کنترل پنل، ارسال Bearer، 401/403، تمدید، callback و لینک سرویس را با mock پوشش می‌دهند. تست واقعی ورود نیاز به Core و Keycloak روشن دارد. با کاربران ساخته‌شده توسط `make users` هر چهار نقش، refresh، خروج و آدرس مستقیم پنل نقش دیگر را بررسی کنید. رمزها را از `backend/build/credentials/users.csv` بردارید.

## Production

```powershell
docker compose -f docker-compose.prod.yml up --build
```

Nginx مسیر `/api/` را روی شبکه `gradian` به Core proxy می‌کند و مسیرهای React را به `index.html` برمی‌گرداند. پیش‌فرض `VITE_API_BASE_URL=/api/v1` است. برای Core جداگانه می‌توانید URL مطلق را در زمان build بدهید؛ CORS بک‌اند و `FRONTEND_URL` باید با origin فرانت یکسان باشد. برای پورت پیش‌فرض تولیدی `8081` نیز نشانی callback باید در Keycloak ثبت باشد.

اجرای standalone کانتینر با proxy نیاز به `--network gradian` دارد.
