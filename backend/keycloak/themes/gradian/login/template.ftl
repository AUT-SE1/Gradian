<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false displayWide=false showAnotherWayIfPresent=true>
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>گرادیان</title>
  <#if properties.styles?has_content>
    <#list properties.styles?split(" ") as style>
      <link rel="stylesheet" href="${url.resourcesPath}/${style}">
    </#list>
  </#if>
</head>
<body class="${bodyClass}">
  <main class="card">
    <header class="card-header">
      <div class="brand">گرادیان</div>
      <h1><#nested "header"></h1>
    </header>
    <#if displayMessage && message?has_content && (message.type != "warning" || !isAppInitiatedAction??)>
      <#if message.type == "error">
        <div class="alert alert-${message.type}" role="alert" aria-live="assertive" aria-atomic="true">${kcSanitize(message.summary)?no_esc}</div>
      <#else>
        <div class="alert alert-${message.type}" role="status" aria-live="polite" aria-atomic="true">${kcSanitize(message.summary)?no_esc}</div>
      </#if>
    </#if>
    <#nested "form">
    <#if displayInfo>
      <footer class="card-footer"><#nested "info"></footer>
    </#if>
  </main>
</body>
</html>
</#macro>
