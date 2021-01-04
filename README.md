# discord jambot

Discord-jambot is a modular bot platform built for the discord chat service. It's a conceptual port of my modular IRC bot of the same kind, with some enhancements to better suit discord-specific concepts and take advantage of the full Discord API.

## Modules

All jambot really is is a system for configuring certain module features to load into certain contexts with certain settings, as well as a shared database for them to use. Simply put, there is a single config file describing what jambot is doing where. Modules can be loaded into a global, server-specific, or channel-specific context, and will only receive API events specific to that context. If a module is loaded into a narrower (channel) scope than a module of the same type, the narrow-scope module will receive the API events instead of the wider-scoped one. This is designed to let you either only run certain features in certain channels, or to run features globally and configure them differently for specific channels.

## Config

As mentioned, there's a single config file for a single jambot instance. Other than the following required top-level configs, any other settings in this file represent where a module is loaded context-wise as well as settings for that specific module's instance in that context. A more robust example of config format is in the `sample_jambot.yml` file.

```
version: discord-jambot 0.1
token: reallylongdiscordtoken
owner: 123456789
database: jambot.db
command_prefix: '>'
```

## Database

Modules can run SQL queries against the shared SQLite DB Instance using the async `client.db_query(query)` and `client.db_commit()` methods on the bot-client object passed to module hooks. Modules should make any required table setup/checks in the `on_connect()` hook.

## Features

### Mirrorkov2

Pretty much the main feature this bot was intended for, a community-learning conversation bot using primitive markov chains. It uses pairs of 2 words as nodes and builds a graph based on the observed frequencies of their orderings as it learns, and then traverses that graph to generate a reply. The name of this specific version comes from the most recently added feature of changing graph weights based on the contexts learned from the user triggering the response (mirroring them). A disadvantage of this feature is only being able to learn directly from discord channels: the legacy markov3 module can learn from an arbitrary uploaded text file.

```
Commands:
*>feed {lines} {channelId} // Learn x lines from the history of channelId, default to current channel
*>words //check how many total words known in current model
*>known {word} //check for how many learned context include a specific word
*>clean //halve the weights of all currently learned contexts; future learned ones will be twice as likely as past onces going forward
```

### Twitch

Dedicate a discord channel to announcing the beginning of streams on twitch accounts linked to any members of the server. No need to keep track of any lists of users; any linked twitch accounts get announced (and can be filtered away through config)

### Others

Theres plenty of other modules on the modules folder but many are either obsolete or just one-off things; go ahead and take a look and ask me on discord at Ice#6667 if you have any questions.
