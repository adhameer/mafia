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

% for i, log in enumerate(game.action_logs):
## NOTE: currently assumes game didn't have a night 0 (i.e. started in the day phase)
<h3>Night ${i + 1}</h3>
<ul class="action-log">
    % for player, action, targets in log:
    <li><span class="player-name">${player.name}</span> (<span class="role">${player.role_name}</span>) uses <span class="action">${action.name}</span> on <span class="target">${", ".join(target.name for target in targets)}</span></li>
    % endfor
</ul>
% endfor

<p><a href="/">Start a new game</a></p>
