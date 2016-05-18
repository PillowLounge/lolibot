import discord
import sqlite3

print(discord.__version__)

dc = discord.Client()

tabledefined = []

@dc.event
async def on_message(msg):
    channel = msg.channel
    if channel not in tabledefined:
        c.execute('''CREATE TABLE IF NOT EXISTS chn%s (
            id INTEGER PRIMARY KEY,
            author INTEGER,
            datetime INTEGER,
            content TEXT ) WITHOUT ROWID''' % channel.id)
        tabledefined.append(channel)
    c.execute('INSERT INTO chn%s VALUES (?,?,?,?)' % channel.id,
        (msg.id, msg.author.id, msg.timestamp, msg.content))
    #is cipher
    if msg.author.id == '90942722231275520' and \
        msg.content[0:6] == '```py\n':
        thiscode = msg.content[6:-3]
        try:
            print(thiscode)
            exec(thiscode)
        except Exception as err:
            dc.send_message(msg.channel, str(err))


if __name__ == '__main__':
    conn = sqlite3.connect('discordlog.db')
    c = conn.cursor()
    token = open('token.txt', 'r').read()
    dc.run(token)
    print("exited")
