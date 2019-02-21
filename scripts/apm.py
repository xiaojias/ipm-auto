#!/usr/bin/env python3
# -*- coding:utf8 -*-
'''
xiaojias@cn.ibm.com
###################################################################
# changes :                                                       #
# 201xxxxx-XJS : Perform actions through API                      #
# 20190218-XJS : Add to support on-prem on HTTP&HTTPS             #
###################################################################

'''
# perform actions through API, for specific subscription

import sys, os.path, datetime
import requests      # replace http module to support https for onprem
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import base64
import json
import re
import pprint

script = os.path.basename(__file__)
def usage():
    print("Usage is:")
    print("%s -s <subscription name> -a <action> [-o <directory>] [-p <pname1>=<pvalue1>[,<pname2>=<pvalue2]]" % script )
    print("-s <subscription name> the short name of subscription name which should have been defined in config/credential.json")
    print("-a <action>  specifies the performing action which should have been defined in config/apiactions.json")
    print("-o <directory>  [optional] specifies where the outfiles will be stored, defaul is ./tmp")
    sys.exit(1)

def errorMessage(message):
    print("Error:%s" % message)
    sys.exit(1)

def readListFromJson(filename):
    with open(filename, "r") as f:
        l = json.load(f)
    return(l)

def readIDfrommgmt_artifactstoList(filename):
    #read _id from the output of href of: /1.0/topology/mgmt_artifacts
    f = open(filename, "r")
    data = f.read()
    jsonobj = json.loads(data)
    
    ids = jsonobj["_items"]
    list_id = []
    for v in ids:
        list_id.append(v["_id"])
    # all the _ids are listed in list_id object
    return(list_id)

def getCredential(name, filename="config/credential.json"):
# Validate the APM subscription configuration, and return the values if valid
    l = readListFromJson(filename)
    for d in l:
        if d.get("Subscription") == name:
            #to check if the necessary info are included
            if d.get("Type"):
                if d.get("Type") == "cloud":
                    if d.get("User") and d.get("Password") and d.get("Service_Location"):
                        if d.get("Subscription_id") or (d.get("Client_ID") and d.get("Client_Secret")):
                            return(d)
                        else:
                            errorMessage("Missing configuration for subscription(%s)" % name)
                elif d.get("Type") == "onprem":
                    if d.get("User") and d.get("Password") and d.get("Protocol") and d.get("Server") and d.get("Port"):
                        return(d)
                    else:
                        errorMessage("Missing configuration for subscription(%s)" % name)
            else:
                errorMessage("Missing configuration for subscription(%s)" % name)

    # Capture the configuration data
    names = ""
    for d in l:
        names += "  " + d.get("Subscription")
    errorMessage("Subscription of %s is not supported or not correctly defined(%s)" % (name, names))

def getApiAction(name, filename="config/apiactions.json"):
    # Validate the API calls configuration, and return the values if valid
    l = readListFromJson(filename)
    for d in l:
        if d.get("name") == name:
            if d.get("status") == "available":
                return(d)
    # Capture the API call configuration data
    names = ""
    for d in l:
        names += "  " + d.get("name")
    errorMessage("action of %s is NOT available of now (%s)" % (name, names))

def validParaIncmdinfo(info):
    #to check if all the parameters defined in key of "hrefp" are provided in dict of info
    if info.get("hrefp"):
        l = info["hrefp"].split(",")
        notl = ""
        for k in l:
            if not info.get(k):
                notl += " %s" % k
        if notl:
            errorMessage('''The parameter/s of "%s" must be provided in either .json file or command''' % notl)

def apiCommand(sub, cmd, filename):
# both sub and action are type of dictionary data, they include subscription and action information respectively
    T = True
    f = open(filename, "w")
    
    headers = {
        'content-type': "application/json",
        'accept': "application/json",
        }
    base64string = base64.b64encode(("%s:%s" % (sub.get("User"), sub.get("Password"))).encode()).decode()
    headers['authorization'] = "Basic %s" % base64string

    # disable https warnings
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Process depends on APM type (cloud or onprem)
    if sub.get("Type"):
        if sub.get("Type") == "cloud":
            if sub.get("Client_ID") and sub.get("Client_Secret"):
                headers['x-ibm-service-location'] = sub.get("Service_Location")
                headers['X-IBM-Client-Id'] = sub.get("Client_ID")
                headers['X-IBM-Client-Secret'] = sub.get("Client_Secret")

                hostURL = "https://api.ibm.com"
                hrefPrefix = "/perfmgmt/run"
                href = "%s%s" % (hrefPrefix, cmd["href"])

            elif sub.get("Subscription_id"):
                hostURL = "https://%s.customers.%s.apm.ibmserviceengage.com" % (sub.get("Subscription_id"), sub.get("Service_Location"))
                href = cmd["href"]

            else:
                errorMessage("Credential info is missing ")
        elif sub.get("Type") == "onprem":
            href = cmd["href"]


            if sub.get("Protocol") == "http":                # for HTTP connection
                hostURL = "http://%s:%s" % (sub.get("Server"), sub.get("Port"))
            elif sub.get("Protocol") == "https":
                hostURL = "https://%s:%s" % (sub.get("Server"), sub.get("Port"))
            else:
                errorMessage("Protocol type is wrong.")
        else:
            errorMessage("APM type is wrong.")
    else:
        errorMessage("APM type is missing.")

    #update the href by writing parameter/s into
    if cmd.get("hrefp"):
        pnames = cmd.get("hrefp").split(",")
        for pname in pnames:
            pvalue = cmd[pname]
            href, number = re.subn(pname, pvalue, href)
    if cmd["action"] == "GET":
        if cmd.get("description"):
            print("Running for ...: %s" % cmd["description"])
        else:
            print("Running for ...: %s" % cmd["name"])

    elif cmd["action"] == "POST":
        filename = cmd["sample"]
        f = open(filename, "r")
        data = json.loads(f.read())
        data_string = json.dumps(data)
        f.close()
        
        if cmd.get("hrefp"):
        #update data_string by writing parameter/s into
            pnames = cmd.get("hrefp").split(",")
            for pname in pnames:
                pvalue = cmd[pname]
                data_string, n = re.subn(pname, pvalue, data_string)
        if cmd.get("description"):
            print("Running .... for: %s" % cmd["description"])
        else:
            print("Running .... for: %s" % cmd["name"])
    
        #conn.request("POST", href, body=data_string, headers=headers)
        # To be changed to use requests
    elif cmd["action"] == "DELETE":
        pass
    else:
        errorMessage("action of %s is not supported" % cmd["action"])
    
    r = requests.get("%s%s" % (hostURL, href), headers=headers, verify=False)
    #r = requests.get("%s%s" % (hostURL, href), headers=headers)
    if r.status_code == 200:
        f.write(r.text)
        print("Successful, the information is gotten")
    elif r == 201:
        print("Successful, the resource of %s is created" )
    else:
        print('Error: failed!\nStatus code: ' + str(r.status_code) + '\nResponse: ' + r.text + '\nExiting...')
        T = False
    f.close()
    return(T)

def convertJsonToTxt(filename):
    pass

def refineJsonFile1(filename):
    #process the file likes for "returnAllGroups" action
    print("refining the format of %s" % filename)
    f = open(filename, "r")
    data = f.read()
    jsonObj = json.loads(data)

    objects = jsonObj["_items"]
    dataString = json.dumps(objects, sort_keys=True, indent=4)
    f.close

    f = open(filename,"w")
    f.write(dataString)
    f.close()
    return(filename)

def print_json_threshold(filename):
    #generate the .json and .json.long file in the same location
    f = open(filename, "r")
    data = f.read()
    jsonobj = json.loads(data)

    thresholds = jsonobj["_items"]
    threshold = thresholds[0]

    new_threshold = {}
    new_threshold["configuration"] = threshold["configuration"]
    new_threshold["description"] = threshold["description"]
    new_threshold["label"] = threshold["label"]
    f.close()
    
    long_file = os.path.dirname(filename) + "/%s.json.long" % threshold["label"]
    short_file = os.path.dirname(filename) + "/%s.json" % threshold["label"]

    f = open(long_file, "w")
    jsonobj = json.dumps(jsonobj, indent=4)
    f.write(jsonobj)
    f.close()

    f = open(short_file, "w")
    jsonobj = json.dumps(new_threshold, indent=4)
    f.write(jsonobj)
    f.close()
    print("Both .json and .json.long files are created for %s in %s" % (threshold["label"], os.path.dirname(filename)))

def processJsonForEveryaction(filename, aname):
    action = aname
    if action in ["returnAllGroups", "returnAllAgents"]:
    # ._items contains the required contents
        f = refineJsonFile1(filename)
    elif  action in ["returnThresholdBasedonLabel"]:
    # refine the format only
        #refineJsonFile1(f)
        #TBD
        # will rename the file and change its contents
        f = print_json_threshold(filename)
    return(f)

def getArgvDic(argv):
    optd = {}
    optd["script"] = argv[0]
    argv = argv[1:]
    while argv:
        if len(argv) >= 2:
            optd[argv[0]] = argv[1]
            argv = argv[2:]
        else:
            usage()
    return(optd)

def main():
    argv = sys.argv
    mydict = getArgvDic(argv)
    #print(mydict)
    para = ["script", "-s", "-h", "-a", "-p", "-o"]
    for key in mydict:
        if not key in para:
            print("%s is not supported!!!" % key)
            usage()

    if not (mydict.get("-s") and mydict.get("-a")):    #required parameters
        usage()
     
    subname, action = (mydict["-s"], mydict["-a"])

    outdir = mydict["-o"] if mydict.get("-o") else "./tmp"
    addps = mydict["-p"] if mydict.get("-p") else ""
    
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    outfile = os.path.join(outdir, "apm.json")   #by default

    subFile = "config/credential.json"
    actionFile = "config/apiactions.json"
    if not (os.path.isfile(subFile) or os.path.isfile(actionFile)):
        errorMessage("Configuration file/s is/are missing")

    subinfo = getCredential(subname, subFile)   
    #return a dictionary data includes: Type, Client_Secret,Client_ID,Service_Location,user & password
                                 #or :Type, Subscription_id,          Service_Location,user & password
    cmdinfo = getApiAction(action, actionFile)
    #return the definition for 'action" to a dict type data
    #write the Additional parameters (provided in command) into dict of cmdinfo
    if addps:
        addp = addps.split(",")
        p = re.compile(r'(?P<k>(.)+)=(?P<v>(.)+)')
        for s in addp:
            a = p.match(s)
            cmdinfo[a.group("k")] = a.group("v")
    if action == "returnThresholdBasedonList" or action == "returnResourcesBaseonList" :
        #from the listfile, to create a list type of data for "thresholdname" in cmdinfo
        tlist = []
        if not cmdinfo.get("listfile"):
            print("Parameter of listfile is required !!!")
            sys.ejxit(1)
        f = open(cmdinfo["listfile"], "r")
        for line in f.readlines():
            tlist.append(line.strip("\n").strip())        
        f.close()

        tlist_succ = []
        tlist_fail = tlist[:]

        for tname in tlist:
            if action == "returnThresholdBasedonList":
                cmdinfo["thresholdname"] = tname
            elif action == "returnResourcesBaseonList":
                cmdinfo["resourceID"] = tname

            validParaIncmdinfo(cmdinfo)
            outfile = os.path.join(os.path.dirname(outfile), "%s.json" % tname)   #rename the filename

            successOrnot = apiCommand(subinfo, cmdinfo, outfile)
            if successOrnot:
                print("Succcess on %s" % tname)
                tlist_succ.append(tname)
                tlist_fail.remove(tname)
        if not tlist_fail:
            print("Successfull on all")
        else:
            f_succ = "%s.succ" % cmdinfo["listfile"]
            f = open(f_succ, "w")
            for i in tlist_succ:
                f.write(i)
                f.write("\n")
            f.close()
           
            print("Failed on some in %s.fail " % cmdinfo["listfile"])
            f_fail = "%s.fail" % cmdinfo["listfile"]
            f_fail = open(f_fail, "w")
            for i in tlist_fail:
                f.write(i)
                f.write("\n")
            f.close()
    elif action == "returnAllResources":
        #get all the resources'id first
        href_bak = cmdinfo["href"]
        cmdinfo["href"] = "/1.0/topology/mgmt_artifacts/"
        cmdinfo["resourceID"] = ''
        if not apiCommand(subinfo, cmdinfo, outfile):
            sys.exit(1)

        cmdinfo["href"] = href_bak
        alist = []
        alist = readIDfrommgmt_artifactstoList(jsonFile)
        
        for v in alist:
            cmdinfo["resourceID"] = v
            outfile = os.path.join(os.path.dirname(outfile), "%s.json" % v)
            successOrnot = apiCommand(subinfo, cmdinfo, outfile)

            if successOrnot:
                print("%s is created" % outfile)
    elif action in {"returnAllThresholds", "returnAllRelation"}:
        #run first, and then run again with "_next" instead of "href" parameter
        validParaIncmdinfo(cmdinfo)
        successOrnot = apiCommand(subinfo, cmdinfo, outfile)
        objAll = {}
        objAll["_items"] = []
        obj = {}
        
        f = open(outfile, "r")
        data = f.read()
        obj = json.loads(data)
        f.close()

        objAll["_items"] += obj["_items"]
        cmdinfo["href"] = obj["_next"]
        while successOrnot and cmdinfo["href"]:
            if action == "returnAllRelation":           #fix the value of "_next"
                cmdinfo["href"] = cmdinfo["href"].replace("/resource_assignments/resource_assignments", "/resource_assignments")
            print(cmdinfo["href"])
            validParaIncmdinfo(cmdinfo)
            successOrnot = apiCommand(subinfo, cmdinfo, outfile)
            
            f = open(outfile, "r")
            data = f.read()
            obj = json.loads(data)
            f.close()
            if obj["_items"]:     #continue, if not the last one
                objAll["_items"] += obj["_items"]
                cmdinfo["href"] = obj["_next"]
            else:
                cmdinfo["href"] = ""

        #dump objAll to outfile
        if action == "returnAllThresholds":
            f_new = os.path.join(os.path.dirname(outfile), "allThresholds.json")
        elif action == "returnAllRelation":
            f_new = os.path.join(os.path.dirname(outfile), "allRelations.json")
        f = open(f_new, "w")
        jsonobj = json.dumps(objAll, indent=4)
        f.write(jsonobj)
        f.close()
        print("Outfile is:%s" % f_new)
        if action == "returnAllRelation":
            #generate relations cataloged by threhold and groups
            f = open(f_new, "r")
            alldata = json.loads(f.read())
            allrelations = alldata["_items"]
            f.close()
            relationCatbyResource = []
            relationCatbyThreshold = []
            for item in allrelations:
                resource = item["resource"]
                threshold = item["threshold"]
                updateOrnot = False
                for i in range(len(relationCatbyResource)):
                    if relationCatbyResource[i]["resource"] == resource:
                        relationCatbyResource[i]["threshold"].append(threshold)
                        updateOrnot = True
                if not updateOrnot:
                    a = {}
                    a["resource"] = resource
                    a["threshold"] = []
                    a["threshold"].append(threshold)
                    relationCatbyResource.append(a)
                updateOrnot = False
                for i in range(len(relationCatbyThreshold)):
                    if relationCatbyThreshold[i]["threshold"] == threshold:
                        relationCatbyThreshold[i]["resource"].append(resource)
                        updateOrnot = True
                if not updateOrnot:
                    a = {}
                    a["threshold"] = threshold
                    a["resource"] = []
                    a["resource"].append(resource)
                    relationCatbyThreshold.append(a)
            #end of item in allrelations
            f_out = f_new.replace("allRelations.json", "allRelationsByThreshold.json")
            f = open(f_out, "w")
            d = {}
            d["_items"] = relationCatbyThreshold
            data = json.dumps(d, indent=4)
            f.write(data)
            f.close()

            f_out = f_new.replace("allRelations.json", "allRelationsByResource.json")
            f = open(f_out, "w")
            d = {}
            d["_items"] = relationCatbyResource
            data = json.dumps(d, indent=4)
            f.write(data)
            f.close()
        #End of action == "returnAllRelation"
    else:
        validParaIncmdinfo(cmdinfo)
        successOrnot = apiCommand(subinfo, cmdinfo, outfile)

        if successOrnot and  action == "returnThresholdBasedonLabel":
            # create .json & .json.long files
            print_json_threshold(outfile)
            os.remove(outfile)
    #change the outfile name
    if action in {"returnAllAgents", "returnAllGroups"}:
        if action == "returnAllAgents":
            f_new = os.path.join(os.path.dirname(outfile), "allAgents.json")
        elif action == "returnAllGroups":
            f_new = os.path.join(os.path.dirname(outfile), "allResoureGroups.json")
        os.rename(outfile, f_new)
        print("The output file is:%s" % f_new)

# Disable to get all the contained agents for every group
#        if action == "returnAllGroups":
#            print("!!! You are free to press Ctrl + c from now to:")
#            print("Cancel the process to return all the contained agents for every resource group")
#            try:
#                #return the contained agents for avery group
#                f_detail = f_new.replace("allResoureGroups.json", "allResoureGroupsDetail.json")
#                f = open(f_new, "r")
#                alldata = json.loads(f.read())
#                allgroups = alldata["_items"]
#                for i in range(len(allgroups)):
#                    cmdinfo["description"] = "get the contained agents for every group"
#                    cmdinfo["action"] = "GET"
#                    cmdinfo["href"] = allgroups[i]["_href"] + "/references/to/contains"
#                    cmdinfo["hrefp"] = ""
#                    outfile = "/tmp/_allResoureGroups.tmp"
#                    successOrnot = apiCommand(subinfo, cmdinfo, outfile)

#                    if successOrnot:
#                        f2 = open(outfile, "r")
#                        alldata["_items"][i]["agents"] = json.loads(f2.read())["_items"]
#                        f2.close()
#                    else:
#                        alldata["_items"][i]["agents"] = []
#                #write data to file
#                f2 = open(f_detail, "w")
#                data = json.dumps(alldata, indent=4)
#                f2.write(data)
#                f2.write("\n")
#                f2.close()
#            except KeyboardInterrupt:
#                print("Exit from returning all the contained agents for every resource group")
#                #end of action == "returnAllGroups"

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
#main()
