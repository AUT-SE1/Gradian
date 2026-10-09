<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=(realm.password && realm.registrationAllowed && !registrationDisabled??); section>
  <#if section = "header">
    ورود به گرادیان
  <#elseif section = "form">
    <form id="kc-form-login" action="${url.loginAction}" method="post">
      <label for="username">شماره موبایل</label>
      <input id="username" name="username" type="text" inputmode="numeric" dir="ltr"
             value="${(login.username!'')}" autofocus autocomplete="username" placeholder="09123456789">

      <label for="password">رمز عبور</label>
      <div class="password-field">
        <input id="password" name="password" type="password" dir="ltr" autocomplete="current-password">
        <button type="button" class="toggle" data-toggle-password="password">نمایش</button>
      </div>

      <#if realm.rememberMe && !usernameHidden??>
        <label class="check">
          <input type="checkbox" name="rememberMe" <#if login.rememberMe??>checked</#if>>
          مرا به خاطر بسپار
        </label>
      </#if>

      <button class="btn" name="login" type="submit">ورود به سامانه</button>
    </form>
    <script>
      document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
        button.addEventListener("click", function () {
          var input = document.getElementById(button.dataset.togglePassword);
          input.type = input.type === "password" ? "text" : "password";
          button.textContent = input.type === "password" ? "نمایش" : "پنهان";
        });
      });
    </script>
  <#elseif section = "info">
    حساب ندارید؟ <a href="${url.registrationUrl}">ثبت‌نام</a>
  </#if>
</@layout.registrationLayout>
