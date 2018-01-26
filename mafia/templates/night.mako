<%! from mafia.views.night import NoTargetForm, TargetForm, SkipForm %>
<form id="night-action" action="/play" method="POST">
% if player == "mafia":
<h2>Mafia Kill</h2>
% else:
<h2>${player.name} (${player.role.name})'s action</h2>
% endif

% if isinstance(form, NoTargetForm):
${form.choice()}
% elif isinstance(form, TargetForm):
    % for target in form.targets:
    ${target()}
    % endfor
%endif

${form.submit()}
</form>
