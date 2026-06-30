<!DOCTYPE html>
<html>
<body>
<form id="f" action="${url.logoutConfirmAction}" method="post">
    <input type="hidden" name="session_code" value="${logoutConfirm.code}">
    <input type="hidden" name="tab_id" value="${logoutConfirm.tabId!}">
    <input type="hidden" name="confirmLogout" value="on"/>
</form>
<script>document.getElementById("f").submit();</script>
</body>
</html>
