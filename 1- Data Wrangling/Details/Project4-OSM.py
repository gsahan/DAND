
# coding: utf-8

# ## Open Street Map Project

# Author : Görkem Berk Şahan 

# Map Area : Istanbul 
# 
# https://mapzen.com/data/metro-extracts/metro/istanbul_turkey/

# Creating an sample file with source code from udacity.

# In[1]:

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow

OSM_FILE = "istanbul_turkey.osm"  # Replace this with your osm file
SAMPLE_FILE = "sample.osm"

k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
pass

""" this code block was closed,
    if needed you should set true """

if False :
    with open(SAMPLE_FILE, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')

        # Write every kth top level element
        for i, element in enumerate(get_element(OSM_FILE)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))

        output.write('</osm>')


# After take a look sample data, we can easyly see some problems

# In[2]:

import re

sample_file = "sample.osm"

street_re = re.compile("\w+.(?P<short>.+\.)?",re.IGNORECASE)# if there is an dot(.), so it may be an short of street, etc...
short_streets = set() # distict street names that has shorten

post_code_re = re.compile("(\d\d\d\d\d)")# all post codes must be 5 digit
invalid_postcodes = set()

city_name_re = re.compile("\w",re.IGNORECASE) # city name is an word, if not we should take a look
invalid_citynames = set()

for event, elem in ET.iterparse(sample_file, events=("start",)):
        etag = elem.tag
        
        if etag == "node" or etag == "way":
            
            for tag in elem.iter("tag"):
                key = tag.attrib['k']
                value = tag.attrib['v']
                
                if  key == "addr:street": # street names 
                    mch = street_re.match(value)
                    if mch  and mch.group('short') != None:                        
                        short_streets.add(mch.group('short')) # distinct shorten street names
                        #print tag.attrib['v'],'---',mch.group('short')
                if key == "addr:postcode": # post codes chacking
                        mch = post_code_re.match(value)
                        if not mch:
                            invalid_postcodes.add(value)      
                if key == "addr:city":
                        mch = city_name_re.match(value)
                        if not mch:
                            invalid_citynames.add(value)

print "\n\n>>TAKE A LOOK STREETS : "
print "\n".join(short_streets)
print "\n"
print "\n"
print "\n>>INVALID POST CODES :"
print "\n".join(invalid_postcodes)                       
print "\n"
print "\n"
print "\n>>INVALID CITY NAMES :"
print "\n".join(invalid_citynames)    


# ## 1. Problems Encountered In Map Data

#     a. Some street names shorten like below ; 
#         Sokak as Sok.,Sk. 
#         Cadde as Cd., Cad.
#         Mahalle as Mah.
#         Bulvar as Bulv.
#     b. There is invalid Post codes like 3400
#     c. Some city names has county names with city name like Üsküdar/İstanbul so "/" or " "(space) used as delimeter and one of its items is city name and other one is county.
#     d. City names is not same format such as camel case ( Istanbul or ISTANBUL )  

# ## 2. Cleaning Data and Creating Json File and MongoDb

# After audit data, some desicions to clean data is like that;
# * Street names has shorten values, correct them
# * Turkish characters is a open issue for compare,group beacuse some users use traditional char but some doesnt, so we clear it to english chars.
# * Some address values is inconsistent, such as it contains county instead city in city key, correct it if we know the true one
# * Some street values has an website address so we clear it
# * Some postcodes is inconsistent of standart postcode, for ex. postcodes of Istanbul city must start 34 , so we can check it
# 

# In[32]:

import json
import pymongo

jsonFile = 'istanbul_turkey.osm.json'
fl = open(jsonFile,'a')# we dont forget to close this file ...


constr = 'localhost:27017'
client = pymongo.MongoClient(constr)
db = client.OSMDB




map_Street = {
    "Sok.":"Sokagi ",
    "Sk.":"Sokagi ",
    "Cad.":"Caddesi",
    "Cd.":"Caddesi ",
    "Mah.":"Mahallesi ",
    "Mh.":"mahallesi ",
    "Bulv.":"Bulvari "
    
} # to use replacement shorten

# turkish chars cause problem when comparing, so I changed them
def clearTurkishCharacters(word):
    list = {"İ":"I",
            "ı":"i",
            "ö":"o",
            "Ö":"O",
            "ş":"s",
            "Ş":"S",
            "ü":"u",
            "Ü":"U",
            'Ğ':'G',
            'ğ':'g',
            'ç':'c',
            'Ç':'C'
           }
    for l in list:
        word = word.replace(l.decode('utf-8'),list[l])
    return word

def correctStreet(name):
    if name.find('.com') != -1 or  name.find('www.') != -1:
        return None
        
    n = name
    for k in map_Street:
        n = n.replace(k,map_Street[k])
    return clearTurkishCharacters(n.strip().title())

#street names has slash "/" so it or space " " it is delimeter for as an we seach this city names :
#after take a look data with mongodb I created below list
city_names = {'istanbul' : 'istanbul',
              'kocaeli':'kocaeli',
              'gebze':'kocaeli',
              'avcilar':'istanbul',
              'sariyer':'istanbul',
              'beylikduzu':'istanbul',
              'sancaktepe':'istanbul',
              'cekmekoy':'istanbul',
              'beyoglu':'istanbul',
              'bakirkoy':'istanbul',
'sultanbeyli' : 'istanbul',
'pendik' : 'istanbul',
'kadikoy' : 'istanbul',
'sisli' : 'istanbul',
'tuzla' : 'istanbul',
'esenyurt' : 'istanbul',
'uskudar' : 'istanbul',
'sile' : 'istanbul',
'atasehir' : 'istanbul',
'istambul' : 'istanbul',
'kartal' : 'istanbul',
'kagithane' : 'istanbul',
'heybeliada' : 'istanbul',
'maltepe' : 'istanbul',
'dilovasi' : 'istanbul',
'sultanahmet' : 'istanbul',
'bahcelievler mahallesi' : 'istanbul',
'yenibosna' : 'istanbul',
'bayrampasa' : 'istanbul',
'darica' : 'istanbul',
'kilyat' : 'istanbul',
'fatih-istanbul' : 'istanbul',
'basaksehir' : 'istanbul',
'cayirova' : 'istanbul',
'ora' : 'istanbul',
'umraniye' : 'istanbul',
'zeytinburnu' : 'istanbul',
'kavacik' : 'istanbul',
'istanbbul' : 'istanbul',
'buyukada' : 'istanbul',
'besiktas' : 'istanbul',
'selinpasa' : 'istanbul',
'umraniye/istanbu' : 'istanbul',
'rumeli' : 'istanbul',
'eyup' : 'istanbul',
'elmadag/sisli' : 'istanbul',
'sekerpinar' : 'istanbul',
'istanbus' : 'istanbul',
'balat' : 'istanbul',
'kumburgaz' : 'istanbul',
'topkapi' : 'istanbul'
       } # and other is county i think

def correctCityName(name):
    if name.find('/') != -1:
        citydata = [clearTurkishCharacters (x.lower().strip()) for x in name.split('/')] 
        for cn in city_names:
            if cn in citydata:
                return city_names[cn].strip().title()
                
            
    if name.find(' ') != -1:
        citydata = [clearTurkishCharacters(x.lower().strip()) for x in name.split(' ')]
        for cn in city_names:
            if cn in citydata:
                return city_names[cn].strip().title()
            
    val = clearTurkishCharacters(name.lower()) 
    
    if val in city_names:
        return city_names[val].strip().title()
    else :
        return val.strip()

def correctPostcode (code,row):
    if 'addr' in row and 'city' in row['addr']:
        curCity = row['addr']['city']
        
        
        if curCity is None and len(code) == 5:
            #print "okkkk Postcode : ",code,curCity
            return code
        elif curCity == 'Istanbul' and code[0:2] == '34' and len(code) == 5:
            #print "ok Postcode : ",code,curCity
            return code
        elif curCity == 'Kocaeli' and code[0:2] == '41' and len(code) == 5:
            #print "ok Postcode : ",code,curCity
            return code
        else:
            #print "incorrect Postcode : ",code,curCity
            return None

# we are going to user data model like this, this model is selected in lessons ;

"""
{
"id": "2406124091",
"type: "node",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
}


"""
created_keys = [  "version",
                  "changeset",
                  "timestamp",
                  "user",
                  "uid"]

dataTable = []


#sample_file 
for event, e in ET.iterparse(OSM_FILE , events=("start",)):
        etag = e.tag
        if etag in ['node','way']:
            
            dataRow = {}
            
            id =  e.attrib['id'] 
            type = e.tag
            
            if "lat" in e.attrib and 'lon' in e.attrib:
                pos = [e.attrib['lat'] , e.attrib['lon'] ]
                dataRow['pos'] = pos
            
            created = {}
            
            if created_keys:
                for i in created_keys:
                    created[i] = e.attrib[i]
                dataRow['created'] = created
                
            else:
                print e,"eksik created bilgisi"
                
            dataRow['id'] = id
            dataRow['type'] = type
            
            
            
            """ 
                we re going to add tag's key-value to our data model, if there is key:child : value so we are going to
                handle it 
            """
            for tag in e.iter("tag"):
                key =  tag.attrib['k']
                value =  tag.attrib['v']
                
                if key.find(':') != -1: # if key has ":" so it has a value for same prop's another child 
                    keys= key.split(':')
                    
                    parentKey = keys[0]
                    childKey =  keys[1]
                    
                    #corrections ---------------------------
                    if childKey == 'city':
                        value = correctCityName(value)
                    elif childKey == 'street':                        
                        value = correctStreet(value)
                    elif childKey == 'postcode':
                        value = correctPostcode(value,dataRow)
                        
                    #end corrections -----------------------
                    if parentKey in dataRow:
                        if isinstance(dataRow[parentKey],basestring): # if same key has and it is str so it was default
                            dataRow[parentKey] = {'default':dataRow[parentKey], childKey: value }
                    else:
                        dataRow[parentKey] = {childKey:value}
                else:
                    dataRow[key] = clearTurkishCharacters(value)
                    
            #db.osmMapData.insert_one(dataRow) # insert data to MongoDB
            #dataTable.append(dataRow) # to write json file 
#json.dump(dataTable , fl) write it
                        
                            
fl.close()
    
                    
            
            
        


# ### suggestions for improving the data 
# 
# When we look data structure, we can see that tag values kept as parentkey:childkey and value, and if there is no child value so it kept as key:value so taking this data take more time, and as I understand there is no data validation for example if city name contains special characters / or - , it may be asking user to confirm this is true.

# ## 2- Data Overview
# <table style="width:100%">
# <tr>
# <td>
# istanbul.osm      file 252 MB 
# </td>
# <td>
# istanbul.osm.json file 274 MB
# </td>
# </tr>
# </table>

# In[39]:



rs = db.osmMapData.distinct("created.uid")
print "Unique user count : ",len(rs)


print "\nnode and way count"
rs = db.osmMapData.aggregate([{"$match":{ "type":{ "$in":["way","node"]} }},{"$group":{"_id":"$type","count":{"$sum":1}}},{"$sort":{"count":-1}}])

for r in rs:
    print r
    
print "\ncity counts"
rs = db.osmMapData.aggregate([{"$group":{"_id":"$addr.city","count":{"$sum":1}}},{"$sort":{"count":-1}}])

for r in rs:
    print r
    
print "\ntop streets accourding to its data count "    
rs = db.osmMapData.aggregate([{"$match":{"type":{"$in":["node","way"]}}},{"$group":{"_id":"$addr.street","count":{"$sum":1}}},{"$sort":{"count":-1}},{"$limit":10}])
for r in rs:
    print r 


# ## 3- Additional Ideas

# In[72]:

import pandas as pd


rs = db.osmMapData.aggregate( [{"$group":{ "_id":"$created.user","count":{"$sum":1} }},{"$sort":{"count":-1}} ])

ls = list(rs)
df = pd.DataFrame(ls)

print df.describe()

rs = db.osmMapData.aggregate( [{"$group":{ "_id":"$created.user","count":{"$sum":1} }},{"$sort":{"count":-1}} ,{"$limit":10}])
ls = list(rs)
df = pd.DataFrame(ls)
print "\n\nTop 10 users"
print df.describe()

rs = db.osmMapData

recordCnt = rs.count()
print "\n\ntotal count : ",recordCnt,"\n\n"

rs = db.osmMapData.aggregate( [{"$group":{ "_id":"$created.user","count":{"$sum":1} }},{"$sort":{"count":-1}} ,{"$limit":10}])

for r in rs:
    print r['_id'], "added about " ,int(r['count']/float(recordCnt)*100 ),"% of total points"


# * Top user Nesim has added 90043 points 6% of total points 
# * Top 10 users has added 32% of all points

# ## Conclusion
# 
# After this analysis, we can see that data that inserted by users couldnt be validated. Even if clean data , some city or street data is incorrect.There are so many case to check data if really work long time on this. OSM must collect  validation rules like data, so data will be clean and standart.





