<%inherit file="base.mako" />
<%block name="title">Mafia - Game Over</%block>

<h1>Game Over</h1>

% if messages:
<div class="messages">
    <ul>
        % for message in messages:
        <li>${message}</li>
        % endfor
    </ul>
</div>
% endif

<p>${winner} wins!</p>

<h2>Roles</h2>
<ul class="roles-list">
    % for player in game.players:
    <li><span class="player-name">${player.name}</span>: <span class="role">${player.role_name}</span></li>
    % endfor
</ul>

<h2>Action Log</h2>

% for log in game.action_logs:
<h3>${log.phase}</h3>
<ul class="action-log">
    % for entry in log.actions:
    <li>${entry.html_str() | n}</li>
    % endfor
</ul>
% endfor

<p><a href="/">Start a new game</a></p>
