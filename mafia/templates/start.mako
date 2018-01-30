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

    % for entry in form.roles:
    <p>${entry()}</p>
    % endfor

    <p>
        ${form.start_phase.label()}
        ${form.start_phase()}
    </p>

    ${form.submit()}
</form>
