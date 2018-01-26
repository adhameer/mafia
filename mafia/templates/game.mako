<%inherit file="base.mako" />
<%block name="title">Mafia - Game in Progress</%block>

<h1>${game.phase.title()} ${game.turn}</h1>

% if messages:
<div class="messages">
    <ul>
        % for message in messages:
        <li>${message}</li>
        % endfor
    </ul>
</div>
% endif

% if game.phase == "day":
<%include file="day.mako" />
% else:
<%include file="night.mako" />
% endif
