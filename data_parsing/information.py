import psycopg2
from environ import API_KEY
from environ import DB_PASS
conn = psycopg2.connect(database="smash_statistics",
                        host="localhost",
                        user="postgres",
                        password=DB_PASS,
                        port="9292")
cursor = conn.cursor()
print("This is the information for all weeklies that have occurred since Jard took over!")
username = ""
while username == "":
    username = input("Enter the tag of the player you want to search for: ")
username = "%" + username + "%"
cursor.execute("SELECT * FROM player WHERE lower(tag) LIKE %s", (username,))
names = cursor.fetchall()
i = 1
print("Matching users are:")
for name in names:
    print("{i}: {name}".format(i=i, name=name[1]))
    i = i + 1
moreInfo = input("Enter the number of the player you want more information on: ")
while not moreInfo.isdigit() or int(moreInfo) < 1 or int(moreInfo) > len(names):
    moreInfo = input("Invalid input. Please enter a number between 1 and {len} ".format(len=len(names)))
moreInfo = int(moreInfo) - 1
id = names[moreInfo][0]
print("You have beaten the following players: ")
cursor.execute("SELECT tag FROM player WHERE id IN (SELECT loserid FROM sets2 WHERE winnerid = %s)", (id,))
names = cursor.fetchall()
wins = 0
for name in names:
    wins = wins + 1
    print(name[0])
print("You have lost to the following players: ")
cursor.execute("SELECT tag FROM player WHERE id IN (SELECT winnerid FROM sets2 WHERE loserid = %s)", (id,))
names = cursor.fetchall()
losses = 0
for name in names:
    losses = losses + 1
    print(name[0])
print("You have won {wins} games and lost {losses} sets.".format(wins=wins, losses=losses))
print("Your overall winrate is {:.2f}%".format((wins/(wins+losses))*100))
