<#import "template.ftl" as layout>
<#macro field name label type="text" dir="" autocomplete="" inputmode="" autofocus=false placeholder="">
  <#assign hasError = messagesPerField.existsError(name)>
  <label for="${name}">${label}</label>
  <input id="${name}" name="${name}" type="${type}"
         <#if dir?has_content>dir="${dir}"</#if>
         <#if autocomplete?has_content>autocomplete="${autocomplete}"</#if>
         <#if inputmode?has_content>inputmode="${inputmode}"</#if>
         <#if autofocus>autofocus</#if>
         <#if placeholder?has_content>placeholder="${placeholder}"</#if>
         <#if type != "password">value="${(register.formData[name]!'')}"</#if>
         required aria-required="true"
         aria-invalid="<#if hasError>true<#else>false</#if>"
         <#if hasError>aria-describedby="${name}-error" aria-errormessage="${name}-error"</#if>>
  <#if hasError>
    <span id="${name}-error" class="field-error" role="alert" aria-live="assertive">${kcSanitize(messagesPerField.get(name))?no_esc}</span>
  </#if>
</#macro>

<@layout.registrationLayout displayInfo=true displayMessage=messagesPerField.exists('global'); section>
  <#if section = "header">
    ثبت‌نام در گرادیان
  <#elseif section = "form">
    <form id="kc-register-form" action="${url.registrationAction}" method="post" novalidate>
      <@field name="firstName" label="نام" autocomplete="given-name" autofocus=true />
      <@field name="lastName" label="نام خانوادگی" autocomplete="family-name" />
      <@field name="username" label="شماره موبایل" dir="ltr" autocomplete="username" inputmode="numeric" placeholder="09123456789" />
      <@field name="email" label="ایمیل" type="email" dir="ltr" autocomplete="email" inputmode="email" placeholder="name@example.com" />
      <#if passwordRequired??>
        <@field name="password" label="رمز عبور" type="password" dir="ltr" autocomplete="new-password" />
        <@field name="password-confirm" label="تکرار رمز عبور" type="password" dir="ltr" autocomplete="new-password" />
      </#if>
      <button class="btn" id="kc-register-submit" type="submit">ثبت‌نام</button>
    </form>
    <script>
      (function () {
        var form = document.getElementById("kc-register-form");
        var firstInvalid = document.querySelector('[aria-invalid="true"]');
        if (firstInvalid) firstInvalid.focus();
        if (form) {
          form.addEventListener("submit", function () {
            form.setAttribute("aria-busy", "true");
          });
        }
      }());
    </script>
  <#elseif section = "info">
    <span>قبلاً ثبت‌نام کرده‌اید؟ <a href="${url.loginUrl}">ورود</a></span>
  </#if>
</@layout.registrationLayout>
