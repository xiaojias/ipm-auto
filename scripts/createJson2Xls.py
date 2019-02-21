#!/usr/bin/env python
# -*- coding:utf8 -*- 
"""
xiaojias@cn.ibm.com
###################################################################
# changes :                                                       #
# 201xxxxx-XJS : Perform actions through API                      #
###################################################################
Create .xls file from .json file/s.

    Args:
        -d <directory>: will search the specific .json files from the directory and all of its sub directory. 
                        So far, the specific files including:
                            allThresholds.json
                            allResoureGroups.json
                            allAgents.json
    Returns:
        a .xls file will be created under above directory.
"""
import sys
import os
import datetime
import json
import re
import xlwt

script = os.path.basename(__file__)
def usage():
    print("Usage is:")
    print("%s -d <directoy> " % script )
    sys.exit(1)

def convertObj2onelayer(item, objdict, prefix="."):
    #write the multiple-layer dictionary to one layer by ading the prefix
    p = prefix
    if isinstance(item, dict):
        for k, v in item.iteritems():
            p2 = "%s.%s" % (p, k)
            if isinstance(v, dict) or isinstance(v, list):
                convertObj2onelayer(v, objdict, prefix=p2)
            else:
                objdict[p2] = v
    elif isinstance(item, list):
        for i in item:
            p2 = "%s.%d" % (p, item.index(i))
            convertObj2onelayer(i, objdict, prefix=p2)
    else:
        objdict[p] = item

    return(objdict)

def set_style(name, bold=False): 
    style = xlwt.XFStyle() # intial style
    
    font = xlwt.Font() 
    font.name = name # 'Times New Roman' 
    font.bold = bold 
    style.font = font 

    return(style)

def getArgvDic(argv):
    """Catch and save arguments into a dictionary.

    Args:
        argv: system arguments
    Returns:
        a dictionary type data
    """
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
    if not mydict.get("-d"):    #required parameters
        usage()
    dirName = mydict.get("-d")

    #define the template of sheets for resources
    templates = []
    #template for threshold
    col_unit = 3333   #pixels per inch
    t = {}
    t["templatename"] = "threshold"
    t["headerlist"] = ("label", "description", "_uiThresholdType", "severity", "formula", 
                    "period", "periods", "matchBy", "actions", "_isDefault", "_appliesToAgentType", "_id")
    t["colWidth"] = [2.3, 4, 0.8, 1, 10, 0.8, 0.4, 2, 0.6, 1]
    t["colWidth"] = [int(i * col_unit) for i in t["colWidth"]]
    t["headers"] = {
        "label": "Threshold name",
        "description": "Description",
        "severity": "Severity",
        "formula": "Formula",
        "period": "Sample interval",
        "periods": "Occurence",
        "matchBy": "Display",
        "actions": "Actions"
        }

    templates.append(t)
    #template for resource group
    t = {}
    t["templatename"] = "resourcegroup"
    t["headerlist"] = ("displayLabel", "description", "entityTypes.0", "_id", 
                    "_alarmServiceKey", "_observedAt") # for ResourceGroup
    t["colWidth"] = [2.3, 5, 2, 2.3, 4, 2.3]
    t["colWidth"] = [int(i * col_unit) for i in t["colWidth"]]
    t["headers"] = {
        "displayLabel": "Name",
        "description": "Description",
        "entityTypes.0": "Type",
        "_id": "ID"
        }
    templates.append(t)

    t = {}
    t["templatename"] = "agent"
    t["headerlist"] = ("keyIndexName", "description", "hostname", "online", "version", "productCode", 
                        "OSPlatformDescription",  "_id", "_observedAt",  "monitoringDomain")
    t["colWidth"] = [2.3, 2, 3, 1, 2, 2, 2, 3, 3, 2]
    t["colWidth"] = [int(i * col_unit) for i in t["colWidth"]]
    t["headers"] = {
        "keyIndexName": "Name",
        }
    templates.append(t)
    
    file_l = ("allThresholds.json", "allResoureGroups.json", "allAgents.json")   #all the to be processed files
    cust = []
    for parent, dirnames, filenames in os.walk(dirName):
        for filename in filenames:
            if filename in file_l:
                fullname = os.path.join(parent, filename)
                cust.append(fullname)
    
    if not cust:
        print("There is not any of following files under %s:" % dirName)
        for f in file_l:
            print(f)
        sys.exit(1)

    f_xls = xlwt.Workbook()
    # read .json file to a list data
    obj = ""
    for fname in cust:
        f = open(fname, "r")
        data = f.read()
        obj = json.loads(data)
        f.close()

        bname = os.path.basename(fname)
        dname = os.path.dirname(fname)
        if dname != dirName:
            s1 = dname.replace(dirName, "").strip("/").replace("/", "-")
        else:
            s1 = ""
        if bname == "allResoureGroups.json":
            t_name = "resourcegroup"
        elif bname == "allAgents.json":
            t_name = "agent"
        elif bname == "allThresholds.json":
            t_name = "threshold"
        sheetname = t_name if s1 == "" else ("%s-%s" % (s1, t_name))

        for i in range(len(templates)):
            if templates[i]["templatename"] == t_name:
                template = templates[i]
                break
        objlist = obj["_items"]  #return the list of all resourcegroups/agents or thresholds

        row = 0
        for item in objlist: # process for every rg, agent or threshold
            #convert item to ONE layer dictionary data for .xls file storing
            objdict = {}
            convertObj2onelayer(item, objdict, prefix="")

            keys = objdict.keys()
            for key in keys:
                p = re.compile(r"(?P<pre>(.)*)\.(?P<num>[0-9]+)((\.)(?P<suf>(.)*))*")
                s = p.match(key)
                if s:
                    s1 = s.group("pre").split(".")[-1]
                    if s.group("suf"):
                        short_key = "%s.%s.%s" % (s1, s.group("num"), s.group("suf"))
                    else:
                        short_key = "%s.%s" % (s1, s.group("num"))
                else:
                    short_key = key.split(".")[-1]
                
                objdict[short_key] = objdict[key]
                #debugging
                #objdict.pop(key)
            i = 0
            cont = objdict.get("formulaElements.%s.metricName" % str(i))
            if objdict.get("operator"):
                operator = objdict["operator"]
            else:
                operator = " "
            formula = ""
            while cont:
                newf = ("{ " + objdict["formulaElements.%s.function" % str(i)] + " " 
                + objdict["formulaElements.%s.metricName" % str(i)] + " " 
                + objdict["formulaElements.%s.operator" % str(i)] + " " 
                + objdict["formulaElements.%s.threshold" % str(i)] + " }")
                formula = formula + " " + operator + " " + newf
                i += 1
                cont = objdict.get("formulaElements.%s.metricName" % str(i))
            formula = formula.strip().strip(operator).strip()
            objdict["formula"] = formula
            
            #append objdict to sheet
            if row == 0:
                #write headers
                sheet = f_xls.add_sheet(sheetname)
                #set the column widths
                for i, v in enumerate(template["colWidth"]):
                    sheet.col(i).width = v
                col = 0
                for i in template["headerlist"]:
                    if template["headers"].get(i):
                        data = template["headers"][i]
                    else:
                        data = i
                    sheet.write(row, col, data, set_style('Times New Roman', True))
                    col += 1
                row += 1
            col = 0
            for k in template["headerlist"]:
                if objdict.get(k):
                    data = objdict.get(k)
                else:
                    data = ""
                sheet.write(row, col, data)
                col += 1
            row += 1
    s1 = datetime.datetime.now().strftime('%Y%m%d')
    xlsfile = os.path.join(dirName, "Monitoring_IPM8-%s.xls" % s1)
    f_xls.save(xlsfile)

    print("File of %s is created." % xlsfile)

main()
