# R05 — تکمیل فرم و قالب واقعی Keycloak

تاریخ: 2026-10-21

## وضعیت

**IN_PROGRESS — FUNCTIONAL IMPLEMENTED / BLOCKED_DESIGN / PENDING_LIVE**

بخش مستقل از طراحی R05 روی خروجی R04 پیاده شد، اما این تسک طبق برنامه به R02 و پذیرش زنده R03 وابسته است. مرجع بصری مستقل و تأییدشده برای فرم ثبت‌نام در ورودی موجود نیست؛ بنابراین ظاهر جدیدی از روی سلیقه ساخته نشد و پذیرش پیکسلی/تصویر مقایسه‌ای موفق اعلام نمی‌شود. Keycloak زنده نیز در این محیط اجرا نشد، پس رندر واقعی FreeMarker و ارسال واقعی فرم هنوز باید در محیط کاربر تأیید شوند.

## تغییرات انجام‌شده

### 1. ایمن‌سازی retry فرم ثبت‌نام

`register.ftl` همچنان داده‌های غیرحساس `firstName`، `lastName`، `username` و `email` را از `register.formData` بازیابی می‌کند، اما برای `password` و `password-confirm` اصلاً attribute نوع `value` رندر نمی‌شود. هر دو فیلد رمز `autocomplete="new-password"` دارند.

### 2. قرارداد واقعی Keycloak حفظ شد

- action فرم ثبت‌نام همان `${url.registrationAction}` است.
- نام شش فیلد پایه Keycloak حفظ شد.
- لینک برگشت فرم ثبت‌نام از `${url.loginUrl}` استفاده می‌کند.
- صفحه ورود فقط وقتی realm اجازه ثبت‌نام می‌دهد و registration برای request غیرفعال نشده است، لینک ثبت‌نام را نشان می‌دهد.
- لینک ورود به ثبت‌نام از `${url.registrationUrl}` استفاده می‌کند و URL ثابت/دستی ساخته نشده است.

### 3. خطا و دسترس‌پذیری

- خطای هر فیلد با `kcSanitize(messagesPerField.get(name))?no_esc` باقی ماند.
- `aria-invalid` و `aria-describedby` به خطای مرتبط با همان input متصل شدند.
- خطای فیلد `role="alert"` دارد و پیام عمومی sanitize‌شده در template با `aria-live="polite"` نمایش داده می‌شود.
- label واقعی، required/aria-required، focus-visible و focus قابل تشخیص برای input/button/link حفظ/اضافه شد.
- autocomplete مناسب برای نام، نام خانوادگی، موبایل/username، ایمیل و رمزهای جدید اضافه شد.
- برای موبایل `inputmode="numeric"` و نمونه canonical `09123456789` استفاده شد.

### 4. موبایل

در عرض‌های کوچک card تمام عرض مفید را می‌گیرد و inputها 16px هستند تا zoom ناخواسته مرورگر موبایل کاهش یابد. این responsive behavior تصمیم فنی است، نه ادعای تطابق با طرح موبایل؛ طرح موبایل ثبت‌نام در منابع موجود تأیید نشده است.

### 5. نمایش رمز

برای فرم ثبت‌نام toggle نمایش رمز اضافه نشد. برنامه R05 آن را فقط در صورت طرح تأییدشده مجاز کرده است. toggle موجود login دست‌نخورده باقی ماند.

## فایل‌های تغییرکرده

- `backend/keycloak/themes/gradian/login/register.ftl`
- `backend/keycloak/themes/gradian/login/login.ftl`
- `backend/keycloak/themes/gradian/login/template.ftl`
- `backend/keycloak/themes/gradian/login/resources/css/gradian.css`
- `backend/keycloak/themes/gradian/README.md`
- `backend/scripts/tests/test_r05_theme_contract.py` — جدید
- `GRADIAN_REGISTRATION_TASKS.md`
- `GRADIAN_SESSION_CONTEXT.md`
- `docs/registration/R05_KEYCLOAK_FORM.md` — این گزارش

## بررسی اجراشده در این محیط

تست contract استاتیک source واقعی قالب را بررسی می‌کند و موارد زیر را قفل می‌کند: action/نام فیلدها، عدم بازتاب password، autocomplete، sanitization، لینک conditional ثبت‌نام، back link، focus و قرارداد موبایل.

فرمان:

```bash
cd backend
python3 -m unittest scripts.tests.test_r05_theme_contract -v
```

نتیجه واقعی:

```text
test_keyboard_and_mobile_contract ... ok
test_login_registration_link_is_conditional_and_uses_keycloak_url ... ok
test_non_sensitive_retry_values_and_accessible_field_errors_remain ... ok
test_passwords_are_never_repopulated ... ok
test_registration_back_link_and_general_message_are_provider_owned ... ok
test_registration_keeps_keycloak_action_and_six_base_fields ... ok

Ran 6 tests
OK
```

این تست contract استاتیک است و رندر FreeMarker زنده را جایگزین نمی‌کند.

## پذیرش زنده باقی‌مانده

موارد زیر در این محیط اجرا/تأیید نشده‌اند و نباید موفق فرض شوند:

1. رندر واقعی FreeMarker در Keycloak 26 محیط کاربر بدون template error؛
2. submit موفق هر شش فیلد به `url.registrationAction`؛
3. خطای رمز کمتر از ۸ کاراکتر از policy realm زنده؛
4. خطای نام فقط فاصله/ZWNJ از user profile زنده؛
5. conflict واقعی موبایل یا ایمیل تکراری؛
6. retry واقعی که داده غیرحساس را نگه دارد و هر دو رمز را خالی کند؛
7. مخفی شدن لینک ثبت‌نام وقتی realm registration خاموش است؛
8. keyboard/mobile smoke روی مرورگر واقعی؛
9. مقایسه تصویری با مرجع ثبت‌نام تأییدشده.

## مانع طراحی

R02 همچنان `BLOCKED_DESIGN` است. تصاویر داشبورد/Login قبلی مرجع قطعی فرم Registration نیستند. تا وقتی مرجع ثبت‌نام تأیید نشود، رنگ/spacing/asset یا password-toggle تازه با حدس نهایی نمی‌شود. R05 از نظر functional source آماده است، ولی طبق معیارهای پروژه هنوز `DONE` نیست.

## قدم بعد

- برای بستن R05: مرجع R02 + smoke زنده Keycloak/R03 لازم است.
- R06 نیز به R02 وابسته است و نباید نهایی شود.
- بخش مستقل R07 که به callback/role/session مربوط است می‌تواند بدون اختراع UI بررسی و پیاده‌سازی شود.
