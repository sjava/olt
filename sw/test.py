from Exscript import Account
from Exscript.protocols import Telnet

account = Account('username', 'passwd')
conn = Telnet()
conn.connect('ip')
conn.login(account)
