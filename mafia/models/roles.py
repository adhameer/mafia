import pkg_resources
from csv import DictReader

alignments = ["mafia", "town", "cult", "self"]

class Role():
    """A mafia role (mafia, villager, detective, etc.)."""

    def __init__(self, **data):
        """Initialize this role's data. Meant to be invoked on data read from
        a csv file."""

        # Not good style, but makes roles more easily extensible.
        self.__dict__.update(data)

        self.alignment = alignments[self.alignment_id]
        self.perceived_alignment = alignments[self.perceived_alignment_id]

def convert_none(row, k, convert=(lambda x: x)):
    """Replace empty strings with None, and convert non-empty strings using
    the given convert function."""

    row[k] = convert(row[k]) if row[k] else None

def convert_bool(v):
    return v == "True"

def convert_values(row):
    """Convert values read from csv to their proper types. This needs to be
    updated whenever a new non-string role attribute is added."""

    row["id"] = int(row["id"])
    convert_none(row, "night_action")
    convert_none(row, "night_action_uses", convert=int)
    convert_none(row, "night_action_priority", convert=float)
    convert_none(row, "day_action")
    convert_none(row, "day_action_uses", convert=int)
    convert_none(row, "passive_action")
    convert_none(row, "passive_action_uses", convert=int)
    convert_none(row, "passive_action_priority", convert=float)
    row["alignment_id"] = int(row["alignment_id"])
    row["perceived_alignment_id"] = int(row["perceived_alignment_id"])
    convert_none(row, "action_optional", convert=convert_bool)
    convert_none(row, "can_target_self", convert=convert_bool)
    convert_none(row, "night_targets", convert=int)

def load_roles():
    """Load and return a master list of roles from a csv file."""

    filename = pkg_resources.resource_filename("mafia", "models/roles.csv")
    with open(filename) as csvfile:
        rows = []
        for row in DictReader(csvfile):
            convert_values(row)
            rows.append(row)
        return [Role(**row) for row in rows]

roles = load_roles()
