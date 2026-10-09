# Gradian Frontend

فرانت‌اند پروژه‌ی Gradian با **React 19، TypeScript، Vite و React Router** ساخته شده است. این پوشه در کنار بک‌اند Django قرار دارد و اجرای توسعه‌ی هر دو سرویس به‌وسیله‌ی Compose ریشه انجام می‌شود.

## شروع سریع

از پوشه‌ی ریشه‌ی پروژه (`Gradian/`) اجرا کنید:

```powershell
Copy-Item .env.example .env
# مقادیر رمز و پورت‌ها را در .env بررسی کنید
docker compose up --build
```

آدرس‌های محلی:

| سرویس | آدرس |
|---|---|
| Frontend/Vite | http://localhost:5173 |
| Django backend | http://localhost:8000 |
| Keycloak | http://localhost:8080 |

برای اجرای پس‌زمینه:

```powershell
docker compose up -d --build
```

برای توقف:

```powershell
docker compose down
```

Compose ریشه شبکه‌ی پروژه را خودش می‌سازد؛ اجرای دستی `docker network create gradian` لازم نیست. اگر شبکه‌ی قدیمی را قبلاً دستی ساخته‌اید و پیام label گرفتید، یک‌بار این کار را انجام دهید:

```powershell
docker compose down --remove-orphans
docker network rm gradian
docker compose up --build
```

## اجرای بدون Docker

```powershell
cd frontend
npm ci
npm run dev
```

فایل `frontend/.env` در صورت نیاز از روی نمونه ساخته می‌شود:

```powershell
Copy-Item .env.example .env
```

در توسعه، کلاینت از مسیر `/api` استفاده می‌کند و Vite آن را به `backend:8000` داخل شبکه‌ی Compose proxy می‌کند. بنابراین URL بک‌اند را در Featureها hard-code نکنید.

## اسکریپت‌ها

| فرمان | کاربرد |
|---|---|
| `npm run dev` | اجرای Vite development server |
| `npm run build` | typecheck و production build |
| `npm run typecheck` | بررسی TypeScript |
| `npm run lint` | بررسی ESLint |
| `npm run preview` | نمایش build تولیدی با Vite |

## ساختار فعلی

```text
frontend/
├── src/
│   ├── app/                 # App، providerها، router و layoutها
│   ├── features/            # قابلیت‌های مستقل مثل auth و portal
│   ├── locales/             # ترجمه‌های fa و en
│   ├── shared/              # API client، typeها، style و ابزار مشترک
│   ├── main.tsx
│   └── ...
├── Dockerfile               # production: build با Node و serve با Nginx
├── Dockerfile.dev           # development: Vite داخل کانتینر
├── nginx.conf               # SPA fallback و health endpoint
├── vite.config.ts
├── package.json
├── package-lock.json
├── .env.example
├── .gitignore
└── GRADIAN_FRONTEND_PROJECT_GUIDE.md
```

قابلیت جدید باید تا حد امکان در `src/features/<feature-name>/` قرار بگیرد. کد عمومی که به یک feature وابسته نیست در `src/shared/` قرار می‌گیرد. تغییرات سراسری router، provider، token و Docker باید با هماهنگی انجام شود.

## API و احراز هویت

> قرارداد فعلی ورود (Authorization Code با PKCE)، مسیرهای `/api/v1/...` و خطاها در [`backend/docs/05-frontend-guide.md`](../backend/docs/05-frontend-guide.md) است. فهرست مسیرهای زیر قدیمی است و با آن تفاوت دارد.

بک‌اند فعلی از Keycloak استفاده می‌کند. مسیرهای مهم فعلی:

```text
GET /api/auth/me/
GET /api/admin-panel/
GET /api/candidate/
GET /api/advisor/
GET /api/teams/<team-number>/<path>
```

توکن باید در درخواست‌ها با هدر زیر ارسال شود:

```http
Authorization: Bearer <access_token>
```

`src/shared/api/httpClient.ts` تنها محل عمومی ارسال درخواست‌ها است. برای هر feature، endpointها را در فایل API همان feature تعریف کنید و JSX را مستقیماً به `fetch` وصل نکنید.

> توجه: فرم Login فعلی اسکلت اولیه است. قرارداد نهایی Login باید بر اساس جریان واقعی Keycloak و قرارداد بک‌اند تکمیل شود؛ نام endpoint یا payload را حدس نزنید.

## i18n، RTL و Theme

- زبان‌های اولیه: فارسی (`fa`) و انگلیسی (`en`).
- متن قابل مشاهده در JSX باید از `react-i18next` بیاید.
- تغییر زبان باید `lang` و `dir` سند را تنظیم کند.
- برای RTL/LTR از CSS logical properties مانند `margin-inline-start` و `padding-inline-end` استفاده کنید.
- رنگ‌ها، فاصله‌ها، شعاع‌ها و سایه‌ها باید در design tokenها تعریف شوند.
- زبان و تم باید بعد از refresh قابل حفظ باشند.

## قواعد توسعه با AI

قبل از درخواست کد، سند زیر را به AI بدهید:

[`GRADIAN_FRONTEND_PROJECT_GUIDE.md`](./GRADIAN_FRONTEND_PROJECT_GUIDE.md)

هر درخواست کدنویسی باید حداقل این موارد را مشخص کند:

```text
Feature:
Route:
Goal:
Allowed files:
API contract:
Roles/permissions:
States: loading, empty, error, success
Languages: fa, en
Direction: RTL/LTR
Theme: light/dark
Validation command:
```

AI باید قبل از تغییر repository را بررسی کند، فایل تکراری نسازد، فقط فایل‌های لازم را تغییر دهد و پس از تغییر `npm run build` یا تست متناسب را اجرا کند.

## Production

برای build تولیدی فرانت‌اند:

```powershell
cd frontend
docker build -t gradian-frontend .
docker run --rm -p 8081:80 gradian-frontend
```

در production، Nginx فایل‌های static را ارائه می‌کند و fallback مسیرهای React Router را به `index.html` برمی‌گرداند. پورت `8081` عمداً انتخاب شده تا با Keycloak روی `8080` تداخل نداشته باشد.

Compose تولیدی داخل `frontend/` فقط برای اجرای مستقل production است:

```powershell
cd frontend
Copy-Item .env.example .env
docker compose -f docker-compose.prod.yml up --build
```

برای کار روزمره‌ی تیم، Compose ریشه مرجع اصلی است.

## چک‌لیست تحویل Feature

- route قابل refresh است؛
- permission و role مشخص است؛
- API و typeها از UI جدا هستند؛
- حالت‌های loading، empty، error و success بررسی شده‌اند؛
- فارسی، انگلیسی، RTL و LTR بررسی شده‌اند؛
- responsive بودن در موبایل بررسی شده است؛
- secret یا token داخل کد commit نشده است؛
- `npm run build` موفق است؛
- فایل‌های تغییرکرده و محدودیت‌های شناخته‌شده در PR نوشته شده‌اند.
