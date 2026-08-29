# Investigation: skills written for the everyday 8B

The everyday brain is small. It does not follow a 7-step essay. It copies
**one `Action:` block** — often the first example in the system prompt, or
it pastes the whole menu. Skills are published only after
`scripts/skill_probe.py` on this machine.

Related: [everyday-laptop](./everyday-laptop.md).

## Experiments (29 Aug 2026, `llama3.1:8b`)

Verbose skills (when-to / numbered steps):

| Task | First action | Result |
| --- | --- | --- |
| `what does apply_source refuse?` | `read` random file | Missed `code.py` |
| same + “start with grep” | `read` then `grep` then `done` | No refuse rules |
| `add … multiply` | `Find: def add(left` | Syntax break (harness now refuses) |
| same | `Action: write-tests` | Not an action |

Tiny skills + harness prelude + short system prompt
(`scripts/skill_probe.py`):

| Task | prelude | First parsed action | Notes |
| --- | --- | --- | --- |
| apply_source refuse | yes | **`done`** | Summary named empty draft, 2/3 length, syntax |
| apply_source refuse | no | `grep` + wrong `read` | Invented a non-ASCII story |
| add multiply | yes, long system prompt | `skill` (menu dump) | 8B pasted every Action example |
| add multiply | yes, short system prompt | **`patch` + Append** | Intended first step |

Then: if the model still dumps a menu, `parse_turn_smart` keeps **one**
block — `done`/`locate` on a question, `patch`/`edit` on an add.

## What to publish

These four kit skills, each a **single copy-paste Action** (no essays):

- `skills/answer-question/SKILL.md`
- `skills/add-feature/SKILL.md`
- `skills/write-tests/SKILL.md`
- `skills/stay-scoped/SKILL.md`

Plus harness: `prelude()` locate before the model, `Action: locate`,
`parse_turn_smart`, syntax reject, skill-name-as-action.

Do not publish a new skill until `skill_probe.py` shows the intended
`action` with `"prelude": true`.

## Do not

- Do not train more 0.5B to “learn skills”.
- Do not put hostnames or personal paths on Pages.
- Do not name third-party products in skill text.
