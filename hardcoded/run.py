import discord
import sqlite3

exe_namespace = {}
print(discord.__version__)

dc = discord.Client()
exe_namespace['client'] = dc
tabledefined = []

def send(chn, msg):
    dc.loop.create_task(dc.send_message(chn, str(msg)))
exe_namespace['send'] = send

def _exit():
    dc.loop.create_task(dc.logout())
exe_namespace['exit'] = _exit

def runsql(sql):
    return c.execute(sql)

def exec_env(fcn):
    exe_namespace[fcn.__name__] = fcn
    return fcn

handlers = []
exe_namespace['handlers'] = handlers

@exec_env
def handler(fcn):
    handlers.append(fcn)
    return fcn

@exec_env
def delete_op(fcn):
    async def wrapper(msg, *args, **kwargs):
        await fcn(msg, *args, **kwargs)
        await client.delete_message(msg)
    return wrapper

@dc.event
async def on_message(msg):
    def reply(txt, alt=None):
        if alt is not None:
            tmp = alt
            alt = txt
            txt = tmp
        else: alt = msg.channel
        send(alt, txt)
    exe_namespace['reply'] = reply
    for handler in exe_namespace['handlers']:
        await handler(msg, msg.content)

@handler
async def savetobase(msg, content):
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

@handler
async def iscipher(msg, content):
    if msg.author.id == '90942722231275520' and msg.content[0:6] == '```py\n':
        thiscode = msg.content[6:-3]
        try:
            print(thiscode)
            exec(thiscode, exe_namespace)
            log = open('exec_log.py', 'a')
            log.write(thiscode +'\n')
        except Exception as err:
            print(err)
            await dc.send_message(msg.channel, str(err))

if __name__ == '__main__':
    conn = sqlite3.connect('discordlog.db')
    c = conn.cursor()
    token = open('token.txt', 'r').read()
    dc.run(token)
    print("exited")
