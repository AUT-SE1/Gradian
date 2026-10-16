<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=false; section>
  <#if section = "header">
    ورود به سامانه
  <#elseif section = "form">
    <p class="login-subtitle">شماره موبایل خود را وارد نمایید</p>
    <form id="kc-form-login" action="${url.loginAction}" method="post">
      <label for="username">شماره موبایل</label>
      <input id="username" name="username" type="text" inputmode="numeric" dir="ltr"
             value="${(login.username!'')}" autofocus autocomplete="username" placeholder="09121122334">

      <label for="password">کلمه عبور</label>
      <div class="password-field">
        <input id="password" name="password" type="password" dir="ltr" autocomplete="current-password" placeholder="••••••••">
        <button type="button" class="toggle" data-toggle-password="password" aria-label="نمایش یا مخفی کردن کلمه عبور">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.7"/></svg>
        </button>
      </div>

      <#if realm.rememberMe && !usernameHidden??>
        <label class="check">
          <input type="checkbox" name="rememberMe" <#if login.rememberMe??>checked</#if>>
          <span>مرا به خاطر بسپار</span>
        </label>
      </#if>

      <button class="btn" name="login" type="submit">ورود به سامانه</button>
    </form>
    <script>
      document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
        button.addEventListener("click", function () {
          var input = document.getElementById(button.dataset.togglePassword);
          input.type = input.type === "password" ? "text" : "password";
        });
      });
    </script>
  </#if>
</@layout.registrationLayout>
