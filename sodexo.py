import requests
from bs4 import BeautifulSoup
import json
from splitwise import Splitwise
import datetime
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
import random
import re
import config
#import logging
#logging.basicConfig(level=logging.DEBUG)

session = requests.Session()


MONTHS = {'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4,  'MAI': 5,  'JUN': 6,
          'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12}
sodexo = []
splitwise = []

url_login = f"https://login.sodexobeneficios.pt/login_processing.php?nif={config.nif}&pass={config.password}&reg=true&_=1648293456682"
url_conta = f"https://minhaconta.sodexobeneficios.pt/?days={config.days}"

response = session.request("GET", url_login)
response = session.request("GET", url_conta)
soup = BeautifulSoup(response.text, 'html.parser')
table_data = [[cell.text.strip() for cell in row("td")]
              for row in soup.find_all("tr")]

for data in table_data:
    if len(data) > 2:
        if not ("-" not in data[2] or "CARREGAMENTO DE BENEF" in data[1] or "ENT:" in data[1]):
            buy = {}
            date = data[0].split()
            desc = " ".join(data[1].split())
            buy["date"] = f"{datetime.date.today().year}-{str(MONTHS[date[0]]).zfill(2)}-{str(date[1]).zfill(2)}"
            buy["desc"] = re.sub("COMPRA \\d+", "", f"SODEXO -{desc}")
            buy["price"] = str(
                float(data[2].replace("\u20ac -", "").replace(',', '.')))
            sodexo.append(buy)
            # buy[""]

print(sodexo)
sObj = Splitwise(config.consumer_key,config.consumer_secret,api_key=config.api_key)

start_date = datetime.datetime.now() - datetime.timedelta(config.days)
current = sObj.getExpenses(group_id=config.groupId, dated_after=start_date.isoformat(), visible=True, limit=50)
for curr in current:
    for user in curr.getUsers():
        if user.getId() == config.beatrizId and float(user.getPaidShare()) == 0:
            buy = {}
            date = datetime.datetime.strptime(
                curr.getDate(), "%Y-%m-%dT%H:%M:%SZ")
            buy["date"] = date.strftime('%Y-%m-%d')
            buy["desc"] = curr.getDescription()
            buy["price"] = curr.getCost()
            print(curr.getDescription())
            splitwise.append(buy)

print("---------")
print(splitwise)
print("---------")

for tran in sodexo:
    if tran not in splitwise:
        print(f"adding {tran}")
        owedShareBeatriz  = round(float(tran["price"])/2, 2)
        owedShareValverde = owedShareBeatriz

        if owedShareBeatriz*2 > float(tran["price"]):
            if random.choice([True, False]):
                owedShareBeatriz = owedShareBeatriz - 0.01
            else:
                owedShareValverde = owedShareValverde - 0.01
        elif owedShareBeatriz*2 < float(tran["price"]):
            if random.choice([True, False]):
                owedShareBeatriz = owedShareBeatriz + 0.01
            else:
                owedShareValverde = owedShareValverde + 0.01
        
        #print(owedShareBeatriz)
        #print(owedShareValverde)
        #print(owedShareBeatriz*2)
        expense = Expense()
        expense.setCost(tran["price"])
        expense.setDescription(tran["desc"])
        expense.setGroupId(config.groupId)
        expense.setDate(tran["date"])

        user1 = ExpenseUser()
        user1.setId(config.beatrizId)
        user1.setPaidShare('0.00')
        user1.setOwedShare(owedShareBeatriz)

        user2 = ExpenseUser()
        user2.setId(config.delfimId)
        user2.setPaidShare(tran["price"])
        user2.setOwedShare(owedShareValverde)

        users = []
        users.append(user1)
        users.append(user2)

        expense.setUsers(users)
        expense, errors = sObj.createExpense(expense)
        if errors:
            print(errors.getErrors())
        print(expense.getDescription())
