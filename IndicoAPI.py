import ast
import datetime
import hashlib
import hmac
import json
import time
import urllib.request
from datetime import timedelta

from graphqlclient import GraphQLClient

param = "limit=500"
key = "aeb5e3b6-e5d5-4108-b91f-3e7c3df265ef"
s_key = b'3531b5c1-bc7b-4129-9de7-e5f05a2f32a7'
client = GraphQLClient('http://0.0.0.0:51438/')


def getUrl(type, id):
    path = str(type) + "/" + str(id) + ".json"
    string = "/export/" + path + "?ak=" + key + "&" + param + "&timestamp=" + str(int(time.time()))
    sha = hmac.new(s_key, string.encode(), hashlib.sha1).hexdigest()
    url = "https://indico.cern.ch" + string + "&signature=" + sha
    # print(url)
    return url


def getData(ID, type):
    url = getUrl(type, ID)
    with urllib.request.urlopen(url) as url:
        data = json.loads(url.read().decode())

    return data


def deleteDB():
    client.execute(
        '''mutation {
        DeleteDB(command: "delete")
    }''')
    # print("done")


def setCategoryI(id):
    data = getData(id, "categ")

    client.execute(
        '''mutation{
            CreateCategory( id: \"''' + str(data["results"][0]["categoryId"]) + '''\" name:  \"''' + str(
            data["results"][0]["category"]) + '''\"){
                            id
                        }
                    }'''
    )


def setCategoryN(id, name):
    client.execute(
        '''mutation{
            CreateCategory( id: \"''' + str(id) + '''\" name:  \"''' + name + '''\"){
                                id
                            }
                        }'''
    )


def setEventWithCateg(id, categ):
    data = getData(id, "event")
    try:
        name = str(data["results"][0]["title"])
    except:
        name = ""
    try:
        description = str(data["results"][0]["description"]).replace("\n", " ").replace("\r", " ").replace("\"", "\\\"")
    except:
        description = ""
    try:
        startDate = datetime.datetime.strptime(data["results"][0]["startDate"]["date"], '%Y-%m-%d')
    except:
        startDate = datetime.datetime.strptime("0000-00-00", '%Y-%m-%d')
    try:
        endDate = datetime.datetime.strptime(data["results"][0]["endDate"]["date"], '%Y-%m-%d')
    except:
        endDate = datetime.datetime.strptime("0000-00-00", '%Y-%m-%d')
    now = datetime.datetime.now()
    client.execute('mutation {CreateEvent(id: \"' + str(id) + '\" name: \"' + str(name) + '\" created: {year:' + str(
        now.year) + 'month: ' + str(now.month) + 'day: ' + str(now.day) + '} startDate: {year:' + str(
        startDate.year) + ' month: ' + str(startDate.month) + ' day: ' + str(startDate.day) + '} endDate: {year:' + str(
        endDate.year) + 'month: ' + str(endDate.month) + 'day: ' + str(
        endDate.day) + '}  description: \"' + description + '\"){name }}')
    if categ:
        exists = client.execute(
            '''query{
                Category(id: \"''' + str(data["results"][0]["categoryId"]) + '''\"){
                                    id
                                }
                            }'''
        )
        print(exists)
        exists = ast.literal_eval(exists)
        print(exists["data"]["Category"] == [])
        if exists["data"]["Category"] == []:
            setCategoryN(data["results"][0]["categoryId"], data["results"][0]["category"])
    client.execute('''
        mutation{
            AddCategoryFrom_Event(from:{id: \"''' + str(
        data["results"][0]["id"]) + '''\"}, to: {id: \"''' + str(data["results"][0]["categoryId"]) + '''\"}){
                from{name}
                to{name}
            }
        }''')


def createAllEventsOfCateg(id):
    data = getData(id, "categ")
    setCategoryN(id, data["results"][0]["category"])
    results = data["results"]
    i = 0
    while i < len(results):
        nextEvent = results[i]["id"]
        exists = client.execute(
            '''query{
                Event(id: ''' + str(nextEvent) + '''){
                    id
                }
            }'''
        )

        exists = ast.literal_eval(exists)

        if exists["data"]["Event"] == []:
            setEventWithCateg(nextEvent, False)

        setItem(str(nextEvent))
        i += 1


def setItem(ID):
    startDate = datetime.datetime.strptime(getData(ID, "event")["results"][0]["startDate"]["date"], '%Y-%m-%d').date()
    endDate = datetime.datetime.strptime(getData(ID, "event")["results"][0]["endDate"]["date"], '%Y-%m-%d').date()

    timetable = getData(ID, "timetable")["results"][ID]

    while True:

        while str(timetable[str(startDate).replace("-", "")])[2:10] != "":
            var = timetable[str(startDate).replace("-", "")]
            var2 = var[str(var)[2:10].replace("'", "")]

            start = datetime.datetime.strptime(str(var2["startDate"]["date"]) + "-" + str(var2["startDate"]["time"]),
                                               "%Y-%m-%d-%H:%M:%S")
            end = datetime.datetime.strptime(str(var2["endDate"]["date"]) + "-" + str(var2["endDate"]["time"]),
                                             "%Y-%m-%d-%H:%M:%S")
            # print(start)
            # print(end)
            # print(var2)

            client.execute('''
                    mutation{
                        CreateItem(
                            id: \"''' + str(var)[2:10] + '''\" 
                            name: \"''' + str(var2["title"]).replace("\n", " ").replace("\r", " ").replace("\"",
                                                                                                           "\\\"") + '''\" 
                            description: \"''' + str(var2["description"]).replace("\n", " ").replace("\r", " ").replace(
                "\"", "\\\"") + '''\" 
                            starts: {year: ''' + str(start.year) + ''' 
                                    day: ''' + str(start.day) + ''' 
                                    month: ''' + str(start.month) + ''' 
                                    hour: ''' + str(start.hour) + '''
                                    minute: ''' + str(start.minute) + '''
                                    second: ''' + str(start.second) + '''
                                    } 
                            ends: {year: ''' + str(end.year) + ''' 
                                    day: ''' + str(end.day) + ''' 
                                    month: ''' + str(end.month) + ''' 
                                    hour: ''' + str(end.hour) + '''
                                    minute: ''' + str(end.minute) + '''
                                    second: ''' + str(end.second) + '''
                                    } 
                        ) 
                        { 
                        name 
                        } 
                    } 
                ''')
            # print("done2")
            """ client.execute('''
                mutation{

                }
            ''')"""

            client.execute('''
                mutation{
                    AddEventFrom_Item(
                    from:{id: \"''' + str(var)[2:10] + '''\"},
                    to: {id: \"''' + str(var2["conferenceId"]) + '''\"})
                     {         
                      from{name}
                      to{name} 
                } }     
            ''')

            try:
                while str(var[str(var)[2:10]]["entries"]) != "":
                    var3 = var[str(var)[2:10]]["entries"][str(var[str(var)[2:10]]["entries"])[2:10]]

                    start = datetime.datetime.strptime(
                        str(var3["startDate"]["date"]) + "-" + str(var3["startDate"]["time"]), "%Y-%m-%d-%H:%M:%S")
                    end = datetime.datetime.strptime(str(var3["endDate"]["date"]) + "-" + str(var3["endDate"]["time"]),
                                                     "%Y-%m-%d-%H:%M:%S")

                    # print(start)
                    # print(end)

                    client.execute('''
                        mutation{
                        CreateItem(
                            id: \"''' + str(var[str(var)[2:10]]["entries"])[2:10] + '''\" 
                            name: \"''' + str(var3["title"]).replace("\n", " ").replace("\r", " ").replace("\"",
                                                                                                           "\\\"") + '''\" 
                            description: \"''' + str(var3["description"]).replace("\n", " ").replace("\r", " ").replace(
                        "\"", "\\\"") + '''\" 
                            starts: {year: ''' + str(start.year) + ''' 
                                    day: ''' + str(start.day) + ''' 
                                    month: ''' + str(start.month) + ''' 
                                    hour: ''' + str(start.hour) + '''
                                    minute: ''' + str(start.minute) + '''
                                    second: ''' + str(start.second) + '''
                                    } 
                            ends: {year: ''' + str(end.year) + ''' 
                                    day: ''' + str(end.day) + ''' 
                                    month: ''' + str(end.month) + ''' 
                                    hour: ''' + str(end.hour) + '''
                                    minute: ''' + str(end.minute) + '''
                                    second: ''' + str(end.second) + '''
                                    } 
                        ) 
                        { 
                        name 
                        } 
                    } 
                    ''')
                    # print("done3")
                    client.execute('''
                                    mutation{
                                        AddItemTo_Item(
                                        from:{id: \"''' + str(var[str(var)[2:10]]["entries"])[2:10] + '''\"},
                                        to: {id: \"''' + str(var)[2:10] + '''\"})
                                         {         
                                          from{name}
                                          to{name} 
                                    } }     
                                ''')

                    var[str(var)[2:10]]["entries"].pop(str(var[str(var)[2:10]]["entries"])[2:10])


            except:
                pass
            var.pop(str(var)[2:10].replace("'", ""))

        if startDate == endDate:
            break
        startDate = startDate + timedelta(days=1)

    return


#deleteDB()
#createAllEventsOfCateg(5885)
#setEventWithCateg(776816, True)
print(getUrl("timetable", "776816"))
#setItem("776816")
# print("done")

# getUrl("user", "c1ef3a38fe0c9aa11f1f4794f41b59a3")
#getUrl("roomName/CERN", "BE Auditorium Meyrin")
#print(getUrl("categ", 9333))
