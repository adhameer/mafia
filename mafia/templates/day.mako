<form id="day-players" action="/play" method="POST">
<table class="players">
    <tr>
        <th>Player</th>
        <th>Role</th>
        <th>Lynch</th>
        <th>Action</th>
    </tr>
    % for (i, player_form) in enumerate(form.actions):
    <tr>
        <% player = game.players[i] %>
        <td>
            % if not player.is_alive:
            <span class="dead">
            % elif player.is_bleeding:
            <span class="bleeding">
            % else:
            <span>
            % endif
                ${player.name}
            </span>
        </td>
        <td>${player.role.name}</td>
        <td>
            % if player.is_alive:
            ${player_form.lynch}
            % endif
        </td>
        <td>
            % if player.has_day_action():
            <p>
                ${player_form.action_target()}
                ${player_form.action_submit()}
            </p>
            % endif

            % if player.can_use_gun():
            <p>
                ${player_form.gun_target()}
                ${player_form.gun_submit()}
            </p>
            % endif
        </td>
        ${player_form.hidden()}
    </tr>
    % endfor
</table>
<p>${form.start_night()}</p>
</form>
