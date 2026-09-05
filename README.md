# ABC

ABC is a thinking and learning tool inspired by Vera F. Birkenbihl's
ABC method, implemented as a Yakoon capability.

The user organizes knowledge into categories and topics. An ABC run
encourages free association across the letters A–Z while keeping the
cognitive work with the human.

The core principle is simple:

> Digitize the administration of the learning method, not the cognitive
> work of the learning method.

ABC does not suggest answers, complete thoughts, evaluate knowledge, or
use AI during an active run.

## Domain Model

    Category
        └── Topic
              ├── Run
              └── Run

- `Category` — a named collection of related topics. Names are globally
  unique, case-insensitively.
- `Topic` — a subject within a category. Names are unique within their
  category, case-insensitively.
- `Run` — one completed ABC run of a topic: an immutable historical
  snapshot with a timestamp and the entries collected during the run,
  assigned to the letters A–Z. Entries are never edited; a run can be
  removed as a whole.

Only empty containers may be deleted. A category containing topics or a
topic containing runs cannot be deleted.

## Commands

ABC is mounted at `/opt/abc`.

    /opt/abc
        category/
            add
            edit
            delete
            list
            find

        topic/
            add
            edit
            delete
            list
            find

        run/
            new
            list
            show
            delete

`find` performs a case-insensitive substring search over names.

Topic search results include their category so that similarly named
topics remain distinguishable.

## Store

ABC uses the logical store `abc`.

Storage is provided through Yakoon's Store abstraction. The concrete
backend is defined by the installation and is not part of the ABC
capability.

## ABC Runs

`run new` starts an interactive run for a topic. The user sees the
topic and the retrieval keys A–Z and 0–9 as a retrieval cue; keys with
entries are emphasized. The user enters associations on a single input
line; several entries can be separated with a semicolon:

    army; emperor; republic; civil rights

An entry is placed under the key character it begins with: the first
character must be an ASCII A–Z letter or a digit. A key prefix
overrides this:

    army                     -> A
    emperor                  -> E
    1945                     -> 1
    9. November              -> 9
    4: 1945                  -> 4
    a: plenty of distance    -> A

Entries that do not begin with a key character (for example umlaut
words like "Ärzte") are not stored — the run view names them and a key
prefix assigns them ("a: Ärzte"). Commas remain ordinary content and
are not separators. Each Enter accepts the input, appends the entries
to the current run state and re-renders the run view; the submitted
input itself is cleared and appears only in the accumulated entries.
Entries under the same key that differ only in case are stored once
(comparison ignores case); the spelling of the first entry is kept.

**Ctrl+N finishes the run.** Finishing stores one immutable run
snapshot for the topic; an empty run is discarded. With `--test` the
run behaves exactly like a normal run, but finishing stores nothing —
knowledge can be tested without creating a real run. Esc pauses the run
(within the session) and Ctrl+X cancels it without storing anything.

During a run, no previous answers, suggestions, search, autocomplete,
AI assistance, evaluation, or scores are present. Completed runs are
historical snapshots and are not edited; `run delete` removes a run as
a whole (for example a discarded test run or an accidental save).

`run list` shows the runs of a topic with their timestamps and entry
counts; `run show` displays one run grouped by key; `run delete` removes
one run.

## Development

Run the tests with:

    python -m pytest tests
