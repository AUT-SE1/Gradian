# نسخه اصلاح‌شده Gradian

این نسخه بر مبنای `Gradian-main(1).zip` و طراحی‌های `figma.pdf` / رفتارهای `core.pdf` آماده شده است.

اصلاحات اصلی:
- Landing مطابق طراحی Figma؛ فقط «شروع یادگیری» و «ورود به پرتال یکپارچه» کاربر را وارد جریان Login می‌کنند.
- Login واقعی با Keycloak Authorization Code + PKCE و بدون endpoint جعلی `/api/auth/login/`.
- صفحه Login خود Keycloak با ظاهر صفحه Login موجود در Figma (شماره موبایل، رمز، نمایش/مخفی رمز، مرا به خاطر بسپار).
- callback ورود، دریافت `/api/v1/me` و هدایت نقش‌ها به Student / Consultant / Professor / Admin.
- نگهداری Session در مرورگر و محافظت از مسیرهای پنل.
- Logout از SSO و بازگشت به Landing.
- پنل Student، Admin، Consultant و Professor مطابق ساختار Figma/Core.
- سرویس‌های دانش‌آموز به سرویس گروه مربوط در پورت‌های 8001 تا 8010 متصل شده‌اند.
- سرویس‌های پنل‌های مدیریتی در ناحیه محتوای همان پنل انتخاب می‌شوند و لینک سرویس گروه مربوط را نمایش می‌دهند.
- API base روی `/api/v1` اصلاح شده و با `.env` قدیمی که `/api` داشته نیز سازگار است.
- Dockerfileهای Python برای شبکه فعلی روی mirror در دسترس PyPI تنظیم شده‌اند.

کاربران تست پس از `make users` در `backend/build/credentials/users.csv` هستند؛ رمز seed پیش‌فرض `change-me` است.
