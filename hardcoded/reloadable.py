import os
import discord
import sqlite3
import logging

logfiles = {}
exe_namespace = {
    'discord':  discord,
    'logfiles': logfiles
}
print(discord.__version__)

dc = discord.Client()
exe_namespace['client'] = dc
tabledefined = []

def send(chn, msg):
    dc.loop.create_task(dc.send_message(chn, str(msg)))
exe_namespace['send'] = send

def _exit():
    async def _exit_inner():
        await dc.logout()
        print("logged out")
    dc.loop.create_task(_exit_inner())
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

def decode_id(i):
    i = int(i)
    return (
        # offset from 2015-01-01
        (i >> 22) + 1420070400000,
        # extract lower 22 bits. (4194303 = 2^22-1)
        (i & 4194303).to_bytes(3, byteorder='big'))

def decoded_id_str(i):
    if type(i) is not tuple: i = decode_id(i)
    return datetime.datetime.fromtimestamp(i[0]/1000.0) \
        .strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] \
        + ' 0x' + ''.join(format(x, '02x') for x in i[1])

@handler
async def savetofile(msg, content):
    channel = msg.channel
    if channel.server.id != '171461285416927233': return
    if channel.id not in logfiles:
        filepath = '../logs/%s/%s'% (channel.server.id, channel.id)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        log = open(filepath, 'ab')
        logfiles[channel.id] = log
    else: log = logfiles[channel.id]
    log.write(int(msg.id).to_bytes(8, byteorder='little'))
    log.write(int(msg.author.id).to_bytes(8, byteorder='little'))
    # avoid nulls
    content = msg.content.encode('utf-8', "replace").replace(b'\x00', b'')
    log.write(content +b'\x00')
    if msg.embeds:
        # double nulls + num of embeds (max 255)
        log.write(b'\x00'+ len(msg.embeds).to_bytes(1, byteorder='little'))
        for emb in msg.embeds:
            log.write(emb.encode('utf-8').replace(b'\x00', b'') +b'\x00')
    log.flush()

@handler
async def readfromfile(msg, content):
    channel = msg.channel
    if channel.server.id != '171461285416927233': return
    if msg.content[:5] != "'read": return
    index = 0
    filepath = '../logs/%s/%s'% (channel.server.id, channel.id)
    if channel.id not in logfiles:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
    else:
        logfiles[channel.id].close()
        del logfiles[channel.id]
    log = open(filepath, 'rb')
    for i in range(index):
        first = log.read(1)
        log.read(15)
        b = None
        while b != b'\x00': b = log.read(1)
        #TODO: finish this
    msgid  = int.from_bytes(log.read(8), byteorder='little')
    authid = str(int.from_bytes(log.read(8), byteorder='little'))
    b = log.read(1)
    msgb = b''
    while b != b'\x00':
        msgb += b
        b = log.read(1)
    auth = discord.utils.find(lambda x: x.id == authid, msg.server.members)
    auth = authid if auth is None else auth.name
    await dc.send_message(channel, str(msgid) +'-'+ auth \
        +': '+ msgb.decode('utf-8'))

#@handler
# async def savetobase(msg, content):
#     channel = msg.channel
#     if channel not in tabledefined:
#         c.execute('''CREATE TABLE IF NOT EXISTS chn%s (
#             id INTEGER PRIMARY KEY,
#             author INTEGER,
#             datetime INTEGER,
#             content TEXT ) WITHOUT ROWID''' % channel.id)
#         tabledefined.append(channel)
#     c.execute('INSERT INTO chn%s VALUES (?,?,?,?)' % channel.id,
#         (msg.id, msg.author.id, msg.timestamp, msg.content))

@handler
async def isowner(msg, content):
    if msg.author.id == botOwner and msg.content[0:6] == '```py\n':
        thiscode = msg.content[6:-3].replace('\t','    ')
        thiscode = '\n    '.join(
            ['async def _exec_(msg, channel, server):']+ thiscode.split('\n'))
        try:
            print(thiscode)
            localvars = {
                'msg': msg,
                'channel': msg.channel,
                'server': msg.server
            }
            exec(thiscode, exe_namespace, localvars)
            await localvars['_exec_'](msg, msg.channel, msg.server)
            log = open('exec_log.py', 'a')
            log.write(thiscode +'\n')
        except Exception as err:
            print(err)
            await dc.send_message(msg.channel, str(err))

#c = None

def run():
    #global c
    #conn = sqlite3.connect('discordlog.db')
    #c = conn.cursor()
    global botOwner
    if os.path.isfile('botOwner.txt'):
        botOwner = open('botOwner.txt', 'r').read()
    else:
        botOwner = '90942722231275520'
    token = open('token.txt', 'r').read()
    dc.run(token)
    for f in logfiles:
        f.close()

if __name__ == '__main__': run()
