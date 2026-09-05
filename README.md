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

- `Category` — a named collection of related topics. Names are globally
  unique, case-insensitively.
- `Topic` — a subject within a category. Names are unique within their
  category, case-insensitively.

Only empty containers may be deleted. A category containing topics
cannot be deleted.

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

`find` performs a case-insensitive substring search over names.

Topic search results include their category so that similarly named
topics remain distinguishable.

## Store

ABC uses the logical store `abc`.

Storage is provided through Yakoon's Store abstraction. The concrete
backend is defined by the installation and is not part of the ABC
capability.

## Planned

ABC runs will add historical learning snapshots to a topic:

    Category
        └── Topic
              ├── Run
              ├── Run
              └── Run

The intended interaction is deliberately simple. The user enters
associations on a single input line; several entries can be separated
with a semicolon:

    Armee; Kaiser; Republik; Bürgerrecht

An entry is placed under the letter it begins with. A letter prefix
overrides this:

    Armee                        -> A
    Kaiser                       -> K
    a: genügend Abstand halten   -> A

Commas remain ordinary content and are not separators.

During a run, no previous answers, suggestions, search, autocomplete,
AI assistance, evaluation, or scores are present. Completed runs are
historical snapshots and are not edited.

The run commands will be documented here once implemented.

## Development

Run the tests with:

    python -m pytest tests
