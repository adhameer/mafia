import pkg_resources
from csv import DictReader

alignments = ["mafia", "town", "cult", "self"]

class Action():
    """An action (kill, inspect, block, etc.)"""

    def __init__(self, **data):
        """Initialize this action's data. Meant to be invoked on data read from
        a csv file."""

        # Not good style, but makes actions more easily extensible.
        self.__dict__.update(data)

class Role():
    """A mafia role (mafia, villager, detective, etc.)."""

    def __init__(self, **data):
        """Initialize this role's data. Meant to be invoked on data read from
        a csv file."""

        # See note above.
        self.__dict__.update(data)

        self.night_action = (None if self.night_action_id is None
                             else action_ids[self.night_action_id])
        self.day_action = (None if self.day_action_id is None
                             else action_ids[self.day_action_id])
        self.passive_action = (None if self.passive_action_id is None
                             else action_ids[self.passive_action_id])
        self.alignment = alignments[self.alignment_id]
        self.perceived_alignment = alignments[self.perceived_alignment_id]

def convert_none(row, k, convert=(lambda x: x)):
    """Replace empty strings with None, and convert non-empty strings using
    the given convert function."""

    row[k] = convert(row[k]) if row[k] else None

def convert_bool(v):
    return v == "True"

def convert_action_values(row):
    """Convert values read from actions.csv to their proper types. This needs
    to be updated whenever a new non-string action attribute is added."""

    row["id"] = int(row["id"])
    convert_none(row, "priority", convert=float)
    convert_none(row, "can_target_self", convert=convert_bool)
    convert_none(row, "targets", convert=int)
    convert_none(row, "immediate", convert=convert_bool)

    return Action(**row)

def convert_role_values(row):
    """Convert values read from roles.csv to their proper types. This needs to
    be updated whenever a new non-string role attribute is added."""

    row["id"] = int(row["id"])
    convert_none(row, "night_action_id", convert=int)
    convert_none(row, "night_action_uses", convert=int)
    convert_none(row, "day_action_id", convert=int)
    convert_none(row, "day_action_uses", convert=int)
    convert_none(row, "passive_action_id", convert=int)
    convert_none(row, "passive_action_uses", convert=int)
    row["alignment_id"] = int(row["alignment_id"])
    row["perceived_alignment_id"] = int(row["perceived_alignment_id"])
    convert_none(row, "action_optional", convert=convert_bool)

    return Role(**row)

def load_csv(filename, converter):
    """Load the csv file located in the mafia package under models/filename.csv
    and return the result of applying converter to each row."""

    file = pkg_resources.resource_filename(
        "mafia", "models/{}.csv".format(filename))
    with open(file) as csvfile:
        return [converter(row) for row in DictReader(csvfile)]

def load_actions():
    """"Load and return a master list of actions from a csv file."""

    return load_csv("actions", convert_action_values)

def load_roles():
    """Load and return a master list of roles from a csv file."""

    return load_csv("roles", convert_role_values)

action_ids = load_actions()
actions = {action.name: action for action in action_ids}
roles = load_roles()
