<#import "template.ftl" as layout>
<#macro field name label type="text" dir="">
  <label for="${name}">${label}</label>
  <input id="${name}" name="${name}" type="${type}" <#if dir?has_content>dir="${dir}"</#if>
         value="${(register.formData[name]!'')}"
         aria-invalid="<#if messagesPerField.existsError(name)>true<#else>false</#if>">
  <#if messagesPerField.existsError(name)>
    <span class="field-error">${kcSanitize(messagesPerField.get(name))?no_esc}</span>
  </#if>
</#macro>
<@layout.registrationLayout displayInfo=true displayMessage=!messagesPerField.existsError('firstName','lastName','username','email','password','password-confirm'); section>
  <#if section = "header">
    ثبت‌نام در گرادیان
  <#elseif section = "form">
    <form id="kc-register-form" action="${url.registrationAction}" method="post">
      <@field name="firstName" label="نام" />
      <@field name="lastName" label="نام خانوادگی" />
      <@field name="username" label="شماره موبایل" dir="ltr" />
      <@field name="email" label="ایمیل" type="email" dir="ltr" />
      <#if passwordRequired??>
        <@field name="password" label="رمز عبور" type="password" dir="ltr" />
        <@field name="password-confirm" label="تکرار رمز عبور" type="password" dir="ltr" />
      </#if>
      <button class="btn" type="submit">ثبت‌نام</button>
    </form>
  <#elseif section = "info">
    قبلاً ثبت‌نام کرده‌اید؟ <a href="${url.loginUrl}">ورود</a>
  </#if>
</@layout.registrationLayout>
