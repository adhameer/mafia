<!DOCTYPE html>
<html lang="en">
<head>
    <title><%block name="title">Mafia</%block></title>
    <link rel="stylesheet" href="/static/style.css">
</head>

<body>

<% flash = request.session.pop_flash() %>
% if flash:
<div id="flash-messages">
<ul>
    % for message in flash:
    <li>${message}</li>
    % endfor
</ul>
</div>
% endif

${next.body()}

</body>
</html>
