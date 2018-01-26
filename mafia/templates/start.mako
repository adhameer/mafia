<%inherit file="base.mako" />
<%block name="title">Mafia - Create a Game</%block>

% if game:
<p><a href="/play">Resume game</a></p>
% endif

<form id="create-game" action="/" method="POST">
    <p>
        ${form.num_players.label()}
        ${form.num_players()}
        ${form.set_num_players()}
    </p>

    % if form.num_players.errors:
    <ul class="errors">
        % for error in form.num_players.errors:
        <li>${error}</li>
        % endfor
    </ul>
    % endif

    <table id="player-list">
        % for i in range(len(form.players)):
        <tr>
            <td>Player ${i + 1}</td>
            <td>${form.players[i].player_name(size=20, maxlength=25)}</td>
            <td>${form.players[i].role()}</td>
        </tr>
        % endfor

        <!-- Hidden fields to keep track of previously deleted players -->
        % for player in form.old_players:
        ${player(style="display: none")}
        % endfor
    </table>

    % if form.players.errors:
    <ul class="errors">
        % for error in form.players.errors:
        <li>${error}</li>
        % endfor
    </ul>
    % endif

    <p>
        ${form.start_phase.label()}
        ${form.start_phase()}
    </p>

    ${form.submit()}
</form>
