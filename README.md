This is a simple music bot for discord people.

To build and run the bot in a container is very easy:

```
docker build -t mursic .
docker run -d --name mursic -e BOT_TOKEN=your_token_here mursic
```

Of course, feel free to do things differently if you so please.

Once running, invite the bot to your server with `Connect` and `Speak` permissions.

The bot has a `help` command to inform users of its various behaviors.

Cheers, and happy listening.
