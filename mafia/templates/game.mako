<%! from mafia.views.play import PlayerForm, NextPlayerForm %>
<%inherit file="base.mako" />
<%block name="title">Mafia - Game in Progress</%block>

% if context.get("unnamed_player", None):
<form id="player-info" action="/play" method="POST">
% if isinstance(form, PlayerForm):
<p>Next player, enter your name:</p>
<p>${form.player_name()} ${form.submit()}</p>
% else:
<p>Your role is ${unnamed_player.secret_role_name()}. ${form.submit()}</p>
% endif
</form>

%else:
<h1>${game.turn()}</h1>

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
% endif
